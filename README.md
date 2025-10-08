# CodeGrapher-AI

An intelligent code analysis and understanding assistant powered by AI. CodeGrapher-AI combines RAG (Retrieval-Augmented Generation), code graph analysis, and agentic workflows to help you explore, understand, and work with your codebases.

## 🌟 Features

- **Multi-Project Management**: Index and analyze multiple Git repositories simultaneously
- **Intelligent Query Routing**: Automatically routes queries between RAG and Agent systems based on context
- **Code Graph Analysis**: Build and query semantic graphs of your codebase to understand relationships between functions, classes, and modules
- **Vector-Based Search**: Fast semantic search across your entire codebase using embeddings
- **AI-Powered Tools**:
  - 📖 Read and analyze files
  - 🧪 Generate unit tests automatically
  - ✅ Run and validate tests
  - 🔧 Refactor code intelligently
  - 🐛 Fix bugs with AI assistance
  - 🔍 Query code structure and dependencies

## 🏗️ Architecture

CodeGrapher-AI uses a modern, scalable architecture:

- **Backend**: Flask API with Redis Queue for asynchronous job processing
- **Frontend**: React + TypeScript with Tailwind CSS
- **AI Models**: Google Gemini 2.5 Flash for reasoning and code generation
- **Vector Store**: ChromaDB for semantic search
- **Code Analysis**: AST-based parsing with networkx for graph construction
- **Agent Framework**: LangChain with custom tools and ReAct prompting

## 📋 Prerequisites

- Python 3.10 or higher
- Node.js 18+ and npm
- Redis server
- Google AI API key

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd CodeGrapher-AI
```

### 2. Backend Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API key
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

### 4. Start Redis

```bash
# macOS/Linux with Homebrew
brew services start redis

# Or run directly
redis-server

# Windows (if installed via WSL or native)
redis-server
```

## 🎮 Usage

### Starting the Application

You need three terminal windows:

**Terminal 1 - Backend API:**
```bash
source .venv/bin/activate
python app.py
```

**Terminal 2 - Worker Process:**
```bash
source .venv/bin/activate
rq worker
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
```

The application will be available at `http://localhost:5173`

### Adding a Project

1. Open the web interface
2. Paste a Git repository URL (must end in `.git`) in the header
3. Click "Add Project"
4. Wait for indexing to complete (status updates will appear in the UI)
5. Select the project from the dropdown to start querying

### Example Queries

- **General Questions**: "What is this project about?"
- **Code Exploration**: "Explain the `create_app` function in `app.py`"
- **Finding Dependencies**: "What functions call `set_password`?"
- **Test Generation**: "Generate unit tests for the `hash_password` function in `models.py`"
- **Refactoring**: "Extract the password hashing logic into a separate function"

## 🛠️ Configuration

Key configuration options in `config.py`:

```python
# Model Configuration
AGENT_MODEL_NAME = "gemini-2.5-flash"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Paths
DATA_PATH = ROOT_DIR / "data"
WORKSPACE_PATH = ROOT_DIR / "workspace"
```

## 📁 Project Structure

```
CodeGrapher-AI/
├── app.py                 # Flask API server
├── worker.py             # RQ worker for async jobs
├── config.py             # Configuration and paths
├── engine/               # Core AI engine
│   ├── agent.py         # LangChain agent setup
│   ├── chain.py         # Query routing logic
│   ├── rag.py           # RAG implementation
│   └── context.py       # Project context management
├── tools/                # Agent tools
│   ├── code_graph.py    # Code graph queries
│   ├── file_system.py   # File operations
│   ├── test_generator.py # Test generation
│   ├── test_runner.py   # Test execution
│   ├── refactor.py      # Code refactoring
│   └── bug_fixer.py     # Bug fixing
├── scripts/             # Indexing scripts
│   ├── build_index.py   # Vector store builder
│   └── build_graph.py   # Code graph builder
├── frontend/            # React frontend
│   └── src/
│       ├── components/  # UI components
│       └── pages/       # Page components
└── data/                # Generated data (gitignored)
    ├── repos/           # Cloned repositories
    ├── vector_stores/   # Vector embeddings
    └── code_graphs/     # Code graphs
```

## 🔧 Tools Available to the Agent

1. **ReadFile**: Read file contents from the repository
2. **ListFiles**: List files in the repository
3. **QueryCodeGraph**: Query the code structure graph
4. **CreateFileInWorkspace**: Create new files in the workspace
5. **UpdateFileInWorkspace**: Modify existing workspace files
6. **ListWorkspaceFiles**: List files in the workspace
7. **GenerateTests**: Generate pytest unit tests for functions
8. **RunTests**: Execute pytest tests and return results
9. **RefactorCode**: Perform code refactoring operations
10. **FixBug**: Analyze and fix bugs in code

## 🔒 Security Features

- Path traversal protection for all file operations
- Workspace isolation for generated files
- Input validation and sanitization
- Project-scoped contexts prevent cross-project access

## 🐛 Troubleshooting

### Redis Connection Issues
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG
```

### Import Errors
```bash
# Ensure you're in the virtual environment
which python  # Should point to .venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend Build Issues
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 📝 Development

### Running Tests

```bash
# Backend tests
pytest tests/

# Frontend tests (if configured)
cd frontend
npm test
```

### Code Quality

```bash
# Python linting
pylint engine/ tools/

# Frontend linting
cd frontend
npm run lint
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

- Built with [LangChain](https://langchain.com/)
- Powered by [Google Gemini](https://ai.google.dev/)
- UI components from [shadcn/ui](https://ui.shadcn.com/)
- Vector store by [ChromaDB](https://www.trychroma.com/)

## 📧 Support

For issues and questions, please open an issue on GitHub.

---

**Note**: This project requires a valid Google AI API key. Get one at [Google AI Studio](https://makersuite.google.com/app/apikey).