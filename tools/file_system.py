# --- tools/file_system.py ---

import os
import json
import ast # Import the ast module for safe literal evaluation
from langchain.tools import tool
import config

# --- Helper function to fix the agent's messy input ---
def parse_tool_input(input_str: str | dict) -> dict:
    """
    Parses the tool input, which can be a string or a dict.
    Handles cases where the model outputs "key: {dict_content}"
    """
    if isinstance(input_str, dict):
        return input_str
    try:
        # Find the first '{' and the last '}' to extract the dictionary string
        start = input_str.find('{')
        end = input_str.rfind('}') + 1
        if start != -1 and end != 0:
            dict_str = input_str[start:end]
            # Use ast.literal_eval for safely evaluating the string as a Python literal
            return ast.literal_eval(dict_str)
    except (ValueError, SyntaxError):
        pass
    return {} # Return empty dict if parsing fails


# --- Read-Only Tools for the main repository ---
@tool
def read_file(file_path: str) -> str:
    """Reads a file from the code repository. Use this to inspect the contents of a file."""
    full_path = os.path.join(config.TARGET_REPO_PATH, file_path)
    if not os.path.abspath(full_path).startswith(os.path.abspath(config.TARGET_REPO_PATH)):
        return "Error: Access denied."
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
        return "Error: Access denied."
    try:
        return json.dumps(os.listdir(full_path))
    except FileNotFoundError:
        return f"Error: Directory '{directory_path}' not found."
    except Exception as e:
        return f"Error listing directory: {e}"


# --- Read/Write Tools for the secure workspace ---
@tool
def create_file_in_workspace(file_info: str | dict) -> str:
    """
    Creates a new file with specified content in the /workspace directory.
    The input must contain a 'file_path' and 'content'.
    Example: {"file_path": "foo.py", "content": "print('hello world')"}
    """
    parsed_args = parse_tool_input(file_info)
    if 'file_path' not in parsed_args or 'content' not in parsed_args:
        return "Error: Input must be a dictionary with 'file_path' and 'content' keys."
    
    file_path = parsed_args['file_path']
    content = parsed_args['content']
    
    full_path = os.path.join(config.WORKSPACE_PATH, file_path)
    if not os.path.abspath(full_path).startswith(os.path.abspath(config.WORKSPACE_PATH)):
        return "Error: Access denied."
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Success: File '{file_path}' created in the workspace."
    except Exception as e:
        return f"Error creating file: {e}"

@tool
def update_file_in_workspace(file_info: str | dict) -> str:
    """
    Updates an existing file with new content in the /workspace directory.
    The input must contain a 'file_path' and 'content'.
    Example: {"file_path": "foo.py", "content": "print('hello world again')"}
    """
    parsed_args = parse_tool_input(file_info)
    if 'file_path' not in parsed_args or 'content' not in parsed_args:
        return "Error: Input must be a dictionary with 'file_path' and 'content' keys."

    file_path = parsed_args['file_path']
    content = parsed_args['content']
    
    full_path = os.path.join(config.WORKSPACE_PATH, file_path)
    if not os.path.abspath(full_path).startswith(os.path.abspath(config.WORKSPACE_PATH)):
        return "Error: Access denied."
    if not os.path.exists(full_path):
        return f"Error: File '{file_path}' not found in workspace."
    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Success: File '{file_path}' updated in the workspace."
    except Exception as e:
        return f"Error updating file: {e}"

@tool
def list_workspace_files(directory_path: str) -> str:
    """Lists the contents of a directory in the /workspace directory."""
    full_path = os.path.join(config.WORKSPACE_PATH, directory_path)
    if not os.path.abspath(full_path).startswith(os.path.abspath(config.WORKSPACE_PATH)):
        return "Error: Access denied."
    try:
        return json.dumps(os.listdir(full_path))
    except FileNotFoundError:
        return f"Error: Directory '{directory_path}' not found in workspace."
    except Exception as e:
        return f"Error listing directory: {e}"