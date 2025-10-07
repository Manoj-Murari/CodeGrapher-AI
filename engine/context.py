# --- engine/context.py ---

import os
from pathlib import Path
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, validator

# Assuming your config.py has these base paths defined
# We'll need to add get_project_repo_path to it later.
from config import (
    VECTOR_STORE_BASE_PATH,
    CODE_GRAPH_BASE_PATH,
    TARGET_REPO_PATH # This will be refactored
)

class ProjectNotIndexedError(Exception):
    """Custom exception for when a project's assets are not found."""
    pass

class ProjectContext(BaseModel):
    """
    An immutable, project-specific context that flows through the entire request.
    It is the single source of truth for all project-related paths and configurations.
    """
    project_id: str = Field(..., min_length=1, description="The unique identifier for the project.")

    @property
    def repo_path(self) -> Path:
        # For now, we assume a flat structure. This will need a lookup.
        # TODO: Replace with a dynamic lookup, e.g., config.get_project_repo_path(self.project_id)
        return TARGET_REPO_PATH / self.project_id

    @property
    def vector_store_path(self) -> Path:
        return VECTOR_STORE_BASE_PATH / self.project_id

    @property
    def code_graph_path(self) -> Path:
        return CODE_GRAPH_BASE_PATH / f"{self.project_id}_graph.json"

    @validator('project_id')
    def validate_project_assets(cls, v):
        """
        Validates that the necessary data assets for this project exist on disk.
        This enforces our 'fail fast' principle.
        """
        project_id = v
        vector_store_dir = VECTOR_STORE_BASE_PATH / project_id
        code_graph_file = CODE_GRAPH_BASE_PATH / f"{project_id}_graph.json"

        if not vector_store_dir.is_dir():
            raise ProjectNotIndexedError(
                f"Project '{project_id}' is not indexed: Vector store not found at {vector_store_dir}"
            )
        if not code_graph_file.is_file():
            raise ProjectNotIndexedError(
                f"Project '{project_id}' is not indexed: Code graph not found at {code_graph_file}"
            )
        return v

class ProjectScopedTool(ABC):
    """
    Abstract Base Class for any tool that operates within a specific project's context.
    Ensures that no tool can be initialized without a valid, secure project context.
    """
    def __init__(self, context: ProjectContext):
        self.context = context
        # Optional: Add a logger that includes context by default
        # self.logger = structlog.get_logger().bind(project_id=self.context.project_id)

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """The core logic of the tool."""
        pass