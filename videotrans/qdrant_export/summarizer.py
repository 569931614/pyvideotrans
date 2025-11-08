"""
Summary Generation Module using LLM API

Generates paragraph-level and video-level summaries for subtitle chunks.
"""

import logging
import time
from typing import List, Tuple
import requests
from .srt_parser import SubtitleChunk

logger = logging.getLogger(__name__)


class SummaryGenerator:
    """Generates summaries using OpenAI-compatible LLM API"""

    def __init__(
        self,
        api_url: str,
        api_key: str,
        model: str = "deepseek-ai/DeepSeek-V3",
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize summary generator

        Args:
            api_url: Base URL for LLM API (e.g., https://api.siliconflow.cn/v1)
            api_key: API key
            model: Model name
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay in seconds (exponential backoff)
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _call_llm(
        self,
        messages: List[dict],
        temperature: float = 0.3,
        max_tokens: int = 500
    ) -> str:
        """
        Call LLM API with retry logic

        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLM response text

        Raises:
            Exception: If all retries fail
        """
        endpoint = f"{self.api_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()

                result = response.json()
                content = result['choices'][0]['message']['content']
                return content.strip()

            except requests.exceptions.RequestException as e:
                logger.warning(f"LLM API call failed (attempt {attempt + 1}/{self.max_retries}): {e}")

                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    raise Exception(f"LLM API call failed after {self.max_retries} attempts: {e}")

    def generate_paragraph_summaries(
        self,
        chunks: List[SubtitleChunk],
        batch_size: int = 10
    ) -> List[str]:
        """
        Generate paragraph summary for each chunk

        Args:
            chunks: List of subtitle chunks
            batch_size: Number of chunks to process per API call

        Returns:
            List of summary strings (same length as chunks)
        """
        summaries = []

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_summaries = self._generate_paragraph_summaries_batch(batch)
            summaries.extend(batch_summaries)

            logger.info(f"Generated paragraph summaries for chunks {i}-{i + len(batch)}")

        return summaries

    def _generate_paragraph_summaries_batch(
        self,
        chunks: List[SubtitleChunk]
    ) -> List[str]:
        """
        Generate summaries for a batch of chunks

        Args:
            chunks: List of chunks to summarize

        Returns:
            List of summaries
        """
        # Format chunks for batch summarization
        chunks_text = ""
        for idx, chunk in enumerate(chunks):
            chunks_text += f"\n\n[片段 {idx + 1}]\n{chunk.text}\n"

        prompt = f"""请为以下视频片段分别生成简洁的摘要（每个片段1-2句话）。

视频片段：{chunks_text}

请按以下格式返回摘要：
[片段 1] 摘要内容
[片段 2] 摘要内容
[片段 3] 摘要内容
...

摘要："""

        messages = [
            {
                "role": "system",
                "content": "你是一个专业的视频内容总结助手。请为每个片段生成简洁、准确的摘要。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            response = self._call_llm(messages, temperature=0.3, max_tokens=1000)

            # Parse summaries from response
            summaries = []
            lines = response.strip().split('\n')

            for line in lines:
                line = line.strip()
                # Match pattern: [片段 N] summary
                match = line.split(']', 1)
                if len(match) == 2:
                    summary = match[1].strip()
                    summaries.append(summary)

            # Ensure we have summaries for all chunks
            while len(summaries) < len(chunks):
                summaries.append("")  # Empty summary as fallback

            return summaries[:len(chunks)]

        except Exception as e:
            logger.error(f"Failed to generate paragraph summaries: {e}")
            # Return empty summaries as fallback
            return [""] * len(chunks)

    def generate_video_summary(
        self,
        paragraph_summaries: List[str],
        video_title: str = ""
    ) -> str:
        """
        Generate video-level summary from paragraph summaries

        Args:
            paragraph_summaries: List of paragraph summaries
            video_title: Optional video title

        Returns:
            Video-level summary (3-5 sentences)
        """
        # Filter out empty summaries
        valid_summaries = [s for s in paragraph_summaries if s.strip()]

        if not valid_summaries:
            return ""

        # Combine summaries
        summaries_text = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(valid_summaries))

        title_context = f"视频标题：{video_title}\n\n" if video_title else ""

        prompt = f"""{title_context}以下是视频各个片段的摘要：

{summaries_text}

请基于这些片段摘要，生成一个完整的视频总结（3-5句话），概括视频的主要内容和核心信息。

视频总结："""

        messages = [
            {
                "role": "system",
                "content": "你是一个专业的视频内容总结助手。请生成简洁、全面的视频总结。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            summary = self._call_llm(messages, temperature=0.3, max_tokens=500)
            logger.info("Generated video-level summary")
            return summary

        except Exception as e:
            logger.error(f"Failed to generate video summary: {e}")
            return ""


def generate_summaries(
    chunks: List[SubtitleChunk],
    llm_api_url: str,
    llm_api_key: str,
    llm_model: str = "deepseek-ai/DeepSeek-V3",
    video_title: str = ""
) -> Tuple[List[str], str]:
    """
    Generate paragraph and video summaries

    Args:
        chunks: List of subtitle chunks
        llm_api_url: LLM API base URL
        llm_api_key: LLM API key
        llm_model: LLM model name
        video_title: Optional video title

    Returns:
        Tuple of (paragraph_summaries, video_summary)
    """
    generator = SummaryGenerator(
        api_url=llm_api_url,
        api_key=llm_api_key,
        model=llm_model
    )

    # Generate paragraph summaries
    paragraph_summaries = generator.generate_paragraph_summaries(chunks)

    # Generate video summary
    video_summary = generator.generate_video_summary(
        paragraph_summaries,
        video_title=video_title
    )

    return paragraph_summaries, video_summary
