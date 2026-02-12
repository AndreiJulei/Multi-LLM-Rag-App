import uuid
from typing import Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from dotenv import load_dotenv

try:
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
except ImportError:
    from chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 import (
        ONNXMiniLM_L6_V2 as DefaultEmbeddingFunction,
    )

load_dotenv()

_COLLECTION_NAME = "rag_documents"

class RagService:
    def __init__(self):
        self.persist_directory = "./chroma_db"
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self._ef = DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name=_COLLECTION_NAME,
            embedding_function=self._ef,
        )

    # indexing
    def add_document_to_index(self, text: str, doc_id: int, collection_id: Optional[int] = None):
        """Chunk, embed, and store a document's text in ChromaDB."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
        )
        chunks = text_splitter.split_text(text)
        if not chunks:
            return
        metadatas = [{"doc_id": doc_id, "collection_id": collection_id} for _ in chunks]
        ids = [str(uuid.uuid4()) for _ in chunks]
        self.collection.add(documents=chunks, metadatas=metadatas, ids=ids)
        print(f"Indexed {len(chunks)} chunks for doc {doc_id} (collection {collection_id})")

    # retrieve
    def _safe_k(self, k: int) -> int:
        """Clamp k to the number of documents actually stored."""
        count = self.collection.count()
        return max(1, min(k, count)) if count > 0 else 0

    def get_relevant_context(self, query: str, k: int = 3) -> str:
        """Global similarity search (no collection filter)."""
        n = self._safe_k(k)
        if n == 0:
            return ""
        results = self.collection.query(query_texts=[query], n_results=n)
        docs = results.get("documents", [[]])[0]
        return "\n---\n".join(docs)

    def query_collection(self, collection_id: int, query: str, k: int = 3) -> str:
        """Similarity search scoped to a specific collection."""
        n = self._safe_k(k)
        if n == 0:
            return ""
        results = self.collection.query(
            query_texts=[query],
            n_results=n,
            where={"collection_id": collection_id},
        )
        docs = results.get("documents", [[]])[0]
        if not docs:
            return self.get_relevant_context(query, k=k)
        return "\n---\n".join(docs)

    # cleanu
    def delete_collection_vectors(self, collection_id: int):
        """Remove all vectors belonging to a given collection."""
        try:
            results = self.collection.get(where={"collection_id": collection_id})
            if results and results["ids"]:
                self.collection.delete(ids=results["ids"])
                print(f"Deleted {len(results['ids'])} vectors for collection {collection_id}")
        except Exception as e:
            print(f"Warning: could not delete vectors for collection {collection_id}: {e}")

    def delete_document_vectors(self, doc_id: int):
        """Remove all vectors belonging to a specific document."""
        try:
            results = self.collection.get(where={"doc_id": doc_id})
            if results and results["ids"]:
                self.collection.delete(ids=results["ids"])
        except Exception as e:
            print(f"Warning: could not delete vectors for doc {doc_id}: {e}")

rag_service = RagService()
