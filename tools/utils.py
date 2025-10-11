# --- tools/utils.py ---

import json
import re
import ast
from typing import Any, Dict

def parse_tool_input(tool_input: str | Dict[str, Any]) -> Dict[str, Any]:
    """
    Robustly parses tool input from an agent, which can be a dict or a
    string in various JSON-like or key-value formats.
    """
    if isinstance(tool_input, dict):
        return tool_input
    
    if not isinstance(tool_input, str):
        raise ValueError(f"Invalid input type. Expected str or dict, but got {type(tool_input).__name__}.")

    text = tool_input.strip()
    
    # 1. Try standard JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Try replacing single quotes with double quotes
    try:
        return json.loads(text.replace("'", '"'))
    except json.JSONDecodeError:
        pass
        
    # 3. Try ast.literal_eval for Python dict literals
    try:
        result = ast.literal_eval(text)
        if isinstance(result, dict):
            return result
    except (ValueError, SyntaxError, MemoryError, TypeError):
        pass

    # 4. Fallback to regex for key=value or key='value' pairs
    try:
        # This regex handles keys, and values that are quoted or unquoted
        pattern = r'(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|(\S+))'
        matches = re.findall(pattern, text)
        if matches:
            # The regex captures into 3 groups for the value, so we merge them
            return {key: next(val for val in (v1, v2, v3) if val) for key, v1, v2, v3 in matches}
    except Exception:
        pass

    raise ValueError(f"Unable to parse tool input string: {tool_input}")