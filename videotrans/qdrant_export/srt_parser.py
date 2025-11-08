"""
SRT File Parser with Encoding Detection and Chunking

Handles parsing of SRT subtitle files with automatic encoding detection,
and chunks subtitles semantically for vector storage.
"""

import os
import re
from dataclasses import dataclass
from typing import List, Tuple
import chardet
import logging

logger = logging.getLogger(__name__)


@dataclass
class SubtitleEntry:
    """Represents a single subtitle entry"""
    index: int
    start_time: float  # seconds
    end_time: float  # seconds
    text: str


@dataclass
class SubtitleChunk:
    """Represents a chunked group of subtitles"""
    chunk_index: int
    start_time: float
    end_time: float
    text: str
    token_count: int


def parse_timestamp(timestamp: str) -> float:
    """
    Parse SRT timestamp to seconds

    Format: HH:MM:SS,mmm or HH:MM:SS.mmm

    Args:
        timestamp: Timestamp string

    Returns:
        Time in seconds
    """
    timestamp = timestamp.strip().replace(',', '.')
    match = re.match(r'(\d+):(\d+):(\d+)\.(\d+)', timestamp)
    if not match:
        raise ValueError(f"Invalid timestamp format: {timestamp}")

    hours, minutes, seconds, milliseconds = map(int, match.groups())
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
    return total_seconds


def detect_encoding(file_path: str) -> str:
    """
    Detect file encoding using chardet

    Args:
        file_path: Path to file

    Returns:
        Detected encoding name (e.g., 'utf-8', 'gbk')
    """
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        confidence = result['confidence']

        logger.info(f"Detected encoding: {encoding} (confidence: {confidence:.2%})")

        # Map common Chinese encodings
        if encoding and encoding.lower() in ['gb2312', 'gb18030']:
            encoding = 'gbk'

        return encoding or 'utf-8'


def parse_srt_file(srt_path: str) -> List[SubtitleEntry]:
    """
    Parse SRT file into subtitle entries

    Args:
        srt_path: Path to SRT file

    Returns:
        List of SubtitleEntry objects

    Raises:
        FileNotFoundError: If SRT file doesn't exist
        ValueError: If SRT format is invalid
    """
    if not os.path.exists(srt_path):
        raise FileNotFoundError(f"SRT file not found: {srt_path}")

    # Detect encoding
    encoding = detect_encoding(srt_path)

    # Read file with detected encoding
    try:
        with open(srt_path, 'r', encoding=encoding) as f:
            content = f.read()
    except UnicodeDecodeError:
        # Fallback to utf-8 if detected encoding fails
        logger.warning(f"Failed to decode with {encoding}, trying utf-8")
        with open(srt_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

    # Parse SRT format
    entries = []
    blocks = re.split(r'\n\s*\n', content.strip())

    for block in blocks:
        if not block.strip():
            continue

        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue

        try:
            # Parse index
            index = int(lines[0].strip())

            # Parse timestamps
            timestamp_line = lines[1].strip()
            match = re.match(r'(\S+)\s*-->\s*(\S+)', timestamp_line)
            if not match:
                logger.warning(f"Invalid timestamp line: {timestamp_line}")
                continue

            start_str, end_str = match.groups()
            start_time = parse_timestamp(start_str)
            end_time = parse_timestamp(end_str)

            # Parse text (remaining lines)
            text = '\n'.join(lines[2:]).strip()

            entries.append(SubtitleEntry(
                index=index,
                start_time=start_time,
                end_time=end_time,
                text=text
            ))

        except Exception as e:
            logger.warning(f"Failed to parse SRT block: {e}\n{block}")
            continue

    logger.info(f"Parsed {len(entries)} subtitle entries from {srt_path}")
    return entries


def estimate_token_count(text: str) -> int:
    """
    Estimate token count for text

    Rough estimation:
    - Chinese: 1 character ≈ 1.5 tokens
    - English: 1 word ≈ 1.3 tokens

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    # Count Chinese characters
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))

    # Count English words
    english_words = len(re.findall(r'[a-zA-Z]+', text))

    # Rough estimation
    estimated_tokens = int(chinese_chars * 1.5 + english_words * 1.3)

    return max(estimated_tokens, len(text) // 4)  # Minimum fallback


def chunk_subtitles(
    entries: List[SubtitleEntry],
    max_tokens: int = 500,
    max_gap_seconds: float = 3.0,
    min_entries_per_chunk: int = 3,
    max_entries_per_chunk: int = 10
) -> List[SubtitleChunk]:
    """
    Chunk subtitles into semantic groups

    Strategy:
    - Combine 3-10 consecutive subtitle entries
    - Respect max_tokens limit
    - Break on gaps > max_gap_seconds
    - Preserve temporal information

    Args:
        entries: List of subtitle entries
        max_tokens: Maximum tokens per chunk
        max_gap_seconds: Maximum time gap to allow in chunk
        min_entries_per_chunk: Minimum entries to group together
        max_entries_per_chunk: Maximum entries to group together

    Returns:
        List of SubtitleChunk objects
    """
    if not entries:
        return []

    chunks = []
    current_chunk_entries = []
    current_tokens = 0
    chunk_index = 0

    for i, entry in enumerate(entries):
        entry_tokens = estimate_token_count(entry.text)

        # Check if we should start new chunk
        should_break = False

        if current_chunk_entries:
            # Check time gap
            time_gap = entry.start_time - current_chunk_entries[-1].end_time
            if time_gap > max_gap_seconds:
                should_break = True

            # Check token limit
            if current_tokens + entry_tokens > max_tokens:
                should_break = True

            # Check max entries limit
            if len(current_chunk_entries) >= max_entries_per_chunk:
                should_break = True

        # Break if needed and we have minimum entries
        if should_break and len(current_chunk_entries) >= min_entries_per_chunk:
            # Create chunk from current entries
            chunk_text = '\n'.join(e.text for e in current_chunk_entries)
            chunks.append(SubtitleChunk(
                chunk_index=chunk_index,
                start_time=current_chunk_entries[0].start_time,
                end_time=current_chunk_entries[-1].end_time,
                text=chunk_text,
                token_count=current_tokens
            ))
            chunk_index += 1

            # Reset
            current_chunk_entries = []
            current_tokens = 0

        # Add current entry to chunk
        current_chunk_entries.append(entry)
        current_tokens += entry_tokens

    # Add final chunk
    if current_chunk_entries:
        chunk_text = '\n'.join(e.text for e in current_chunk_entries)
        chunks.append(SubtitleChunk(
            chunk_index=chunk_index,
            start_time=current_chunk_entries[0].start_time,
            end_time=current_chunk_entries[-1].end_time,
            text=chunk_text,
            token_count=current_tokens
        ))

    logger.info(f"Created {len(chunks)} chunks from {len(entries)} entries")
    return chunks
