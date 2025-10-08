# --- tools/file_system.py ---

import os
import json
from pathlib import Path

import config
from engine.context import ProjectContext, ProjectScopedTool

class ReadFileTool(ProjectScopedTool):
    def execute(self, tool_input: str | dict) -> str:
        """
        Reads a file from THIS PROJECT'S repository.
        The input can be a dictionary with a 'file_path' key, or a string that is the file path.
        """
        if isinstance(tool_input, dict):
            file_path = tool_input.get("file_path")
        elif isinstance(tool_input, str):
            file_path = tool_input
        else:
            return "Error: Invalid input type for ReadFile. Expected a string or a dictionary."

        if not file_path:
            return "Error: 'file_path' not provided in the input."
        
        try:
            full_path = self.context.repo_path / file_path
            resolved_path = full_path.resolve()
            if not str(resolved_path).startswith(str(self.context.repo_path.resolve())):
                return "Error: Access denied. Path is outside the project boundary."
            if not resolved_path.is_file():
                return f"Error: Path '{file_path}' is not a file."
            return resolved_path.read_text(encoding='utf-8')
        except Exception as e:
            return f"An unexpected error occurred while reading file: {str(e)}"

class ListFilesTool(ProjectScopedTool):
    def execute(self, tool_input: str | dict) -> str:
        """
        Lists contents of a directory in THIS PROJECT'S repository.
        Input can be a dictionary with an optional 'directory_path' key, or a string that is the directory path.
        """
        if isinstance(tool_input, dict):
            directory_path = tool_input.get("directory_path", ".")
        elif isinstance(tool_input, str):
            directory_path = tool_input if tool_input.strip() else "."
        else:
            return "Error: Invalid input type for ListFiles. Expected a string or a dictionary."

        try:
            full_path = (self.context.repo_path / directory_path).resolve()
            if not str(full_path).startswith(str(self.context.repo_path.resolve())):
                return "Error: Access denied."
            if not full_path.is_dir():
                return f"Error: Path '{directory_path}' is not a directory."
            contents = os.listdir(full_path)
            classified_contents = {
                "directories": [item for item in contents if (full_path / item).is_dir()],
                "files": [item for item in contents if (full_path / item).is_file()]
            }
            return json.dumps(classified_contents, indent=2)
        except Exception as e:
            return f"An unexpected error occurred while listing files: {str(e)}"

class CreateFileInWorkspaceTool(ProjectScopedTool):
    def execute(self, tool_input: dict) -> str:
        """
        Creates a new file in the /workspace directory.
        Input must be a dictionary with 'file_path' and 'content' keys.
        """
        try:
            if isinstance(tool_input, str):
                args_dict = json.loads(tool_input)
            else:
                args_dict = tool_input
            file_path = args_dict.get("file_path")
            content = args_dict.get("content")
            if not file_path or content is None:
                return "Error: Input must be a dictionary with 'file_path' and 'content' keys."
            
            full_path = (config.WORKSPACE_PATH / file_path).resolve()
            if not str(full_path).startswith(str(config.WORKSPACE_PATH.resolve())):
                return "Error: Access denied. Path is outside the workspace boundary."
            
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            return f"Success: File '{file_path}' created in the workspace."
        except (json.JSONDecodeError, AttributeError):
            return f"Error: Invalid input format. Expected a JSON string or dict with 'file_path' and 'content', but received: {tool_input}"
        except Exception as e:
            return f"Error creating file: {str(e)}"

class UpdateFileInWorkspaceTool(ProjectScopedTool):
    def execute(self, tool_input: dict) -> str:
        """
        Updates an existing file in the /workspace directory.
        Input must be a dictionary with 'file_path' and 'content' keys.
        """
        try:
            if isinstance(tool_input, str):
                args_dict = json.loads(tool_input)
            else:
                args_dict = tool_input
            file_path = args_dict.get("file_path")
            content = args_dict.get("content")
            if not file_path or content is None:
                return "Error: Input must be a dictionary with 'file_path' and 'content' keys."

            full_path = (config.WORKSPACE_PATH / file_path).resolve()
            if not str(full_path).startswith(str(config.WORKSPACE_PATH.resolve())):
                return "Error: Access denied. Path is outside the workspace boundary."
            if not full_path.is_file():
                return f"Error: File '{file_path}' not found in workspace. Use CreateFileInWorkspace to create it first."
            full_path.write_text(content, encoding='utf-8')
            return f"Success: File '{file_path}' updated in the workspace."
        except (json.JSONDecodeError, AttributeError):
            return f"Error: Invalid input format. Expected a JSON string or dict with 'file_path' and 'content', but received: {tool_input}"
        except Exception as e:
            return f"Error updating file: {str(e)}"

class ListWorkspaceFilesTool(ProjectScopedTool):
    def execute(self, tool_input: str | dict) -> str:
        """
        Lists contents of a directory in the /workspace directory.
        Input can be a dictionary with an optional 'directory_path' key, or a string that is the directory path.
        """
        if isinstance(tool_input, dict):
            directory_path = tool_input.get("directory_path", ".")
        elif isinstance(tool_input, str):
            directory_path = tool_input if tool_input.strip() else "."
        else:
            return "Error: Invalid input type for ListWorkspaceFiles. Expected a string or a dictionary."
        
        try:
            full_path = (config.WORKSPACE_PATH / directory_path).resolve()
            if not str(full_path).startswith(str(config.WORKSPACE_PATH.resolve())):
                return "Error: Access denied. Path is outside the workspace boundary."
            if not full_path.is_dir():
                return f"Error: Directory '{directory_path}' not found in workspace."
            contents = os.listdir(full_path)
            classified_contents = {
                "directories": [item for item in contents if (full_path / item).is_dir()],
                "files": [item for item in contents if (full_path / item).is_file()]
            }
            return json.dumps(classified_contents, indent=2)
        except Exception as e:
            return f"An unexpected error occurred while listing workspace files: {str(e)}"
