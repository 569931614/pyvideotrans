"""
Qdrant Client for pyvideotrans

Handles interaction with Qdrant vector database for storing video chunks
and metadata.
"""

import hashlib
import logging
import os
import uuid
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)

from .srt_parser import SubtitleChunk

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    """Video metadata for storage"""
    video_id: str
    video_title: str
    video_path: str
    source_type: str = "pyvideotrans"
    language: str = "zh-cn"
    duration: float = 0.0
    chunk_count: int = 0
    video_summary: str = ""
    keywords: List[str] = None
    srt_file: str = ""
    folder_id: Optional[str] = None  # 文件夹ID
    folder: Optional[str] = None  # 文件夹名称


def generate_video_id(video_path: str, language: str, source_type: str = "pyvideotrans") -> str:
    """
    Generate consistent video ID across systems

    Args:
        video_path: Absolute path to video file
        language: Language code (e.g., "zh-cn", "en")
        source_type: Source system ("pyvideotrans" or "hearsight")

    Returns:
        Unique hash string (16 characters)
    """
    # Normalize path
    normalized_path = os.path.normpath(os.path.abspath(video_path))

    # Combine components
    unique_string = f"{normalized_path}|{language}|{source_type}"

    # Hash to fixed length
    hash_object = hashlib.sha256(unique_string.encode())
    return hash_object.hexdigest()[:16]


