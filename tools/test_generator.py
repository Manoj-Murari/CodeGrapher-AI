# --- tools/test_generator.py ---

import ast
import os
import json # <-- NEW: Import the json library
from pathlib import Path

import google.generativeai as genai

import config
from engine.context import ProjectContext, ProjectScopedTool

class GenerateTestsTool(ProjectScopedTool):
    """
    A tool that generates unit tests for a specific function in a given file.
    """
    def __init__(self, context: ProjectContext):
        super().__init__(context)
        try:
            self.llm = genai.GenerativeModel(config.AGENT_MODEL_NAME)
        except Exception as e:
            print(f"--- ❌ ERROR: Failed to initialize Google Generative AI model in GenerateTestsTool. ---")
            print(f"--- Please ensure your GOOGLE_API_KEY is set correctly. Error: {e} ---")
            self.llm = None

    def _find_function_source(self, file_path: Path, function_name: str) -> str | None:
        if not file_path.is_file():
            return None
        try:
            source_code = file_path.read_text(encoding='utf-8')
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
                    return ast.get_source_segment(source_code, node)
        except Exception:
            return None
        return None

    def _clean_response(self, response_text: str) -> str:
        if response_text.strip().startswith("```python"):
            lines = response_text.strip().split('\n')[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            return '\n'.join(lines)
        return response_text

    def execute(self, tool_input: str | dict) -> str:
        """
        Generates pytest unit tests for a specified function and saves them
        to a new file in the /workspace directory.
        The input is a JSON string containing 'file_path' and 'function_name'.
        """
        if self.llm is None:
            return "Error: The Generative AI model is not configured. Cannot generate tests."

        # --- THE DEFINITIVE FIX: Parse the incoming JSON string ---
        try:
            if isinstance(tool_input, str):
                args_dict = json.loads(tool_input)
            else:
                args_dict = tool_input # It's already a dictionary

            file_path = args_dict.get("file_path")
            function_name = args_dict.get("function_name")
            if not file_path or not function_name:
                return "Error: Input must contain 'file_path' and 'function_name' keys."
        except (json.JSONDecodeError, AttributeError):
            return f"Error: Invalid input format. Expected a JSON string with 'file_path' and 'function_name', but received: {tool_input}"
        # --- END FIX ---

        target_file_path = self.context.repo_path / file_path
        function_source = self._find_function_source(target_file_path, function_name)
        
        if function_source is None:
            return f"Error: Could not find function '{function_name}' in file '{file_path}' or the file could not be parsed."

        prompt = f"""
        You are an expert Python test engineer specializing in `pytest`. Your task is to write a set of robust unit tests for the following function.

        **Function to Test:**
        File: `{file_path}`
        ```python
        {function_source}
        ```

        **Requirements:**
        1.  Write the tests in a separate file.
        2.  Include all necessary imports (including `pytest` and the function itself from the correct module path).
        3.  Create at least two test cases: one for a typical "happy path" scenario and one for a common edge case (e.g., invalid inputs, empty values, errors).
        4.  Your response MUST contain ONLY the Python code for the test file, enclosed in a single markdown block (```python ... ```). Do not include any extra explanations or introductory text.
        """
        
        try:
            response = self.llm.generate_content(prompt)
            generated_test_code = self._clean_response(response.text)
        except Exception as e:
            return f"Error: Failed to generate test code from the AI model. Details: {e}"

        if not generated_test_code.strip():
             return "Error: The AI model returned an empty response."

        output_filename = f"test_{function_name}.py"
        try:
            output_path = (config.WORKSPACE_PATH / output_filename).resolve()
            if not str(output_path).startswith(str(config.WORKSPACE_PATH.resolve())):
                return "Error: Access denied. Invalid output path for test file."
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(generated_test_code, encoding='utf-8')
            
            return f"Success: Test file '{output_filename}' was generated and saved to the workspace."
        except Exception as e:
            return f"Error: Failed to save the generated test file. Details: {e}"

