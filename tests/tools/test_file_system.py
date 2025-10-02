# --- tests/tools/test_file_system.py ---

import pytest
import os
from unittest.mock import patch, mock_open

from tools.file_system import read_file, parse_tool_input
import config

# Test Case 1: Test the input parser for messy LLM outputs
def test_parse_tool_input():
    """Ensures the parser can handle various string formats."""
    good_dict = {"file_path": "foo.py", "content": "bar"}

    # Test 1: Perfect dictionary input
    assert parse_tool_input(good_dict) == good_dict

    # Test 2: Stringified dictionary
    assert parse_tool_input('{"file_path": "foo.py", "content": "bar"}') == good_dict

    # Test 3: Common LLM messy output with extra text
    messy_string = """
    Here is the dictionary:
    {
        "file_path": "foo.py",
        "content": "bar"
    }
    That should work.
    """
    assert parse_tool_input(messy_string) == good_dict

# Test Case 2: Test successful file reading
@patch("builtins.open", new_callable=mock_open, read_data="file content")
@patch("os.path.abspath")
def test_read_file_success(mock_abspath, mock_open_file):
    """Should return file content when path is valid."""
    # Mock abspath to simulate a safe path
    safe_path = os.path.abspath(config.TARGET_REPO_PATH)
    mock_abspath.return_value = os.path.join(safe_path, "safe_file.py")

    result = read_file.invoke("safe_file.py") 

    assert result == "file content"

# Test Case 3: Test path traversal security block
def test_read_file_path_traversal_denied():
    """Should return an error for paths outside the target repo."""
    # This path tries to go up one directory from the root
    malicious_path = "../secrets.txt"
    result = read_file.invoke(malicious_path)
    assert "Error: Access denied." in result