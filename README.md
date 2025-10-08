<div align="center">

<br />

<img src="httpspreviews/logo_placeholder.png" alt="CodeGrapher-AI Logo" width="150">

<br />

CodeGrapher-AI

Go beyond searching. Start a conversation with your code.

<p>

<a href="httpspreviews/demo.gif"><img src="https://img.shields.io/badge/Live-Demo-brightgreen?style=for-the-badge&logo=youtube" alt="Live Demo"></a>

<a href="#"><img src="https://img.shields.io/github/stars/your-username/CodeGrapher-AI?style=for-the-badge&logo=github&color=FFC107" alt="GitHub stars"></a>

<a href="#"><img src="https://img.shields.io/github/forks/your-username/CodeGrapher-AI?style=for-the-badge&logo=github&color=blue" alt="GitHub forks"></a>

<a href="#"><img src="https://img.shields.io/github/license/your-username/CodeGrapher-AI?style=for-the-badge&color=lightgrey" alt="License"></a>

</p>

</div>

CodeGrapher-AI is an open-source AI assistant that ingests a codebase, analyzes it semantically and structurally, and empowers you to ask complex questions, generate tests, refactor code, and even fix bugs through a simple chat interface.

🎥 Live Demo

See how CodeGrapher-AI can accelerate your development workflow. From understanding legacy code to fixing bugs with a TDD-powered AI, it's all here.

<div align="center">

<a href="httpspreviews/demo_placeholder.gif">

<img src="httpspreviews/demo_placeholder.gif" alt="CodeGrapher-AI Demo GIF" width="800">

</a>

</div>

✨ Core Features

CodeGrapher-AI isn't just another chatbot. It's an integrated system with a "dual-brain" architecture designed for deep code intelligence.

🧠 Intelligent Query Routing: Automatically analyzes your prompt to decide the best way to answer.

RAG Brain: For semantic questions like "What's the purpose of the user authentication module?"

Agent Brain: For direct actions like "Read the Dockerfile" or "Find all callers of the get_user function."

🔍 Deep Semantic Search: Leverages vector embeddings to find code based on conceptual similarity, not just keywords. Understand the why behind the code, not just the where.

🕸️ Structural Code Graphing: Uses Abstract Syntax Trees (AST) to build a comprehensive map of your codebase. Ask precise questions about function callers, class methods, and dependencies.

🛠️ A Toolbox for Action: The AI Agent is equipped with powerful, secure tools to interact with your code:

File System I/O: Read and list files within the project's secure boundary.

Workspace: A sandboxed environment for the AI to draft changes, create new files, or run tests without touching your source code.

Test Generation: Point it at a function, and it will write pytest unit tests for you.

Automated Refactoring: Ask it to extract a method or simplify a complex function.

TDD-Powered Bug Fixing: Describe a bug, and the AI will first write a failing test to reproduce it, then attempt to generate a fix, and finally re-run the test to confirm the solution.

🏛️ Architecture Overview

Built with scalability and security in mind, the system integrates a modern web stack with a robust, asynchronous AI backend.

<div align="center">

<img src="httpspreviews/architecture_placeholder.png" alt="Architecture Diagram" width="800">

</div>

Frontend: A sleek and responsive React (TypeScript) + Vite application provides the chat interface. Styled with TailwindCSS.

Backend API: A Flask server acts as the central hub, handling user queries and managing background jobs.

Async Workers: Long-running tasks like cloning and indexing repositories are handled by Redis Queue (RQ) workers, ensuring the API remains fast and responsive.

AI Engine: The core of the system, orchestrating LangChain agents and LlamaIndex RAG pipelines with Google's Gemini models.

Data Layer:

ChromaDB serves as the vector store for semantic search.

A custom JSON file stores the structural code graph.

Cloned repositories are stored permanently on disk.

🚀 Getting Started

You can have your own instance of CodeGrapher-AI running in just a few minutes.

Prerequisites

Python 3.11+

Node.js 18+ and npm

Git

Redis Server (running locally or accessible)

A Google AI API Key (get one from Google AI Studio)

1. Clone & Setup

Bash



# Clone the repository

git clone https://github.com/your-username/CodeGrapher-AI.gitcd CodeGrapher-AI# Set up Python virtual environment and install backend dependencies

python -m venv .venvsource .venv/bin/activate  # On Windows: .\.venv\Scripts\activate

pip install -r requirements.txt# Install the project in editable mode (crucial for imports)

pip install -e .# Install frontend dependenciescd frontend

npm installcd ..

2. Configure Environment

Create a .env file in the project root. This is where you'll put your secret keys.

Code snippet



# Your Google AI API Key

GOOGLE_API_KEY="your-google-api-key-here"



# (Optional) Set to True for detailed agent thought processes in the console

AGENT_VERBOSE=True



# (Optional) URL for your Redis instance

REDIS_URL="redis://localhost:6379"

3. Launch the Application

You need three terminal windows for this.

Terminal 1: Start the Redis Worker

Bash



source .venv/bin/activate

rq worker

Terminal 2: Start the Flask Backend

Bash



source .venv/bin/activate

flask run

Terminal 3: Start the React Frontend

Bash



cd frontend

npm run dev

You can now access the application at http://localhost:5173.

👨‍💻 Usage

Add a Project: Paste any public HTTPS Git URL (ending in .git) into the "Add Project" input and click the button. The RQ worker will pick up the job and begin cloning and indexing.

Select a Project: Once indexed, the project will appear in the dropdown. Select it.

Start Chatting! Try a few different types of questions:

RAG Query: "Explain the purpose of the run_chain function in engine/chain.py."

Agent (File System): "Read the contents of the pyproject.toml file."

Agent (Code Graph): "Who are the callers of the execute function in the ReadFileTool class?"

Agent (Test Generation): "Generate unit tests for the get_project_name_from_url function in worker.py."

🤝 Contributing

As a solo developer, I'm building this project in the open and welcome all contributions. Whether it's a bug fix, a new feature, or improving the documentation, your help is appreciated.

Fork the repository.

Create a new branch (git checkout -b feature/your-awesome-feature).

Make your changes.

Run the tests! (docker build -t codegrapher-tests . && docker run codegrapher-tests)

Commit your changes (git commit -m 'Add some awesome feature').

Push to the branch (git push origin feature/your-awesome-feature).

Open a Pull Request.

📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

<div align="center">

<p>Built with passion by a developer, for developers.</p>

</div>