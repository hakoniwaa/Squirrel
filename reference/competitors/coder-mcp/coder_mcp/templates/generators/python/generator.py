#!/usr/bin/env python3
"""
Python Generator
Simplified Python-specific generator using modular builders
"""

import logging
from pathlib import Path
from typing import Any, Dict

from ...template_engine import GeneratedCode
from ..base import BaseBuilder, BaseGenerator
from .builders.class_builder import ClassBuilder
from .builders.function_builder import FunctionBuilder
from .builders.test_builder import PythonTestBuilder

logger = logging.getLogger(__name__)


class PythonGenerator(BaseGenerator):
    """Python-specific code generator"""

    def get_language_name(self) -> str:
        """Get the language name"""
        return "python"

    def get_file_extension(self) -> str:
        """Get the primary file extension"""
        return ".py"

    def _register_builders(self) -> Dict[str, BaseBuilder]:
        """Register Python-specific builders"""
        return {
            "class": ClassBuilder(self.template_engine, self.workspace_root),
            "function": FunctionBuilder(self.template_engine, self.workspace_root),
            "test": PythonTestBuilder(self.template_engine, self.workspace_root),
            "api_endpoint": self._create_api_endpoint_builder(),
            "database_model": self._create_database_model_builder(),
            "service_class": self._create_service_class_builder(),
        }

    def _create_api_endpoint_builder(self) -> BaseBuilder:
        """Create a builder for API endpoints"""
        return ApiEndpointBuilder(self.template_engine, self.workspace_root)

    def _create_database_model_builder(self) -> BaseBuilder:
        """Create a builder for database models"""
        return DatabaseModelBuilder(self.template_engine, self.workspace_root)

    def _create_service_class_builder(self) -> BaseBuilder:
        """Create a builder for service classes"""
        return ServiceClassBuilder(self.template_engine, self.workspace_root)

    def get_test_framework(self) -> str:
        """Get the default test framework for Python"""
        return "pytest"

    def get_package_manager(self) -> str:
        """Get the default package manager for Python"""
        return "pip"

    def setup_project_structure(self) -> Dict[str, Any]:
        """Setup basic Python project structure"""
        files_created = []

        try:
            # Create source directory
            src_dir = self.get_source_directory()
            src_dir.mkdir(parents=True, exist_ok=True)

            # Create __init__.py files
            init_files = [
                src_dir / "__init__.py",
                src_dir / "api" / "__init__.py",
                src_dir / "models" / "__init__.py",
                src_dir / "services" / "__init__.py",
            ]

            for init_file in init_files:
                init_file.parent.mkdir(parents=True, exist_ok=True)
                if not init_file.exists():
                    init_file.write_text('"""Package initialization"""\n')
                    files_created.append(str(init_file.relative_to(self.workspace_root)))

            # Create test directory
            test_dir = self.get_test_directory()
            test_dir.mkdir(parents=True, exist_ok=True)

            test_init = test_dir / "__init__.py"
            if not test_init.exists():
                test_init.write_text('"""Test package initialization"""\n')
                files_created.append(str(test_init.relative_to(self.workspace_root)))

            return {
                "success": True,
                "files_created": files_created,
                "directories_created": [
                    str(src_dir.relative_to(self.workspace_root)),
                    str(test_dir.relative_to(self.workspace_root)),
                ],
            }

        except (OSError, IOError, PermissionError) as e:
            self.logger.error("Error setting up Python project structure: %s", str(e))
            return {"success": False, "error": str(e)}

    def setup_testing_framework(self) -> Dict[str, Any]:
        """Setup pytest testing framework"""

        files_created = []

        try:
            # pytest.ini
            pytest_config = self.workspace_root / "pytest.ini"
            if not pytest_config.exists():
                content = """[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=app
    --cov-report=term-missing
    --cov-fail-under=80

markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
"""
                pytest_config.write_text(content)
                files_created.append(str(pytest_config.relative_to(self.workspace_root)))

            # conftest.py
            conftest_file = self.get_test_directory() / "conftest.py"
            if not conftest_file.exists():
                content = '''"""
Pytest configuration and fixtures
"""

import pytest
from pathlib import Path


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace for testing"""
    return tmp_path


@pytest.fixture
def sample_data():
    """Provide sample test data"""
    return {
        "name": "TestItem",
        "description": "Test description",
        "is_active": True
    }
'''
                conftest_file.write_text(content)
                files_created.append(str(conftest_file.relative_to(self.workspace_root)))

            # Always create a basic test file if none exist
            test_dir = self.get_test_directory()
            test_dir.mkdir(parents=True, exist_ok=True)
            test_files = list(test_dir.glob("test_*.py"))
            if not test_files:
                smoke_test = test_dir / "test_smoke.py"
                smoke_content = "def test_smoke():\n    assert True\n"
                smoke_test.write_text(smoke_content)
                files_created.append(str(smoke_test.relative_to(self.workspace_root)))

            return {"success": True, "files_created": files_created}

        except (OSError, IOError, PermissionError) as e:
            self.logger.error("Error setting up testing framework: %s", str(e))
            return {"success": False, "error": str(e)}

    def setup_linting(self) -> Dict[str, Any]:
        """Setup Python linting configuration"""
        files_created = []

        try:
            # .flake8
            flake8_config = self.workspace_root / ".flake8"
            if not flake8_config.exists():
                content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    .venv,
    venv,
    .pytest_cache,
    build,
    dist
