# --- scripts/build_index.py ---

import chromadb
import argparse # <-- Import argparse
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import CodeSplitter
from llama_index.core import Settings
import os

import config

# --- NEW: Add main function with argument parsing ---
def main():
    """Main function to build the vector store index."""
    parser = argparse.ArgumentParser(description="Build a vector store index for a codebase.")
    parser.add_argument("--name", required=True, help="A unique name for the project.")
    parser.add_argument("--path", required=True, help="The path to the project's source code directory.")
    args = parser.parse_args()
    
    project_name = args.name
    project_path = args.path

    print(f"--- 🚀 Starting Index Building for project: {project_name} ---")

    # --- 1. Configure Global Settings ---
    print(f"--- 🧠 Loading embedding model: {config.EMBEDDING_MODEL_NAME} ---")
    Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBEDDING_MODEL_NAME)
    Settings.llm = None
    print("--- ✅ Embedding model loaded. ---")

    # --- 2. Load Documents ---
    print(f"--- 📂 Loading documents from {project_path} ---")
    reader = SimpleDirectoryReader(
        input_dir=project_path,
        required_exts=[".py"],
        exclude=["*.venv*", "*__pycache__*", "*node_modules*", "*.git*"],
        recursive=True
    )
    documents = reader.load_data()
    print(f"--- ✅ Loaded {len(documents)} documents. ---")

    if not documents:
        print(f"--- ⚠️ No documents found in {project_path}. ---")
        return

    # --- 3. Setup ChromaDB Vector Store (Now with dynamic paths) ---
    vector_store_path = config.get_vector_store_path(project_name)
    collection_name = config.get_collection_name(project_name)
    print(f"--- 💾 Setting up ChromaDB at {vector_store_path} with collection '{collection_name}' ---")
    
    db = chromadb.PersistentClient(path=str(vector_store_path))
    chroma_collection = db.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    print("--- ✅ Vector store setup complete. ---")

    # --- 4. Parse Code and Build Index ---
    print("--- 💻 Parsing code and building index... ---")
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
    print(f"--- 🎉 Index building complete for {project_name}! ---")
    
    nodes_in_db = chroma_collection.count()
    print(f"--- Total nodes indexed: {nodes_in_db} ---")

if __name__ == "__main__":
    config.setup_directories()
    main()