# --- engine/rag.py ---

import os
import logging
from dotenv import load_dotenv
from typing import List

import chromadb
from llama_index.core import VectorStoreIndex, Settings, QueryBundle
from llama_index.core.schema import NodeWithScore
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from sentence_transformers import CrossEncoder
# --- THE FIX: Corrected import path for Gemini ---
from llama_index.llms.gemini import Gemini

import config
from engine.context import ProjectContext

load_dotenv()

class LocalRerank(BaseNodePostprocessor):
    # ... (class code is correct and remains the same)
    def __init__(self, model_name: str = "BAAI/bge-reranker-base", top_n: int = 3):
        super().__init__()
        self._model = CrossEncoder(model_name)
        self._top_n = top_n

    def _postprocess_nodes(
        self, nodes: List[NodeWithScore], query_bundle: QueryBundle
    ) -> List[NodeWithScore]:
        if not nodes or not query_bundle.query_str:
            return nodes
        query_and_nodes = [(query_bundle.query_str, node.get_content()) for node in nodes]
        scores = self._model.predict(query_and_nodes)
        for node, score in zip(nodes, scores):
            node.score = float(score)
        sorted_nodes = sorted(nodes, key=lambda x: x.score or 0.0, reverse=True)
        return sorted_nodes[:self._top_n]


_query_engines = {}

def get_query_engine(context: ProjectContext):
    # ... (this function is correct and remains the same)
    project_name = context.project_id
    if project_name in _query_engines:
        return _query_engines[project_name]

    logging.info(f"--- [RAG] Initializing ADVANCED engine for '{project_name}'... ---")
    
    Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBEDDING_MODEL_NAME)
    
    # --- THE FIX: Use the new Gemini class name ---
    llm = Gemini(model_name=config.AGENT_MODEL_NAME, api_key=os.environ.get("GOOGLE_API_KEY"))

    vector_store_path = str(context.vector_store_path)
    collection_name = config.get_collection_name(project_name)
    vector_store = ChromaVectorStore(
        chroma_collection=chromadb.PersistentClient(path=vector_store_path).get_collection(collection_name)
    )
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    retriever = VectorIndexRetriever(index=index, similarity_top_k=10)
    reranker = LocalRerank(top_n=3)

    query_engine = RetrieverQueryEngine.from_args(
        retriever,
        llm=llm,
        node_postprocessors=[reranker],
        streaming=True,
    )

    _query_engines[project_name] = query_engine
    logging.info(f"--- [RAG] Advanced RAG engine for '{project_name}' initialized! ---")
    return query_engine

