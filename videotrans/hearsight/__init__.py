"""
HearSight功能模块 - MVP版本

提供基于Whisper识别结果的智能段落划分和LLM摘要生成功能
"""

from .segment_merger import merge_srt_to_paragraphs
from .summarizer import generate_summary
from .chat_client import chat_with_openai

__all__ = [
    'merge_srt_to_paragraphs',
    'generate_summary',
    'chat_with_openai',
]
