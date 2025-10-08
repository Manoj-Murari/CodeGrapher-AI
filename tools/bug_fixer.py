# --- tools/bug_fixer.py ---

import ast
import json # <-- Import the json library
import shutil
from pathlib import Path

import google.generativeai as genai
import config
from engine.context import ProjectContext, ProjectScopedTool
# We're importing the other tools to use their logic internally
from .test_generator import GenerateTestsTool
from .test_runner import RunTestsTool

class FixBugTool(ProjectScopedTool):
    """
    An orchestrator tool that attempts to fix a bug in a function using a
    Test-Driven Development (TDD) workflow.
    """
    def __init__(self, context: ProjectContext):
        super().__init__(context)
        try:
            self.llm = genai.GenerativeModel(config.AGENT_MODEL_NAME)
        except Exception as e:
            self.llm = None
            print(f"--- ❌ ERROR: Failed to initialize Gemini model in FixBugTool: {e} ---")
            
        self._test_generator_tool = GenerateTestsTool(context)
        self._test_runner_tool = RunTestsTool(context)

    def _copy_project_to_workspace(self) -> str:
        """Prepares a clean workspace by copying the project source into it."""
        try:
            if config.WORKSPACE_PATH.exists():
                shutil.rmtree(config.WORKSPACE_PATH)
            shutil.copytree(self.context.repo_path, config.WORKSPACE_PATH)
            return f"Successfully copied '{self.context.project_id}' to workspace."
        except Exception as e:
            return f"Error: Failed to copy project to workspace. Details: {e}"

    def execute(self, tool_input: str | dict) -> str:
        """
        Executes a full TDD cycle to fix a described bug.
        The input must be a dictionary or JSON string with 'file_path', 
        'function_name', and 'bug_description' keys.
        """
        if self.llm is None:
            return "Error: The Generative AI model is not configured."

        # --- THE FIX: Parse the incoming JSON string ---
        try:
            if isinstance(tool_input, str):
                args_dict = json.loads(tool_input)
            else:
                args_dict = tool_input

            file_path = args_dict.get("file_path")
            function_name = args_dict.get("function_name")
            bug_description = args_dict.get("bug_description")

            if not all([file_path, function_name, bug_description]):
                return "Error: Input must include 'file_path', 'function_name', and 'bug_description'."
        except (json.JSONDecodeError, AttributeError):
            return f"Error: Invalid input format. Expected a JSON string or dict, but received: {tool_input}"
        # --- END FIX ---

        mission_log = [f"### Starting Bug Fix Mission for `{function_name}` ###"]
        
        # 0. Prepare the workspace
        mission_log.append("\n--- Step 0: Preparing secure workspace ---")
        setup_result = self._copy_project_to_workspace()
        mission_log.append(setup_result)
        if "Error" in setup_result:
            return "\n".join(mission_log)

        # 1. Generate a failing test
        mission_log.append("\n--- Step 1: Generating a failing test ---")
        # We need to construct the dictionary input for the test generator tool
        gen_test_input = {
            "file_path": file_path, 
            "function_name": function_name, 
            "bug_description": bug_description # Pass the bug description to the prompt
        }
        test_gen_result = self._test_generator_tool.execute(gen_test_input)
        mission_log.append(test_gen_result)
        if "Error" in test_gen_result:
            return "\n".join(mission_log)
        
        test_file_name = f"test_{function_name}.py"

        # 2. Run the test to confirm it fails
        mission_log.append("\n--- Step 2: Running test to confirm failure ---")
        test_run_result = self._test_runner_tool.execute()
        mission_log.append(test_run_result)

        if "Exit Code: 0" in test_run_result or "passed" in test_run_result:
             mission_log.append("ABORT: Generated test did not fail as expected. Cannot verify the bug.")
             return "\n".join(mission_log)
        mission_log.append("✅ Test failed as expected. Proceeding with fix.")

        # 3. Generate the fix
        mission_log.append("\n--- Step 3: Generating code fix ---")
        original_file_path = config.WORKSPACE_PATH / file_path
        original_source = original_file_path.read_text(encoding='utf-8')
        test_file_path = config.WORKSPACE_PATH / test_file_name
        
        test_source = ""
        if test_file_path.exists():
            test_source = test_file_path.read_text(encoding='utf-8')

        fix_prompt = f"""
        You are an expert Python software engineer. A test has failed, indicating a bug. Your task is to fix the bug.

        **Failing Test Code (`{test_file_name}`):**
        ```python
        {test_source}
        ```

        **Original Source Code (`{file_path}`):**
        ```python
        {original_source}
        ```
        
        **Bug Description:** {bug_description}

        **Instructions:**
        1. Analyze the original code and the failing test.
        2. Provide a fixed version of the original source code.
        3. Your response MUST be ONLY the complete, corrected Python code for the original file (`{file_path}`), enclosed in a single markdown block.
        """
        try:
            response = self.llm.generate_content(fix_prompt)
            fixed_code = self._test_generator_tool._clean_response(response.text)
            mission_log.append("✅ AI has generated a potential fix.")
        except Exception as e:
            mission_log.append(f"Error: AI model failed to generate a fix. Details: {e}")
            return "\n".join(mission_log)
            
        # 4. Apply the fix
        mission_log.append("\n--- Step 4: Applying fix to file in workspace ---")
        original_file_path.write_text(fixed_code, encoding='utf-8')
        mission_log.append(f"Applied fix to `{file_path}` in workspace.")
        
        # 5. Run tests again to confirm fix
        mission_log.append("\n--- Step 5: Running tests again to confirm fix ---")
        final_test_result = self._test_runner_tool.execute()
        mission_log.append(final_test_result)
        
        # 6. Report final result
        if "Exit Code: 0" in final_test_result or "passed" in final_test_result:
            mission_log.append("\n### ✅ MISSION SUCCESS: All tests passed. The bug has been fixed. ###")
        else:
            mission_log.append("\n### ❌ MISSION FAILED: The AI-generated fix did not resolve the test failures. ###")
            
        return "\n".join(mission_log)