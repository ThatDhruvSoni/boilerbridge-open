from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.auth import get_current_user
from app.config import ALLOWED_ORIGINS
from app.rag import get_response
from app.supabase_client import supabase

app = FastAPI(title="BoilerBridge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConversationRequest(BaseModel):
    title: str = "Untitled Conversation"


class MessageRequest(BaseModel):
    conv_id: str
    content: str


@app.get("/")
async def health_check():
    return {"status": "ok"}


def ensure_profile(user):
    """Return the local profile for a signed-in user, creating it if needed."""
    result = supabase.table("users").select("*").eq("email", user.email).execute()
    if result.data:
        return result.data[0]

    metadata = user.user_metadata or {}
    created = supabase.table("users").insert(
        {
            "email": user.email,
            "name": metadata.get("full_name") or metadata.get("name"),
        }
    ).execute()
    return created.data[0]


def require_conversation(conv_id: str, user):
    """Load a conversation only when it belongs to the signed-in user."""
    profile = ensure_profile(user)
    result = (
        supabase.table("conversations")
        .select("*")
        .eq("id", conv_id)
        .eq("user_id", profile["id"])
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result.data[0]


@app.get("/auth/me")
async def auth_me(user=Depends(get_current_user)):
    profile = ensure_profile(user)
    return {
        "user_id": profile["id"],
        "email": profile["email"],
        "name": profile.get("name"),
    }


@app.get("/conversations")
async def get_conversations(user=Depends(get_current_user)):
    profile = ensure_profile(user)
    result = (
        supabase.table("conversations")
        .select("*")
        .eq("user_id", profile["id"])
        .order("created_at")
        .execute()
    )
    return {"conversations": result.data}


@app.post("/conversations")
async def create_conversation(data: ConversationRequest, user=Depends(get_current_user)):
    profile = ensure_profile(user)
    result = supabase.table("conversations").insert(
        {"user_id": profile["id"], "title": data.title}
    ).execute()
    return {"conversation_id": result.data[0]["id"]}


@app.get("/messages/{conv_id}")
async def get_messages(conv_id: str, user=Depends(get_current_user)):
    require_conversation(conv_id, user)
    result = (
        supabase.table("messages")
        .select("*")
        .eq("conversation_id", conv_id)
        .order("created_at")
        .execute()
    )
    return {"messages": result.data}


@app.post("/messages")
async def send_message(data: MessageRequest, user=Depends(get_current_user)):
    require_conversation(data.conv_id, user)

    messages = (
        supabase.table("messages")
        .select("sender,content")
        .eq("conversation_id", data.conv_id)
        .order("created_at")
        .execute()
        .data
    )
    history = "\n".join(
        f"{message['sender'].capitalize()}: {message['content']}"
        for message in messages
    )

    response = get_response(history, data.content)

    supabase.table("messages").insert(
        {
            "conversation_id": data.conv_id,
            "sender": "user",
            "content": data.content,
        }
    ).execute()
    supabase.table("messages").insert(
        {
            "conversation_id": data.conv_id,
            "sender": "assistant",
            "content": response,
        }
    ).execute()

    return {"response": response}
