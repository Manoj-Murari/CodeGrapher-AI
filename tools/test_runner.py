# --- tools/test_runner.py ---

import subprocess
import sys
import os # <-- Import the os module
from pathlib import Path

import config
from engine.context import ProjectScopedTool

class RunTestsTool(ProjectScopedTool):
    """
    A tool to run a specific pytest test file from the workspace.
    """
    def execute(self, test_file: str) -> str:
        """
        Runs a specific pytest test file located in the /workspace directory
        and returns the captured output from the test run.
        - test_file: The string name of the test file to execute (e.g., "test_example.py").
        """
        # Security: Ensure the test file is within the workspace
        workspace_path = config.WORKSPACE_PATH.resolve()
        test_file_path = (workspace_path / test_file).resolve()

        if not str(test_file_path).startswith(str(workspace_path)):
            return "Error: Access denied. Test file must be inside the workspace."

        if not test_file_path.is_file():
            return f"Error: Test file not found at '{test_file}' in the workspace."

        # --- THE FIX: Configure the environment for the subprocess ---
        # 1. Copy the current environment to pass it to the subprocess
        env = os.environ.copy()
        
        # 2. Get the project's root directory from the context
        project_root_path = str(self.context.repo_path.resolve())

        # 3. Prepend the project's root path to the PYTHONPATH
        #    This allows the test file to import modules like 'conduit'
        #    os.pathsep is ';' on Windows and ':' on Linux/macOS
        env['PYTHONPATH'] = f"{project_root_path}{os.pathsep}{env.get('PYTHONPATH', '')}"
        
        # Use the python executable from the current virtual environment to run pytest
        python_executable = sys.executable
        command = [python_executable, "-m", "pytest", str(test_file_path)]

        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=120,
                env=env # <-- Pass the modified environment to the subprocess
            )
            output = f"--- Test Results for {test_file} ---\n"
            output += f"Exit Code: {process.returncode}\n\n"
            if process.stdout:
                output += f"STDOUT:\n{process.stdout}\n"
            if process.stderr:
                output += f"STDERR:\n{process.stderr}\n"
            return output
        except FileNotFoundError:
            return "Error: `pytest` command not found. Make sure pytest is installed in the environment."
        except subprocess.TimeoutExpired:
            return "Error: Test execution timed out after 120 seconds."
        except Exception as e:
            return f"An unexpected error occurred while running tests: {e}"