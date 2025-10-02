# --- tools/file_system.py ---

import os
import json
from langchain.tools import tool

# Import our project's configuration
import config

@tool
def read_file(file_path: str) -> str:
    """Reads a file from the code repository. Use this to inspect the contents of a file."""
    full_path = os.path.join(config.TARGET_REPO_PATH, file_path)
    if not os.path.abspath(full_path).startswith(os.path.abspath(config.TARGET_REPO_PATH)):
        return "Error: Access denied. You can only read files within the target_repo."
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File '{file_path}' not found."
    except Exception as e:
        return f"Error reading file: {e}"

@tool
def list_files(directory_path: str) -> str:
    """Lists the contents of a directory in the code repository."""
    full_path = os.path.join(config.TARGET_REPO_PATH, directory_path)
    if not os.path.abspath(full_path).startswith(os.path.abspath(config.TARGET_REPO_PATH)):
        return "Error: Access denied. You can only list directories within the target_repo."
    try:
        return json.dumps(os.listdir(full_path))
    except FileNotFoundError:
        return f"Error: Directory '{directory_path}' not found."
    except Exception as e:
        return f"Error listing directory: {e}"

# We will add workspace tools later if needed (create_file, update_file, etc.)