class QdrantVectorStore:
    """Qdrant vector store client for pyvideotrans"""

    def __init__(
        self,
        url: str = "http://localhost:6333",
        api_key: Optional[str] = None,
        collection_prefix: str = "video",
        vector_size: int = 1024  # Default to bge-large-zh-v1.5 dimension
    ):
        """
        Initialize Qdrant client

        Args:
            url: Qdrant server URL
            api_key: Optional API key
            collection_prefix: Prefix for collection names
            vector_size: Vector dimension (default: 1024 for bge-large-zh-v1.5)
        """
        self.client = QdrantClient(url=url, api_key=api_key)
        self.collection_chunks = f"{collection_prefix}_chunks"
        self.collection_metadata = f"{collection_prefix}_metadata"
        self.vector_size = vector_size

        # Ensure collections exist
        self.ensure_collections()

    def ensure_collections(self):
        """
        Ensure required collections exist

        Uses self.vector_size from __init__
        """
        try:
            # Check and create video_chunks collection
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_chunks not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_chunks,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_chunks} (vector_size={self.vector_size})")
            else:
                logger.info(f"Collection already exists: {self.collection_chunks}")

            # Note: video_metadata doesn't need vectors, but Qdrant requires it
            # Use the same vector size as chunks collection for consistency
            if self.collection_metadata not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_metadata,
                    vectors_config=VectorParams(
                        size=self.vector_size,  # Use same size as chunks
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_metadata} (vector_size={self.vector_size})")

        except Exception as e:
            logger.error(f"Failed to ensure collections: {e}")
            raise

    def delete_existing_chunks(self, video_id: str):
        """
        Delete existing chunks for a video (for deduplication)

        Args:
            video_id: Video ID to delete
        """
        try:
            # Delete from chunks collection
            self.client.delete(
                collection_name=self.collection_chunks,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="video_id",
                            match=MatchValue(value=video_id)
                        )
                    ]
                )
            )
            logger.info(f"Deleted existing chunks for video_id: {video_id}")

        except Exception as e:
            logger.warning(f"Failed to delete existing chunks: {e}")

    def upsert_chunks(
        self,
        video_id: str,
        video_title: str,
        video_path: str,
        language: str,
        chunks: List[SubtitleChunk],
        embeddings: List[List[float]],
        paragraph_summaries: List[str],
        srt_file: str
    ):
        """
        Upsert chunks to Qdrant

        Args:
            video_id: Unique video identifier
            video_title: Video title
            video_path: Path to video file
            language: Language code
            chunks: List of subtitle chunks
            embeddings: List of embedding vectors
            paragraph_summaries: List of paragraph summaries
            srt_file: Path to SRT file
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")

        if len(paragraph_summaries) != len(chunks):
            # Pad with empty strings if needed
            paragraph_summaries = paragraph_summaries + [""] * (len(chunks) - len(paragraph_summaries))

        # Delete existing chunks for this video
        self.delete_existing_chunks(video_id)

        # Prepare points
        points = []
        for i, (chunk, embedding, summary) in enumerate(zip(chunks, embeddings, paragraph_summaries)):
            # Generate UUID from video_id and chunk index (deterministic)
            point_id_str = f"{video_id}_{i}"
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, point_id_str))

            payload = {
                "video_id": video_id,
                "video_title": video_title,
                "video_path": video_path,
                "source_type": "pyvideotrans",
                "language": language,
                "chunk_text": chunk.text,
                "chunk_index": chunk.chunk_index,
                "start_time": chunk.start_time,
                "end_time": chunk.end_time,
                "paragraph_summary": summary,
                "created_at": datetime.utcnow().isoformat(),
                "srt_file": srt_file
            }

            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            ))

        # Upload to Qdrant
        self.client.upsert(
            collection_name=self.collection_chunks,
            points=points
        )

        logger.info(f"Upserted {len(points)} chunks for video_id: {video_id}")

    def upsert_metadata(
        self,
        metadata: VideoMetadata
    ):
        """
        Upsert video metadata to Qdrant

        Args:
            metadata: Video metadata object
        """
        payload = {
            "video_id": metadata.video_id,  # Add video_id to payload for easier querying
            "video_title": metadata.video_title,
            "video_path": metadata.video_path,
            "source_type": metadata.source_type,
            "language": metadata.language,
            "duration": metadata.duration,
            "chunk_count": metadata.chunk_count,
            "video_summary": metadata.video_summary,
            "keywords": metadata.keywords or [],
            "created_at": datetime.utcnow().isoformat(),
            "srt_file": metadata.srt_file
        }

        # Use dummy vector since Qdrant requires vectors
        # Match the dimension configured for the collection
        dummy_vector = [0.0] * self.vector_size

        # Generate UUID for metadata point
        metadata_point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"metadata_{metadata.video_id}"))

        point = PointStruct(
            id=metadata_point_id,
            vector=dummy_vector,
            payload=payload
        )

        self.client.upsert(
            collection_name=self.collection_metadata,
            points=[point]
        )

        logger.info(f"Upserted metadata for video_id: {metadata.video_id}")

    def check_video_exists(self, video_id: str) -> bool:
        """
        Check if video already exists in Qdrant

        Args:
            video_id: Video ID to check

        Returns:
            True if video exists
        """
        try:
            result = self.client.retrieve(
                collection_name=self.collection_metadata,
                ids=[video_id]
            )
            return len(result) > 0

        except Exception as e:
            logger.warning(f"Failed to check video existence: {e}")
            return False

    def delete_video(self, video_id: str) -> bool:
        """
        Delete all data for a video from Qdrant

        Args:
            video_id: Video ID to delete

        Returns:
            True if deletion was successful
        """
        try:
            # Delete chunks from video_chunks collection
            self.client.delete(
                collection_name=self.collection_chunks,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="video_id",
                            match=MatchValue(value=video_id)
                        )
                    ]
                )
            )
            logger.info(f"Deleted chunks for video_id: {video_id}")

            # Delete metadata from video_metadata collection
            try:
                self.client.delete(
                    collection_name=self.collection_metadata,
                    points_selector=[video_id]
                )
                logger.info(f"Deleted metadata for video_id: {video_id}")
            except Exception as e:
                logger.warning(f"Failed to delete metadata (might not exist): {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to delete video from Qdrant: {e}")
            return False

    def delete_by_video_path(self, video_path: str) -> bool:
        """
        Delete all data for a video by video path (all languages/sources)

        Args:
            video_path: Video file path (can be local path or OSS URL)

        Returns:
            True if deletion was successful and data was actually deleted
        """
        try:
            # 不要规范化OSS URL，直接使用原始路径
            if video_path.startswith(('http://', 'https://')):
                search_path = video_path
                logger.info(f"Using OSS URL directly: {search_path}")
            else:
                search_path = os.path.normpath(os.path.abspath(video_path))
                logger.info(f"Using normalized local path: {search_path}")

            deleted_any = False

            # First, check if any chunks exist for this video_path
            chunks_check = self.client.scroll(
                collection_name=self.collection_chunks,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="video_path",
                            match=MatchValue(value=search_path)
                        )
                    ]
                ),
                limit=1,
                with_payload=False,
                with_vectors=False
            )

            if chunks_check[0]:  # If chunks found
                # Delete all chunks matching this video_path
                self.client.delete(
                    collection_name=self.collection_chunks,
                    points_selector=Filter(
                        must=[
                            FieldCondition(
                                key="video_path",
                                match=MatchValue(value=search_path)
                            )
                        ]
                    )
                )
                logger.info(f"Deleted all chunks for video_path: {search_path}")
                deleted_any = True

            # Delete all metadata entries matching this video_path
            # Note: We can't directly filter metadata deletion by payload,
            # so we need to query first then delete by IDs
            try:
                # Search for metadata entries with this video_path
                search_result = self.client.scroll(
                    collection_name=self.collection_metadata,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(
                                key="video_path",
                                match=MatchValue(value=search_path)
                            )
                        ]
                    ),
                    limit=100
                )

                if search_result[0]:  # If any results found
                    metadata_ids = [point.id for point in search_result[0]]
                    self.client.delete(
                        collection_name=self.collection_metadata,
                        points_selector=metadata_ids
                    )
                    logger.info(f"Deleted {len(metadata_ids)} metadata entries for video_path: {search_path}")
                    deleted_any = True
            except Exception as e:
                logger.warning(f"Failed to delete metadata entries (might not exist): {e}")

            if not deleted_any:
                logger.warning(f"No data found to delete for video_path: {search_path}")

            return deleted_any

        except Exception as e:
            logger.error(f"Failed to delete video by path from Qdrant: {e}")
            return False
