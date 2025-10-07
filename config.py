# --- config.py ---

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
TARGET_REPO_PATH = ROOT_DIR / "target_repo"
WORKSPACE_PATH = ROOT_DIR / "workspace"
DATA_PATH = ROOT_DIR / "data"
VECTOR_STORE_BASE_PATH = DATA_PATH / "vector_stores"
CODE_GRAPH_BASE_PATH = DATA_PATH / "code_graphs"


# --- DEFINITIVE FIX: Use a model name that is confirmed to be on your list ---
AGENT_MODEL_NAME = "gemini-2.5-flash"
CLASSIFICATION_MODEL_NAME = "gemini-2.5-flash"


EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
AGENT_VERBOSE = os.environ.get("AGENT_VERBOSE", "False").lower() in ('true', '1', 't')

def get_code_graph_path(project_name: str) -> Path:
    """Returns the path to the code graph JSON file for a specific project."""
    return CODE_GRAPH_BASE_PATH / f"{project_name}_graph.json"

def get_vector_store_path(project_name: str) -> Path:
    """Returns the path to the vector store directory for a specific project."""
    return VECTOR_STORE_BASE_PATH / project_name

def get_collection_name(project_name: str) -> str:
    """Returns the collection name for a specific project."""
    return f"{project_name}_embeddings"

def setup_directories():
    os.makedirs(TARGET_REPO_PATH, exist_ok=True)
    os.makedirs(WORKSPACE_PATH, exist_ok=True)
    os.makedirs(VECTOR_STORE_BASE_PATH, exist_ok=True)
    os.makedirs(CODE_GRAPH_BASE_PATH, exist_ok=True)