# --- config.py ---

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
TARGET_REPO_PATH = ROOT_DIR / "target_repo"
WORKSPACE_PATH = ROOT_DIR / "workspace"
DATA_PATH = ROOT_DIR / "data"
VECTOR_STORE_PATH = DATA_PATH / "vector_store"
CODE_GRAPH_PATH = DATA_PATH / "code_graph.json"

# --- DEFINITIVE FIX: Use a model name that is confirmed to be on your list ---
AGENT_MODEL_NAME = "gemini-2.5-flash"
CLASSIFICATION_MODEL_NAME = "gemini-2.5-flash"

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "codegrapher_ai_embeddings"

def setup_directories():
    os.makedirs(TARGET_REPO_PATH, exist_ok=True)
    os.makedirs(WORKSPACE_PATH, exist_ok=True)
    os.makedirs(VECTOR_STORE_PATH, exist_ok=True)

# --- Environment-Controlled Settings ---
# Reads the AGENT_VERBOSE variable from .env and converts it to a boolean
AGENT_VERBOSE = os.environ.get("AGENT_VERBOSE", "False").lower() in ('true', '1', 't')