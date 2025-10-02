# --- scripts/build_index.py ---

import chromadb
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import CodeSplitter
from llama_index.core import Settings
import os

import config

def main():
    """Main function to build the vector store index."""
    print("--- 🚀 Starting Index Building Process ---")

    # --- 1. Configure Global Settings (Embedding Model, LLM) ---
    print(f"--- 🧠 Loading embedding model: {config.EMBEDDING_MODEL_NAME} ---")
    Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBEDDING_MODEL_NAME)
    Settings.llm = None
    print("--- ✅ Embedding model loaded. ---")

    # --- 2. Load Documents from the Target Repository ---
    print(f"--- 📂 Loading documents from {config.TARGET_REPO_PATH} ---")
    reader = SimpleDirectoryReader(
        input_dir=config.TARGET_REPO_PATH,
        required_exts=[".py"],
        exclude=["*.venv*", "*__pycache__*", "*node_modules*", "*.git*"],
        recursive=True
    )
    documents = reader.load_data()
    print(f"--- ✅ Loaded {len(documents)} documents. ---")

    if not documents:
        print("--- ⚠️ No documents found. Please add Python files to the 'target_repo' directory. ---")
        return

    # --- 3. Setup ChromaDB Vector Store ---
    print(f"--- 💾 Setting up ChromaDB vector store at {config.VECTOR_STORE_PATH} ---")
    db = chromadb.PersistentClient(path=str(config.VECTOR_STORE_PATH))
    chroma_collection = db.get_or_create_collection(config.COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    print("--- ✅ Vector store setup complete. ---")

    # --- 4. Parse Code and Build Index ---
    print("--- 💻 Parsing code into nodes and building index... (This may take a while) ---")
    python_splitter = CodeSplitter(
        language="python",
        chunk_lines=40,
        chunk_lines_overlap=15,
        max_chars=1500,
    )
    Settings.transformations = [python_splitter]

    VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True
    )
    print(f"--- 🎉 Index building complete! ---")
    
    # --- FIX: Get the count directly from the persistent vector store ---
    # This is a more reliable way to confirm the data has been saved.
    nodes_in_db = chroma_collection.count()
    print(f"--- Total nodes indexed: {nodes_in_db} ---")
    print(f"--- Your AI is now ready to query the codebase. You can run 'app.py'. ---")

if __name__ == "__main__":
    config.setup_directories()
    main()