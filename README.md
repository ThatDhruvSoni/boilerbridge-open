# BoilerBridge Backend

Backend for BoilerBridge, a research-discovery assistant I built to help Purdue students find faculty and labs that match their interests.

The service combines a FastAPI API, Supabase-backed user/conversation storage, and a FAISS retrieval pipeline. Student questions are first rewritten into retrieval-friendly research queries, matched against an indexed collection of Purdue faculty information with maximal marginal relevance, and then answered with the retrieved material as context.

## Stack

- FastAPI
- Supabase
- FAISS + OpenAI embeddings
- OpenAI chat completions
- LangChain vector-store integration

## Project structure

```
app/
  main.py             API routes and conversation flow
  auth.py             Supabase token validation
  config.py           environment configuration
  rag.py              query rewriting, retrieval, and response generation
  supabase_client.py  database client
  purdue_faiss_index/ local retrieval index
```

## Running locally

Create a virtual environment and install the dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and provide your own credentials. Then start the API:

```bash
uvicorn app.main:app --reload
```

The original project used a separate React frontend. This repository focuses on the backend and retrieval pipeline.

## Security notes

API credentials are read from environment variables and are not stored in the repository. Protected routes validate the Supabase access token and scope conversation access to the authenticated user.

The checked-in FAISS index is project-generated and trusted by this application. LangChain's FAISS loader uses pickle for its document metadata, so the index should not be replaced with files from an untrusted source.
