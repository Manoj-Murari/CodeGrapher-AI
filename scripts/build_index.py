# --- scripts/build_index.py ---

import chromadb
from pathlib import Path
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import CodeSplitter
from llama_index.core import Settings
import logging

import config

def build_vector_store(project_name: str, project_path: str):
    """
    Analyzes a codebase in a given path, splits the code into chunks,
    generates embeddings, and stores them in a ChromaDB vector store.
    """
    logging.info(f"--- 🚀 Starting Index Building for project: {project_name} ---")

    Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBEDDING_MODEL_NAME)
    Settings.llm = None

    # --- THE DEFINITIVE FIX ---
    # 1. Manually check for the existence of .py files before calling LlamaIndex.
    
    # We use pathlib to recursively search for any file ending in .py
    # The `next()` function with a default of `None` is a very efficient way
    # to check if there's at least one match without iterating through everything.
    
    py_files = list(Path(project_path).rglob("*.py"))
    
    if not py_files:
        logging.warning(f"--- ⚠️ No .py files found in {project_path}. Skipping vector store creation. ---")
        return # Exit gracefully

    # 2. Only if files are found, proceed with the LlamaIndex reader.
    reader = SimpleDirectoryReader(
        input_dir=project_path,
        required_exts=[".py"],
        exclude=["*.venv*", "*__pycache__*", "*node_modules*", "*.git*"],
        recursive=True
    )
    documents = reader.load_data()
    logging.info(f"--- ✅ Loaded {len(documents)} documents. ---")

    # This check is now redundant but kept as a safeguard.
    if not documents:
        logging.warning(f"--- ⚠️ LlamaIndex reader found no documents unexpectedly. Skipping. ---")
        return

    # Set up the persistent ChromaDB vector store
    vector_store_path = config.get_vector_store_path(project_name)
    collection_name = config.get_collection_name(project_name)
    logging.info(f"--- 💾 Setting up ChromaDB at {vector_store_path} with collection '{collection_name}' ---")
    
    db = chromadb.PersistentClient(path=str(vector_store_path))
    chroma_collection = db.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Configure the code splitter
    python_splitter = CodeSplitter(
        language="python", chunk_lines=40, chunk_lines_overlap=15, max_chars=1500
    )
    Settings.transformations = [python_splitter]

    # Process documents and build the index
    VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True
    )
    logging.info(f"--- 🎉 Index building complete for {project_name}! ---")
