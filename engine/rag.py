# --- engine/rag.py ---

import os
import logging
import google.generativeai as genai
# --- ADD THIS IMPORT ---
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
        
        # --- FIX 2: Add error handling for empty chunks ---
        for chunk in response_stream:
            try:
                yield chunk.text
            except ValueError:
                # This can happen if the API returns an empty chunk (e.g. safety filters)
                # We'll just skip it and continue to the next chunk.
                logging.warning("Skipped an empty chunk from the API.")
                pass

_query_engine = None

def get_query_engine():
    global _query_engine
    if _query_engine is not None:
        return _query_engine

    logging.info("--- [RAG] Initializing custom engine for the first time... ---")

    Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBEDDING_MODEL_NAME)
    vector_store = ChromaVectorStore(
        chroma_collection=chromadb.PersistentClient(path=str(config.VECTOR_STORE_PATH)).get_collection(config.COLLECTION_NAME)
    )
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    retriever = index.as_retriever(similarity_top_k=3)

    api_key = os.environ.get("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)

    # --- FIX 1: Define permissive safety settings ---
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    llm = genai.GenerativeModel(
        config.AGENT_MODEL_NAME,
        safety_settings=safety_settings # Apply the settings here
    )

    _query_engine = CustomQueryEngine(retriever=retriever, llm=llm)
    logging.info("--- [RAG] Custom RAG engine initialized successfully! ---")
    return _query_engine