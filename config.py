"""Shared configuration for Lab 18."""

import os
from dotenv import load_dotenv

load_dotenv()

# --- API Keys & LLM Provider (Support OpenAI & Groq) ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# LLM Base URL & Model Name
if GROQ_API_KEY:
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
else:
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", None)
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")


def get_llm_client():
    """Return OpenAI client configured for either Groq or OpenAI."""
    try:
        from openai import OpenAI
        groq_key = os.getenv("GROQ_API_KEY", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("LLM_BASE_URL", "")

        if groq_key:
            return OpenAI(
                api_key=groq_key,
                base_url=base_url or "https://api.groq.com/openai/v1"
            )
        elif openai_key and openai_key.startswith("sk-"):
            if base_url:
                return OpenAI(api_key=openai_key, base_url=base_url)
            return OpenAI(api_key=openai_key)
    except Exception:
        pass
    return None


# --- Qdrant ---
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "lab18_production"
NAIVE_COLLECTION = "lab18_naive"

# --- Embedding ---
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024

# --- Chunking ---
HIERARCHICAL_PARENT_SIZE = 2048
HIERARCHICAL_CHILD_SIZE = 256
SEMANTIC_THRESHOLD = 0.85

# --- Search ---
BM25_TOP_K = 20
DENSE_TOP_K = 20
HYBRID_TOP_K = 20
RERANK_TOP_K = 3

# --- Paths ---
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TEST_SET_PATH = os.path.join(os.path.dirname(__file__), "test_set.json")
