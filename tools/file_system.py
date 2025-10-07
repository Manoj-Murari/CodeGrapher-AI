# --- tools/file_system.py ---

import os
import json
from pathlib import Path

import config
from engine.context import ProjectContext, ProjectScopedTool

class ReadFileTool(ProjectScopedTool):
    def execute(self, file_path: str) -> str:
        """
        Reads a file from THIS PROJECT'S repository.
        The path should be relative to the project's root directory.
        """
        try:
            full_path = self.context.repo_path / file_path
            resolved_path = full_path.resolve()

            if not str(resolved_path).startswith(str(self.context.repo_path.resolve())):
                return "Error: Access denied. Path is outside the project boundary."

            if resolved_path.is_symlink():
                return "Error: Access denied. Symbolic links are not allowed."

            if not resolved_path.is_file():
                return f"Error: Path '{file_path}' is not a file."

            if resolved_path.stat().st_size > 5 * 1024 * 1024:
                return "Error: File is too large to read (max 5MB)."
            
            allowed_extensions = ['.py', '.js', '.ts', '.md', '.txt', '.json', '.html', '.css', '.yaml', '.toml', 'Dockerfile', '.env']
            if resolved_path.suffix not in allowed_extensions and resolved_path.name not in ['Dockerfile', '.env']:
                 return f"Error: File type '{resolved_path.suffix}' is not permitted for reading."

            return resolved_path.read_text(encoding='utf-8')
        except FileNotFoundError:
            return f"Error: File '{file_path}' not found."
        except UnicodeDecodeError:
            return f"Error: File '{file_path}' is not a valid UTF-8 text file."
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

class ListFilesTool(ProjectScopedTool):
    def execute(self, directory_path: str = ".") -> str:
        """
        Lists the contents of a directory in THIS PROJECT'S repository.
        The path should be relative to the project's root directory.
        Defaults to the project root if no path is provided.
        """
        try:
            full_path = (self.context.repo_path / directory_path).resolve()
            
            if not str(full_path).startswith(str(self.context.repo_path.resolve())):
                return "Error: Access denied. Path is outside the project boundary."

            if not full_path.is_dir():
                return f"Error: Path '{directory_path}' is not a directory."

            contents = os.listdir(full_path)
            classified_contents = {
                "directories": [item for item in contents if (full_path / item).is_dir()],
                "files": [item for item in contents if (full_path / item).is_file()]
            }
            return json.dumps(classified_contents, indent=2)
        except FileNotFoundError:
            return f"Error: Directory '{directory_path}' not found."
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"

# --- NEW: Fully Implemented Workspace Tools ---

class CreateFileInWorkspaceTool(ProjectScopedTool):
    def execute(self, file_path: str, content: str) -> str:
        """
        Creates a new file with specified content in the secure /workspace directory.
        Subdirectories will be created if they don't exist.
        """
        try:
            # All workspace operations are relative to the global WORKSPACE_PATH
            full_path = (config.WORKSPACE_PATH / file_path).resolve()

            # Security check: Ensure the final path is within the workspace
            if not str(full_path).startswith(str(config.WORKSPACE_PATH.resolve())):
                return "Error: Access denied. Path is outside the workspace boundary."
            
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            return f"Success: File '{file_path}' created in the workspace."
        except Exception as e:
            return f"Error creating file: {str(e)}"

class UpdateFileInWorkspaceTool(ProjectScopedTool):
    def execute(self, file_path: str, content: str) -> str:
        """
        Updates an existing file with new content in the secure /workspace directory.
        """
        try:
            full_path = (config.WORKSPACE_PATH / file_path).resolve()

            if not str(full_path).startswith(str(config.WORKSPACE_PATH.resolve())):
                return "Error: Access denied. Path is outside the workspace boundary."

            if not full_path.is_file():
                return f"Error: File '{file_path}' not found in workspace. Use create_file_in_workspace to create it first."

            full_path.write_text(content, encoding='utf-8')
            return f"Success: File '{file_path}' updated in the workspace."
        except Exception as e:
            return f"Error updating file: {str(e)}"

class ListWorkspaceFilesTool(ProjectScopedTool):
    def execute(self, directory_path: str = ".") -> str:
        """Lists the contents of a directory in the secure /workspace directory."""
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
            return f"An unexpected error occurred: {str(e)}"