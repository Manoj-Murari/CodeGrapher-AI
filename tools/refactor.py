# --- tools/refactor.py ---

import ast
import json
from pathlib import Path

import google.generativeai as genai

import config
from engine.context import ProjectContext, ProjectScopedTool

class RefactorCodeTool(ProjectScopedTool):
    """
    A tool to perform automated code refactoring, such as extracting a method.
    """
    def __init__(self, context: ProjectContext):
        super().__init__(context)
        try:
            self.llm = genai.GenerativeModel(config.AGENT_MODEL_NAME)
        except Exception as e:
            self.llm = None
            print(f"--- ❌ ERROR: Failed to initialize Gemini model in RefactorCodeTool: {e} ---")

    def execute(self, tool_input: str | dict) -> str:
        """
        Extracts a snippet of code from an existing function into a new function,
        then saves the modified file to the /workspace directory.
        The input must be a JSON string or dictionary containing four keys:
        'file_path', 'function_name', 'code_to_extract', and 'new_function_name'.
        """
        if self.llm is None:
            return "Error: The Generative AI model is not configured. Cannot refactor code."

        try:
            if isinstance(tool_input, str):
                args = json.loads(tool_input)
            else:
                args = tool_input
            
            file_path = args["file_path"]
            function_name = args["function_name"]
            code_to_extract = args["code_to_extract"]
            new_function_name = args["new_function_name"]
        except (json.JSONDecodeError, KeyError):
            return "Error: Invalid input. Must be a JSON object with keys 'file_path', 'function_name', 'code_to_extract', and 'new_function_name'."

        target_file = self.context.repo_path / file_path
        if not target_file.is_file():
            return f"Error: Source file not found at '{file_path}'."

        try:
            original_source = target_file.read_text(encoding='utf-8')
            original_lines = original_source.splitlines()
            tree = ast.parse(original_source)
        except Exception as e:
            return f"Error: Failed to parse the source file '{file_path}'. Details: {e}"

        # 1. Find the target function node in the AST
        target_node = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
                target_node = node
                break
        
        if target_node is None:
            return f"Error: Function '{function_name}' not found in '{file_path}'."

        original_function_source = ast.get_source_segment(original_source, target_node)

        # 2. Construct a detailed, structured prompt
        prompt = f"""
        You are an expert software engineer specializing in Python code refactoring. Your task is to extract a block of code from an existing function into a new function.

        **Context:**
        Full source code of the file `{file_path}`:
        ```python
        {original_source}
        ```

        **Refactoring Details:**
        - **Original Function Name:** `{function_name}`
        - **Code Snippet to Extract:**
        ```python
        {code_to_extract}
        ```
        - **New Function Name:** `{new_function_name}`

        **Instructions:**
        1. Create the new function (`{new_function_name}`) containing the extracted code. Analyze the snippet to determine the necessary arguments and return values.
        2. Rewrite the original function (`{function_name}`) so that it now calls the new function.
        3. Your response MUST be a single, valid JSON object with two keys: "new_function_code" and "updated_original_function_code".

        **Example Response Format:**
        ```json
        {{
          "new_function_code": "def new_function(arg1):\n    # ... extracted logic ...\n    return result",
          "updated_original_function_code": "def original_function(arg1):\n    # ... logic before ...\n    result = new_function(arg1)\n    # ... logic after ..."
        }}
        ```
        """

        # 3. Call the LLM
        try:
            response = self.llm.generate_content(prompt)
            # Basic JSON cleaning
            cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
            refactored_code = json.loads(cleaned_text)
            
            new_function_code = refactored_code["new_function_code"]
            updated_original_function_code = refactored_code["updated_original_function_code"]

        except (json.JSONDecodeError, KeyError, Exception) as e:
            return f"Error: Failed to get a valid refactoring plan from the AI. Details: {e}\nRaw AI Response:\n{response.text}"

        # 4. Programmatically rebuild the source file
        new_source_lines = []
        in_original_function = False
        start_line, end_line = target_node.lineno, target_node.end_lineno
        
        for i, line in enumerate(original_lines):
            line_num = i + 1
            if line_num == start_line:
                in_original_function = True
                new_source_lines.extend(updated_original_function_code.splitlines())
            elif line_num > start_line and line_num <= end_line:
                continue # Skip the old lines of the original function
            else:
                new_source_lines.append(line)
                if line_num == end_line:
                    # After the original function ends, insert the new function
                    new_source_lines.append("") # Add a blank line for spacing
                    new_source_lines.extend(new_function_code.splitlines())

        new_source_code = "\n".join(new_source_lines)

        # 5. Save the modified file to the workspace
        output_file_path = config.WORKSPACE_PATH / file_path
        try:
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
            output_file_path.write_text(new_source_code, encoding='utf-8')
            return f"Success: Refactored code was saved to '{file_path}' in the workspace. Please review the changes."
        except Exception as e:
            return f"Error: Failed to save the refactored file to the workspace. Details: {e}"
