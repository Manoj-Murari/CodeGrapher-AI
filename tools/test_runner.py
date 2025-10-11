# --- tools/test_runner.py ---

import subprocess
import sys
import os
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

        # --- THE FIX: Configure the environment AND working directory for the subprocess ---
        # 1. Copy the current environment
        env = os.environ.copy()
        
        # 2. Define project paths. The repo_path is where the source code lives.
        #    The test is running against a copy in the workspace, but needs to import from the original.
        project_root = str(self.context.repo_path.resolve())
        
        # 3. Prepend the project's root path to PYTHONPATH.
        #    This allows the test file to import modules from the project's source tree.
        pythonpath_parts = [project_root]
        if 'PYTHONPATH' in env:
            pythonpath_parts.append(env['PYTHONPATH'])
        
        env['PYTHONPATH'] = os.pathsep.join(pythonpath_parts)
        
        # 4. Use the python executable from the current virtual environment
        python_executable = sys.executable
        # We run pytest against the test file inside the workspace
        command = [python_executable, "-m", "pytest", str(test_file_path), "-v"]

        try:
            # 5. Run the subprocess with the correct environment AND working directory
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=120,
                # CRITICAL: Set the working directory to the source repo.
                # This makes relative imports like 'from my_package import utils' work.
                cwd=project_root,
                env=env # Pass the modified environment
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