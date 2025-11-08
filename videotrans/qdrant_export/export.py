"""
Main Export Function for Qdrant Integration

Coordinates the full export workflow:
1. Parse SRT file
2. Chunk subtitles
3. Generate summaries
4. Generate embeddings
5. Upload to Qdrant
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional

from .srt_parser import parse_srt_file, chunk_subtitles
from .summarizer import generate_summaries
from .embedder import generate_embeddings
from .qdrant_client import QdrantVectorStore, VideoMetadata, generate_video_id

logger = logging.getLogger(__name__)


@dataclass
class ExportResult:
    """Result of export operation"""
    success: bool
    video_id: str
    chunks_count: int
    error_message: str = ""


@dataclass
class ExportConfig:
    """Configuration for Qdrant export"""
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None

    # Summary generation
    enable_summaries: bool = True
    llm_api_url: str = ""
    llm_api_key: str = ""
    llm_model: str = "deepseek-ai/DeepSeek-V3"

    # Embedding generation
    embedding_api_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"

    # Chunking parameters
    max_tokens_per_chunk: int = 500
    max_gap_seconds: float = 3.0

    # Folder organization
    folder_id: Optional[str] = None  # 视频所属文件夹ID


def export_to_qdrant(
    srt_path: str,
    video_path: str,
    video_title: str,
    language: str,
    config: ExportConfig
) -> ExportResult:
    """
    Export translated SRT to Qdrant

    Main workflow:
    1. Parse SRT file
    2. Chunk subtitles
    3. Generate summaries (optional)
    4. Generate embeddings
    5. Upload to Qdrant

    Args:
        srt_path: Path to SRT file
        video_path: Path to video file
        video_title: Video title
        language: Language code (e.g., "zh-cn", "en")
        config: Export configuration

    Returns:
        ExportResult with success status and details
    """
    try:
        logger.info(f"Starting Qdrant export for: {video_title}")
        logger.info(f"SRT file: {srt_path}")
        logger.info(f"Language: {language}")

        # Step 1: Parse SRT file
        logger.info("Step 1/5: Parsing SRT file...")
        entries = parse_srt_file(srt_path)

        if not entries:
            return ExportResult(
                success=False,
                video_id="",
                chunks_count=0,
                error_message="No subtitle entries found in SRT file"
            )

        # Step 2: Chunk subtitles
        logger.info("Step 2/5: Chunking subtitles...")
        chunks = chunk_subtitles(
            entries,
            max_tokens=config.max_tokens_per_chunk,
            max_gap_seconds=config.max_gap_seconds
        )

        if not chunks:
            return ExportResult(
                success=False,
                video_id="",
                chunks_count=0,
                error_message="No chunks generated from subtitles"
            )

        logger.info(f"Created {len(chunks)} chunks")

        # Step 3: Generate summaries (optional)
        paragraph_summaries = []
        video_summary = ""

        if config.enable_summaries:
            logger.info("Step 3/5: Generating summaries...")
            try:
                paragraph_summaries, video_summary = generate_summaries(
                    chunks=chunks,
                    llm_api_url=config.llm_api_url,
                    llm_api_key=config.llm_api_key,
                    llm_model=config.llm_model,
                    video_title=video_title
                )
                logger.info(f"Generated {len(paragraph_summaries)} paragraph summaries")
            except Exception as e:
                logger.warning(f"Failed to generate summaries (non-fatal): {e}")
                # Continue without summaries
                paragraph_summaries = [""] * len(chunks)
                video_summary = ""
        else:
            logger.info("Step 3/5: Skipping summary generation (disabled)")
            paragraph_summaries = [""] * len(chunks)

        # Step 4: Generate embeddings
        logger.info("Step 4/5: Generating embeddings...")
        chunk_texts = [chunk.text for chunk in chunks]

        embeddings = generate_embeddings(
            texts=chunk_texts,
            embedding_api_url=config.embedding_api_url,
            embedding_api_key=config.embedding_api_key,
            embedding_model=config.embedding_model
        )

        logger.info(f"Generated {len(embeddings)} embeddings")

        # Detect vector size from first embedding
        vector_size = len(embeddings[0]) if embeddings else 1024

        # Step 5: Upload to Qdrant
        logger.info("Step 5/5: Uploading to Qdrant...")

        # Generate video ID
        video_id = generate_video_id(video_path, language, "pyvideotrans")

        # Initialize Qdrant client with correct vector size
        qdrant_store = QdrantVectorStore(
            url=config.qdrant_url,
            api_key=config.qdrant_api_key,
            vector_size=vector_size
        )

        # Upload chunks
        qdrant_store.upsert_chunks(
            video_id=video_id,
            video_title=video_title,
            video_path=video_path,
            language=language,
            chunks=chunks,
            embeddings=embeddings,
            paragraph_summaries=paragraph_summaries,
            srt_file=srt_path
        )

        # Upload metadata
        duration = chunks[-1].end_time if chunks else 0.0

        # 获取文件夹名称（如果指定了folder_id）
        folder_name = None
        if config.folder_id:
            try:
                from videotrans.hearsight.vector_store import get_vector_store
                vector_store = get_vector_store()
                folders = vector_store.list_folders()
                for folder in folders:
                    if folder.get('folder_id') == config.folder_id:
                        folder_name = folder.get('name')
                        break
                logger.info(f"Assigning to folder: {folder_name} (ID: {config.folder_id})")
            except Exception as e:
                logger.warning(f"Failed to get folder name: {e}")

        metadata = VideoMetadata(
            video_id=video_id,
            video_title=video_title,
            video_path=video_path,
            source_type="pyvideotrans",
            language=language,
            duration=duration,
            chunk_count=len(chunks),
            video_summary=video_summary,
            keywords=[],
            srt_file=srt_path,
            folder_id=config.folder_id,
            folder=folder_name
        )

        qdrant_store.upsert_metadata(metadata)

        logger.info(f"✓ Successfully exported to Qdrant: video_id={video_id}, chunks={len(chunks)}")

        return ExportResult(
            success=True,
            video_id=video_id,
            chunks_count=len(chunks)
        )

    except Exception as e:
        error_msg = f"Qdrant export failed: {str(e)}"
        logger.error(error_msg, exc_info=True)

        return ExportResult(
            success=False,
            video_id="",
            chunks_count=0,
            error_message=error_msg
        )


def validate_export_config(config: ExportConfig) -> tuple[bool, str]:
    """
    Validate export configuration

    Args:
        config: Export configuration

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not config.qdrant_url:
        return False, "Qdrant URL is required"

    if not config.embedding_api_url:
        return False, "Embedding API URL is required"

    if not config.embedding_api_key:
        return False, "Embedding API key is required"

    if config.enable_summaries:
        if not config.llm_api_url:
            return False, "LLM API URL is required when summaries are enabled"
        if not config.llm_api_key:
            return False, "LLM API key is required when summaries are enabled"

    return True, ""
