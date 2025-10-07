# --- engine/rag.py ---

import os
import logging
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import chromadb
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from dotenv import load_dotenv
import config

load_dotenv()

class CustomQueryEngine:
    def __init__(self, retriever, llm):
        self._retriever = retriever
        self._llm = llm

    def query(self, query_text: str):
        retrieved_nodes = self._retriever.retrieve(query_text)
        if not retrieved_nodes:
            yield "Sorry, I could not find any relevant context in the codebase to answer your question."
            return

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
        response_stream = self._llm.generate_content(prompt_template, stream=True)
        
        for chunk in response_stream:
            try:
                yield chunk.text
            except ValueError:
                logging.warning("Skipped an empty chunk from the API.")
                pass

# Cache for query engines, one per project
_query_engines = {} 

def get_query_engine(project_name: str):
    """Initializes and returns a project-specific RAG query engine."""
    global _query_engines
    if project_name in _query_engines:
        return _query_engines[project_name]

    logging.info(f"--- [RAG] Initializing custom engine for '{project_name}'... ---")

    Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBEDDING_MODEL_NAME)

    # Use the new config functions to get project-specific paths
    vector_store_path = config.get_vector_store_path(project_name)
    collection_name = config.get_collection_name(project_name)
    
    vector_store = ChromaVectorStore(
        chroma_collection=chromadb.PersistentClient(path=str(vector_store_path)).get_collection(collection_name)
    )
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    retriever = index.as_retriever(similarity_top_k=3)

    api_key = os.environ.get("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)

    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    llm = genai.GenerativeModel(
        config.AGENT_MODEL_NAME,
        safety_settings=safety_settings
    )

    query_engine = CustomQueryEngine(retriever=retriever, llm=llm)
    _query_engines[project_name] = query_engine # Cache the new engine
    logging.info(f"--- [RAG] Custom RAG engine for '{project_name}' initialized! ---")
    return query_engine