"""
                flake8_config.write_text(content)
                files_created.append(str(flake8_config.relative_to(self.workspace_root)))

            # pyproject.toml (if it doesn't exist)
            pyproject_file = self.workspace_root / "pyproject.toml"
            if not pyproject_file.exists():
                content = '''[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
target-version = ['py38']
include = '\\.pyi?$'
extend-exclude = """
/(
  | .git
  | .venv
  | venv
  | build
  | dist
)/
"""

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
'''
                pyproject_file.write_text(content)
                files_created.append(str(pyproject_file.relative_to(self.workspace_root)))

            return {"success": True, "files_created": files_created}

        except (OSError, IOError, PermissionError) as e:
            self.logger.error("Error setting up linting: %s", str(e))
            return {"success": False, "error": str(e)}


# Specialized builders for complex features
class ApiEndpointBuilder(BaseBuilder):
    """Builder for FastAPI endpoints"""

    def __init__(self, template_engine, workspace_root: Path):
        super().__init__(template_engine)
        self.workspace_root: Path = workspace_root

    def build(self, name: str, options: Dict[str, Any]) -> Any:
        """Build a FastAPI endpoint"""
        variables = self.get_common_variables(name, options)
        variables.update(
            {
                "method": options.get("method", "GET"),
                "auth_required": options.get("auth_required", True),
                "description": options.get("description", f"{name} API endpoint"),
            }
        )

        template = '''"""
{{ description }}
FastAPI endpoint with proper error handling and validation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter(prefix="/{{ name_snake }}", tags=["{{ name }}"])


class {{ name_pascal }}Request(BaseModel):
    """Request model for {{ name }}"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    # TODO: Add more request fields


class {{ name_pascal }}Response(BaseModel):
    """Response model for {{ name }}"""
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


@router.{{ method.lower() }}("/")
async def {{ method.lower() }}_{{ name_snake }}(
    {% if method in ["POST", "PUT", "PATCH"] %}request: {{ name_pascal }}Request,{% endif %}
    {% if auth_required %}current_user = Depends(get_current_user){% endif %}
) -> {{ name_pascal }}Response:
    """
    {{ method }} {{ name }} endpoint

    Args:
        {% if method in ["POST", "PUT", "PATCH"] %}request: {{ name }} request data{% endif %}
        {% if auth_required %}current_user: Current authenticated user{% endif %}

    Returns:
        {{ name_pascal }}Response: Created/updated {{ name }}

    Raises:
        HTTPException: If validation fails or resource not found
    """
    try:
        # TODO: Implement business logic
        result = {{ name_pascal }}Response(
            id=1,
            name={%- if method in ["POST", "PUT", "PATCH"] -%}
                request.name
            {%- else -%}
                "example"
            {%- endif %},
            description={%- if method in ["POST", "PUT", "PATCH"] -%}
                request.description
            {%- else -%}
                None
            {%- endif %},
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in {{ name }} endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
'''

        content = self.render_string(template, variables)

        source_dir = Path("src") / "api" if (Path("src").exists()) else Path("api")
        file_path = source_dir / f"{name.lower()}.py"

        return GeneratedCode(
            content=content,
            file_path=file_path,
            language="python",
            purpose=f"{name} FastAPI endpoint",
        )


class DatabaseModelBuilder(BaseBuilder):
    """Builder for SQLAlchemy models"""

    def __init__(self, template_engine, workspace_root: Path):
        super().__init__(template_engine)
        self.workspace_root: Path = workspace_root

    def build(self, name: str, options: Dict[str, Any]) -> Any:
        """Build a SQLAlchemy model"""
        variables = self.get_common_variables(name, options)
        variables.update(
            {
                "orm": options.get("orm", "sqlalchemy"),
                "table_name": options.get("table_name", f"{name.lower()}s"),
            }
        )

        template = '''"""
{{ name }} database model
SQLAlchemy model with proper relationships and validation
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Dict, Any

