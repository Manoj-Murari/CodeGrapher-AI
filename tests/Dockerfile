# Dockerfile for running tests in an isolated environment

# 1. Base Image
FROM python:3.11-slim
WORKDIR /app

# 2. Dependency Management
# This layer is cached as long as the lock file doesn't change.
RUN pip install poetry

# Copy project dependency definitions
COPY pyproject.toml poetry.lock ./

# Install ALL dependencies, including dev dependencies like pytest and pytest-mock
# This is the key step that makes the 'mocker' fixture available.
RUN poetry install

# 3. Copy the code to be tested from the workspace
# The build context will be our /workspace directory.
COPY . .

# 4. The command to run when the container starts
CMD ["poetry", "run", "pytest"]