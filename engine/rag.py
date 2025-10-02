# --- engine/rag.py (Production Ready) ---

import os
import sys
import google.generativeai as genai

# --- Path Fix ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- End Path Fix ---

import chromadb
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from dotenv import load_dotenv

import config

load_dotenv()

# --- Custom RAG Implementation to bypass LlamaIndex bugs ---
class CustomQueryEngine:
    def __init__(self, retriever, llm):
        self._retriever = retriever
        self._llm = llm

    def query(self, query_text: str) -> str:
        retrieved_nodes = self._retriever.retrieve(query_text)
        if not retrieved_nodes:
            return "Sorry, I could not find any relevant context in the codebase to answer your question."
        
        context_str = "\n\n".join([n.get_content() for n in retrieved_nodes])
        prompt_template = f"""
Context information from the codebase is below.
---------------------
{context_str}
---------------------
Given the context information and not any prior knowledge, please answer the query.
Query: {query_text}
Answer:
"""
        response = self._llm.generate_content(prompt_template)
        return response.text

# --- Singleton pattern to cache the engine ---
_query_engine = None

def get_query_engine():
    """
    Initializes and returns our custom RAG query engine.
    Caches the engine to avoid reloading models on every call.
    """
    global _query_engine
    if _query_engine is not None:
        return _query_engine

    print("--- 🧠 Initializing custom RAG engine for the first time... ---")

    # 1. Configure LlamaIndex retriever
    Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBEDDING_MODEL_NAME)
    vector_store = ChromaVectorStore(
        chroma_collection=chromadb.PersistentClient(path=str(config.VECTOR_STORE_PATH)).get_collection(config.COLLECTION_NAME)
    )
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    retriever = index.as_retriever(similarity_top_k=3)

    # 2. Configure Google GenAI model
    api_key = os.environ.get("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)
    llm = genai.GenerativeModel(config.AGENT_MODEL_NAME)

    # 3. Create and cache our custom engine
    _query_engine = CustomQueryEngine(retriever=retriever, llm=llm)
    print("--- 🎉 Custom RAG engine initialized successfully! ---")
    return _query_engine

# --- For testing purposes ---
if __name__ == '__main__':
    query_engine = get_query_engine()
    response = query_engine.query("What is the purpose of the 'create_app' function?")
    print("\n--- 📝 Final Test Response ---")
    print(response)