from app.database import Base


class {{ name_pascal }}(Base):
    """
    {{ name }} model

    This model represents a {{ name_snake }} in the system with proper
    validation, relationships, and serialization methods.
    """
    __tablename__ = "{{ table_name }}"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Core fields
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # TODO: Add relationships
    # user_id = Column(Integer, ForeignKey("users.id"))
    # user = relationship("User", back_populates="{{ name_snake }}s")

    def __repr__(self) -> str:
        """String representation of {{ name }}"""
        return f"<{{ name_pascal }}(id={self.id}, name={self.name!r})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "{{ name_pascal }}":
        """Create {{ name }} instance from dictionary"""
        return cls(
            name=data["name"],
            description=data.get("description"),
            is_active=data.get("is_active", True)
        )

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update {{ name }} instance from dictionary"""
        for key, value in data.items():
            if hasattr(self, key) and key not in ["id", "created_at"]:
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
'''

        content = self.render_string(template, variables)

        source_dir = Path("src") / "models" if (Path("src").exists()) else Path("models")
        file_path = source_dir / f"{name.lower()}.py"

        return GeneratedCode(
            content=content,
            file_path=file_path,
            language="python",
            purpose=f"{name} SQLAlchemy model",
        )


class ServiceClassBuilder(BaseBuilder):
    """Builder for service classes with business logic"""

    def __init__(self, template_engine, workspace_root: Path):
        super().__init__(template_engine)
        self.workspace_root: Path = workspace_root

    def build(self, name: str, options: Dict[str, Any]) -> Any:
        """Build a service class"""
        variables = self.get_common_variables(name, options)

        template = '''"""
{{ name }} Service
Business logic and service layer for {{ name }}
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class {{ name_pascal }}Service:
    """
    Service class for {{ name }} business logic

    This class encapsulates all business logic related to {{ name }}
    operations, providing a clean interface between the API layer
    and the database layer.
    """

    def __init__(self):
        self.logger = logger

    async def create_{{ name_snake }}(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new {{ name }}

        Args:
            data: {{ name }} data dictionary

        Returns:
            Created {{ name }} data
        """
        try:
            # Validate input data
            self._validate_{{ name_snake }}_data(data)

            # TODO: Implement business logic
            result = {
                "id": 1,
                "name": data["name"],
                "description": data.get("description"),
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            self.logger.info(f"Created {{ name }} with name: {data['name']}")
            return result

        except Exception as e:
            self.logger.error(f"Error creating {{ name }}: {e}")
            raise

    async def get_{{ name_snake }}_by_id(
        self, {{ name_snake }}_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get {{ name }} by ID

        Args:
            {{ name_snake }}_id: {{ name }} ID

        Returns:
            {{ name }} data or None if not found
        """
        # TODO: Implement database lookup
        return None

    def _validate_{{ name_snake }}_data(self, data: Dict[str, Any]) -> None:
        """
        Validate {{ name }} data

        Args:
            data: Data to validate

        Raises:
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        if "name" not in data or not data["name"]:
            raise ValueError("Name is required")

        if len(data["name"]) > 255:
            raise ValueError("Name must be 255 characters or less")
'''

        content = self.render_string(template, variables)

        source_dir = Path("src") / "services" if (Path("src").exists()) else Path("services")
        file_path = source_dir / f"{name.lower()}_service.py"

        return GeneratedCode(
            content=content, file_path=file_path, language="python", purpose=f"{name} service class"
        )
