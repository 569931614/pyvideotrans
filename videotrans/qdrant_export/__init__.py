"""
Qdrant Export Module for pyvideotrans

This module handles exporting translated SRT files to Qdrant vector database
for RAG-based question answering integration with HearSight.

Main workflow:
1. Parse SRT file
2. Chunk subtitles semantically
3. Generate paragraph summaries for each chunk
4. Generate video-level summary
5. Generate embeddings for chunks
6. Upload to Qdrant collections
"""

from .export import export_to_qdrant, ExportResult, ExportConfig, validate_export_config

__all__ = ['export_to_qdrant', 'ExportResult', 'ExportConfig', 'validate_export_config']
