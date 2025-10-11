# --- config.py ---

import os
from pathlib import Path
import google.generativeai as genai
import logging

ROOT_DIR = Path(__file__).resolve().parent
TARGET_REPO_PATH = ROOT_DIR / "target_repo"
WORKSPACE_PATH = ROOT_DIR / "workspace"
DATA_PATH = ROOT_DIR / "data"
VECTOR_STORE_BASE_PATH = DATA_PATH / "vector_stores"
CODE_GRAPH_BASE_PATH = DATA_PATH / "code_graphs"
REPOS_BASE_PATH = DATA_PATH / "repos"

# --- Model Configuration ---
AGENT_MODEL_NAME = "gemini-1.5-flash"
CLASSIFICATION_MODEL_NAME = "gemini-1.5-flash"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# --- Agent Configuration ---
AGENT_VERBOSE = os.environ.get("AGENT_VERBOSE", "False").lower() in ('true', '1', 't')

# --- NEW: Global API Key Configuration ---
def configure_google_genai():
    """
    Reads the GOOGLE_API_KEY from the environment and configures the genai library.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logging.error("GOOGLE_API_KEY environment variable not found or is empty.")
        # We don't exit here, to allow parts of the app to run, but tools will fail.
        return
    try:
        genai.configure(api_key=api_key)
        logging.info("Successfully configured Google Generative AI.")
    except Exception as e:
        logging.error(f"Failed to configure Google Generative AI: {e}")

# --- (The rest of the functions remain the same) ---
def get_code_graph_path(project_name: str) -> Path:
    return CODE_GRAPH_BASE_PATH / f"{project_name}_graph.json"

def get_vector_store_path(project_name: str) -> Path:
    return VECTOR_STORE_BASE_PATH / project_name

def get_collection_name(project_name: str) -> str:
    return f"{project_name}_embeddings"

def setup_directories():
    os.makedirs(TARGET_REPO_PATH, exist_ok=True)
    os.makedirs(WORKSPACE_PATH, exist_ok=True)
    os.makedirs(VECTOR_STORE_BASE_PATH, exist_ok=True)
    os.makedirs(CODE_GRAPH_BASE_PATH, exist_ok=True)
    os.makedirs(REPOS_BASE_PATH, exist_ok=True)
