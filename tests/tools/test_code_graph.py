# --- tests/tools/test_code_graph.py ---

import pytest
import json
from pathlib import Path
import os

# Make sure the project root is in the path for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from engine.context import ProjectContext
from tools.code_graph import QueryCodeGraphTool

# A sample code graph with varying confidence levels
SAMPLE_GRAPH_WITH_CONFIDENCE = {
    "nodes": [
        {"id": "file1.py::func_a", "name": "func_a"},
        {"id": "file1.py::func_b", "name": "func_b"},
        {"id": "file2.py::method_c", "name": "method_c"},
        {"id": "file3.py::heuristic_d", "name": "heuristic_d"}
    ],
    "edges": [
        # High confidence call
        {"source": "file2.py::method_c", "target": "file1.py::func_a", "confidence": 1.0},
        # Low confidence (heuristic) call
        {"source": "file3.py::heuristic_d", "target": "file1.py::func_a", "confidence": 0.4},
        # High confidence call
        {"source": "file1.py::func_a", "target": "file1.py::func_b", "confidence": 0.9}
    ]
}

@pytest.fixture
def setup_graph_project(tmp_path: Path):
    """Sets up a temporary project with a valid, rich code graph for testing."""
    project_id = "test_confidence_project"
    data_root = tmp_path / "data"
    (data_root / "vector_stores" / project_id).mkdir(parents=True)
    (data_root / "code_graphs").mkdir(parents=True)
    (data_root / "code_graphs" / f"{project_id}_graph.json").write_text(json.dumps(SAMPLE_GRAPH_WITH_CONFIDENCE))
    (tmp_path / project_id).mkdir()

    mp = pytest.MonkeyPatch()
    mp.setattr("config.VECTOR_STORE_BASE_PATH", data_root / "vector_stores")
    mp.setattr("config.CODE_GRAPH_BASE_PATH", data_root / "code_graphs")
    mp.setattr("config.TARGET_REPO_PATH", tmp_path)
    yield ProjectContext(project_id=project_id)
    mp.undo()


# --- The Tests ---

def test_query_graph_find_callers_default_confidence(setup_graph_project):
    """Tests finding callers using the default high confidence threshold."""
    tool = QueryCodeGraphTool(setup_graph_project)
    result = tool.execute(entity_name="func_a", relationship="callers")
    data = json.loads(result)
    assert len(data) == 1
    assert data[0]["name"] == "method_c" # Should not include the low-confidence one

def test_query_graph_find_callers_low_confidence(setup_graph_project):
    """Tests that a low confidence threshold includes heuristic guesses."""
    tool = QueryCodeGraphTool(setup_graph_project)
    result = tool.execute(entity_name="func_a", relationship="callers", min_confidence=0.3)
    data = json.loads(result)
    assert len(data) == 2 # Should include both
    assert {"method_c", "heuristic_d"} == {item["name"] for item in data}

def test_query_graph_find_callees_with_confidence(setup_graph_project):
    """Tests finding callees with a specific confidence threshold."""
    tool = QueryCodeGraphTool(setup_graph_project)
    result = tool.execute(entity_name="func_a", relationship="callees", min_confidence=0.85)
    data = json.loads(result)
    assert len(data) == 1
    assert data[0]["name"] == "func_b"

def test_query_graph_no_results_with_high_confidence(setup_graph_project):
    """Tests getting no results when confidence threshold is too high."""
    tool = QueryCodeGraphTool(setup_graph_project)
    result = tool.execute(entity_name="func_a", relationship="callees", min_confidence=0.95)
    assert "No callees found" in result