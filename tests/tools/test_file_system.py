# --- tests/tools/test_file_system.py ---

import pytest
from pathlib import Path
import os
import json

# Make sure the project root is in the path for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from engine.context import ProjectContext, ProjectNotIndexedError
from tools.file_system import ReadFileTool, ListFilesTool

# This is a pytest fixture. It runs before each test that uses it.
# It creates a temporary, controlled file system structure for our tests.
@pytest.fixture
def setup_project(tmp_path: Path):
    """Sets up a temporary project directory with files, subdirs, and security traps."""
    # Main project directories
    project_root = tmp_path / "test_project"
    data_root = tmp_path / "data"
    
    # Create structure for a valid ProjectContext
    (data_root / "vector_stores" / "test_project").mkdir(parents=True)
    (data_root / "code_graphs").mkdir(parents=True)
    (data_root / "code_graphs" / "test_project_graph.json").write_text("{}")
    
    # Create the repository content
    repo_path = project_root
    repo_path.mkdir()
    (repo_path / "main.py").write_text("print('hello world')")
    (repo_path / "utils").mkdir()
    (repo_path / "utils" / "helpers.py").write_text("# a helper function")
    
    # Create a large file to test size limits (6MB)
    (repo_path / "large_file.log").write_text("A" * 6 * 1024 * 1024)
    
    # Create a file with a disallowed extension
    (repo_path / "data.bin").write_text("binary data")

    # Create a secret file outside the project boundary
    (tmp_path / "secret.txt").write_text("password123")
    
    # Create a symlink pointing outside the project boundary
    # Note: symlink creation can be skipped on Windows if permissions are an issue
    try:
        os.symlink(tmp_path / "secret.txt", repo_path / "secret_link")
    except OSError:
        print("Skipping symlink test: Insufficient permissions on this OS.")
        pass

    # Monkeypatch the config paths to point to our temporary directory for this test
    # We use a context manager to ensure the patch is reverted after the test
    mp = pytest.MonkeyPatch()
    mp.setattr("config.VECTOR_STORE_BASE_PATH", data_root / "vector_stores")
    mp.setattr("config.CODE_GRAPH_BASE_PATH", data_root / "code_graphs")
    # This assumes projects are stored in subdirectories of a base repo path
    mp.setattr("config.TARGET_REPO_PATH", project_root.parent)
    yield ProjectContext(project_id="test_project")
    mp.undo()


# --- Tests for ReadFileTool ---

def test_read_file_success(setup_project):
    """Tests that a valid file within the project can be read."""
    context = setup_project
    tool = ReadFileTool(context)
    result = tool.execute(file_path="main.py")
    assert result == "print('hello world')"

def test_read_file_in_subdirectory_success(setup_project):
    """Tests that a file in a subdirectory can be read."""
    context = setup_project
    tool = ReadFileTool(context)
    result = tool.execute(file_path="utils/helpers.py")
    assert result == "# a helper function"

def test_read_file_denied_path_traversal(setup_project):
    """Tests that path traversal is blocked."""
    context = setup_project
    tool = ReadFileTool(context)
    # The resolved path will be outside the project boundary
    result = tool.execute(file_path="../secret.txt")
    assert "Error: Access denied" in result

def test_read_file_denied_symlink(setup_project):
    """Tests that reading symbolic links is blocked."""
    context = setup_project
    # Skip test if symlink wasn't created
    if not (context.repo_path / "secret_link").exists():
        pytest.skip("Symlink not created, skipping test.")
        
    tool = ReadFileTool(context)
    result = tool.execute(file_path="secret_link")
    assert "Error: Access denied. Symbolic links are not allowed." in result

def test_read_file_denied_too_large(setup_project):
    """Tests that the file size limit is enforced."""
    context = setup_project
    tool = ReadFileTool(context)
    result = tool.execute(file_path="large_file.log")
    assert "Error: File is too large" in result

def test_read_file_denied_bad_extension(setup_project):
    """Tests that the file extension whitelist is enforced."""
    context = setup_project
    tool = ReadFileTool(context)
    result = tool.execute(file_path="data.bin")
    assert "Error: File type '.bin' is not permitted" in result

def test_read_file_not_found(setup_project):
    """Tests that a clear error is given for a non-existent file."""
    context = setup_project
    tool = ReadFileTool(context)
    result = tool.execute(file_path="non_existent_file.py")
    assert "Error: File 'non_existent_file.py' not found" in result

# --- Tests for ListFilesTool ---

def test_list_files_success_root(setup_project):
    """Tests that listing the project root works correctly."""
    context = setup_project
    tool = ListFilesTool(context)
    result = tool.execute() # Default path is '.'
    
    data = json.loads(result)
    
    assert "directories" in data
    assert "files" in data
    assert "utils" in data["directories"]
    assert "main.py" in data["files"]
    assert "large_file.log" in data["files"]

def test_list_files_success_subdirectory(setup_project):
    """Tests that listing a subdirectory works correctly."""
    context = setup_project
    tool = ListFilesTool(context)
    result = tool.execute(directory_path="utils")
    
    data = json.loads(result)
    
    assert "helpers.py" in data["files"]
    assert not data["directories"] # No subdirectories in 'utils'

def test_list_files_denied_traversal(setup_project):
    """Tests that directory traversal is blocked."""
    context = setup_project
    tool = ListFilesTool(context)
    result = tool.execute(directory_path="../")
    assert "Error: Access denied" in result

def test_list_files_error_when_path_is_file(setup_project):
    """Tests that an error is returned if the path is a file, not a directory."""
    context = setup_project
    tool = ListFilesTool(context)
    result = tool.execute(directory_path="main.py")
    assert "Error: Path 'main.py' is not a directory" in result

def test_list_files_not_found(setup_project):
    """Tests for a clear error on a non-existent directory."""
    context = setup_project
    tool = ListFilesTool(context)
    result = tool.execute(directory_path="non_existent_dir")
    assert "Error: Directory 'non_existent_dir' not found" in result