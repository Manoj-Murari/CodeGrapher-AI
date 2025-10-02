# CodeGrapher-AI

An intelligent AI agent designed to understand, analyze, and answer questions about a given codebase using a combination of Retrieval-Augmented Generation (RAG) and tool-using agents.

## Key Features

- **Dual-Capability Engine:** Intelligently routes user queries to the best tool for the job:
  - A **RAG pipeline** for semantic understanding ("What does this code do?").
  - A **tool-using Agent** for performing actions ("Read this file.").
- **Semantic Code Search (RAG):** Uses LlamaIndex and a ChromaDB vector database to find the most relevant code snippets and synthesize answers.
- **Structural Code Analysis:** Parses the entire codebase using Python's `ast` module to build a structural graph of function/method calls, which is queryable by the agent.
- **Agentic Tool Use:** Built with LangChain, the agent can read files from the repository and query the code graph to answer complex, multi-step questions.
- **Web Interface:** A simple and clean Flask-based web UI for interactive chatting with the AI.

## Architecture Overview

This project uses a modern, flat-layout architecture that separates concerns into distinct packages and scripts:

- **`/scripts`**: Contains standalone scripts for data processing. These are run once to prepare the AI's knowledge.
  - `build_index.py`: Parses the codebase and builds the ChromaDB vector store for the RAG engine.
  - `build_graph.py`: Parses the codebase and builds the `code_graph.json` for the agent's structural analysis tool.
- **`/data`**: Stores the generated data files (`vector_store/` and `code_graph.json`). This directory is ignored by Git.
- **`/engine`**: The core "brain" of the application.
  - `rag.py`: Defines the custom RAG query engine.
  - `agent.py`: Defines the LangChain agent and its associated tools.
  - `chain.py`: The main entry point that contains the intelligent router to choose between the RAG engine and the Agent.
- **`/tools`**: Contains the individual Python functions that the LangChain agent can use.
- **`app.py`**: The Flask web server that provides the API and serves the frontend.
- **`pyproject.toml`**: The modern configuration file that defines the project for installation, making imports clean and reliable.

## Core Technologies

- **LLMs:** Google Gemini (`gemini-2.5-flash`)
- **Frameworks:** LangChain, LlamaIndex
- **Vector Database:** ChromaDB
- **Embeddings:** `all-MiniLM-L6-v2` (via Sentence Transformers)
- **Code Parsing:** Python's built-in `ast` module
- **Web Server:** Flask

## Setup and Installation

Follow these steps to set up and run the project locally.

**1. Clone the Repository**
```bash
git clone <your-repo-url>
cd CodeGrapher-AI
```

**2. Create and Activate a Virtual Environment**
```bash
# For Windows
python -m venv .venv
.\.venv\Scripts\activate

# For macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install Dependencies**
Install all required packages from the `requirements.txt` file.
```bash
pip install -r requirements.txt
```

**4. Install the Project in Editable Mode**
This crucial step makes your project's modules (`engine`, `tools`, `config`) importable from anywhere.
```bash
pip install -e .
```

**5. Create a `.env` File**
Create a file named `.env` in the project root and add your Google AI API key.
```env
GOOGLE_API_KEY="your-google-api-key-here"
AGENT_VERBOSE=True
```

**6. Add a Codebase to Analyze**
Place the source code of the project you want to analyze into the `/target_repo` directory. For example:
```bash
git clone [https://github.com/gothinkster/flask-realworld-example-app.git](https://github.com/gothinkster/flask-realworld-example-app.git) target_repo
```

## Running the Application

Running the application is a two-stage process: first, process the data, then run the web server.

**Stage 1: Process the Codebase**

Run the following scripts from the project root to build the AI's knowledge base. You only need to do this once, or whenever the code in `target_repo` changes.

```bash
# Build the semantic vector index (for RAG)
python scripts/build_index.py

# Build the structural code graph (for the Agent tool)
python scripts/build_graph.py
```

**Stage 2: Launch the Web App**

Run the Flask server. The `--debug` flag provides helpful logs and enables auto-reloading.
```bash
flask run --debug
```
Now, open your web browser and navigate to **http://127.0.0.1:5000**.

## Usage Examples

You can now ask the AI questions. Try both RAG-style and Agent-style queries:

- **RAG Query (Semantic understanding):**
  > What is the purpose of the `create_app` function?

- **Agent Query (Reading a file):**
  > Read the contents of the file named Pipfile.

- **Agent Query (Using the code graph):**
  > Who are the callers of the `find_by_email` function?

---