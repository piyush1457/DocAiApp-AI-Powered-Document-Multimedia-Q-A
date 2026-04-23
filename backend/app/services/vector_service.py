import os
import uuid
import faiss
import numpy as np
import json
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from google import genai
from sqlalchemy import select
from app.core.config import settings
from app.db.models.chunk import Chunk

logger = logging.getLogger(__name__)


@dataclass
class ChunkResult:
    text: str
    metadata: Dict[str, Any]
    score: float


class FAISSVectorStore:
    def __init__(self, base_path: str = "/tmp/faiss_indexes", dimension: int = 768):
        self.base_path = base_path
        self.dimension = dimension
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def _get_paths(self, user_id: str):
        index_file = os.path.join(self.base_path, f"{user_id}.index")
        meta_file = os.path.join(self.base_path, f"{user_id}.json")
        return index_file, meta_file

    async def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            try:
                # Try text-embedding-004 first
                response = await self.client.aio.models.embed_content(
                    model="models/text-embedding-004",
                    contents=text,
                    config={"task_type": "retrieval_document"},
                )
                embeddings.append(response.embeddings[0].values)
            except Exception as e:
                logger.warning(f"text-embedding-004 failed, trying embedding-001: {e}")
                try:
                    # Fallback to embedding-001
                    response = await self.client.aio.models.embed_content(
                        model="models/embedding-001",
                        contents=text,
                        config={"task_type": "retrieval_document"},
                    )
                    embeddings.append(response.embeddings[0].values)
                except Exception as e2:
                    logger.error(f"All embedding models failed: {e2}")
                    embeddings.append([0.0] * self.dimension)
        return embeddings

    async def ensure_index_loaded(self, user_id: str, file_id: str, db):
        """
        Checks if index exists for user. If not, rebuilds it from all user chunks in DB.
        """
        index_file, meta_file = self._get_paths(user_id)

        if not os.path.exists(index_file):
            logger.warning(
                f"FAISS index not found for user {user_id}, rebuilding from DB"
            )
            # Fetch all chunks for this user (not just file_id, or maybe just file_id?
            # The prompt says "if no chunks exist for the file_id", but the path has user_id.
            # Usually we group by user).
            # Convert string file_id to UUID for the DB query to avoid AttributeError in some environments
            file_uuid = uuid.UUID(file_id) if isinstance(file_id, str) else file_id
            stmt = select(Chunk).where(Chunk.file_id == file_uuid)
            result = await db.execute(stmt)
            chunks = result.scalars().all()

            if chunks:
                await self.add_chunks(chunks, user_id)
                logger.info(
                    f"Rebuilt index for user {user_id} with {len(chunks)} chunks"
                )
            else:
                logger.warning(
                    f"No chunks found in DB for file {file_id}, cannot build index"
                )

    async def add_chunks(self, chunks: List[Any], user_id: str) -> None:
        """
        Adds chunks to a user-specific index.
        """
        if not chunks:
            return

        index_file, meta_file = self._get_paths(user_id)

        # Load existing index/metadata or create new
        if os.path.exists(index_file):
            index = faiss.read_index(index_file)
            with open(meta_file, "r") as f:
                metadata = json.load(f)
        else:
            index = faiss.IndexIDMap(faiss.IndexFlatL2(self.dimension))
            metadata = {}

        texts = [c.text for c in chunks]
        embeddings = await self._get_embeddings(texts)

        np_embeddings = np.array(embeddings).astype("float32")
        start_id = len(metadata)
        ids = np.arange(start_id, start_id + len(chunks)).astype("int64")

        index.add_with_ids(np_embeddings, ids)

        # Store metadata
        for i, chunk in enumerate(chunks):
            idx = str(ids[i])
            metadata[idx] = {
                "text": chunk.text,
                "file_id": str(chunk.file_id),
                "page_number": getattr(chunk, "page_number", None),
                "start_time": getattr(chunk, "start_time", None),
                "end_time": getattr(chunk, "end_time", None),
            }

        # Save
        faiss.write_index(index, index_file)
        with open(meta_file, "w") as f:
            json.dump(metadata, f)

    async def similarity_search(
        self, query: str, user_id: str, file_id: str, top_k: int = 6
    ) -> List[ChunkResult]:
        """
        Searches user index, filters by file_id.
        """
        index_file, meta_file = self._get_paths(user_id)

        if not os.path.exists(index_file):
            logger.error(f"Index file {index_file} missing for search")
            return []

        index = faiss.read_index(index_file)
        with open(meta_file, "r") as f:
            metadata = json.load(f)

        query_embeddings = await self._get_embeddings([query])
        np_query = np.array(query_embeddings).astype("float32")

        distances, indices = index.search(np_query, 100)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            meta = metadata.get(str(idx))
            if meta and meta.get("file_id") == str(file_id):
                results.append(
                    ChunkResult(text=meta["text"], metadata=meta, score=float(dist))
                )
                if len(results) >= top_k:
                    break
        return results

    def delete_by_file_id(self, user_id: str, file_id: str) -> None:
        """
        Removes vectors associated with file_id from user index.
        """
        index_file, meta_file = self._get_paths(user_id)
        if not os.path.exists(index_file):
            return

        index = faiss.read_index(index_file)
        with open(meta_file, "r") as f:
            metadata = json.load(f)

        ids_to_remove = [
            int(idx)
            for idx, meta in metadata.items()
            if meta.get("file_id") == str(file_id)
        ]

        if ids_to_remove:
            index.remove_ids(np.array(ids_to_remove).astype("int64"))
            for idx in ids_to_remove:
                metadata.pop(str(idx), None)

            faiss.write_index(index, index_file)
            with open(meta_file, "w") as f:
                json.dump(metadata, f)


vector_service = FAISSVectorStore()
