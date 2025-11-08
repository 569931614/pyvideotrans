"""
Embedding Generation Module using OpenAI-compatible API

Generates vector embeddings for subtitle chunks using OpenAI-compatible
embedding APIs (e.g., OpenAI, SiliconFlow).
"""

import logging
import time
from typing import List
import requests

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates embeddings using OpenAI-compatible embedding API"""

    def __init__(
        self,
        api_url: str,
        api_key: str,
        model: str = "text-embedding-3-small",
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize embedding generator

        Args:
            api_url: Base URL for embedding API (e.g., https://api.siliconflow.cn/v1)
            api_key: API key
            model: Embedding model name
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay in seconds (exponential backoff)
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _call_embedding_api(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """
        Call embedding API with retry logic

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            Exception: If all retries fail
        """
        endpoint = f"{self.api_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "input": texts
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
                embeddings = [item['embedding'] for item in result['data']]

                return embeddings

            except requests.exceptions.RequestException as e:
                logger.warning(f"Embedding API call failed (attempt {attempt + 1}/{self.max_retries}): {e}")

                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    raise Exception(f"Embedding API call failed after {self.max_retries} attempts: {e}")

    def generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for texts with batching

        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process per API call

        Returns:
            List of embedding vectors
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            try:
                embeddings = self._call_embedding_api(batch)
                all_embeddings.extend(embeddings)

                logger.info(f"Generated embeddings for texts {i}-{i + len(batch)} / {len(texts)}")

            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch {i}-{i + len(batch)}: {e}")
                raise

        return all_embeddings


def generate_embeddings(
    texts: List[str],
    embedding_api_url: str,
    embedding_api_key: str,
    embedding_model: str = "text-embedding-3-small",
    batch_size: int = 100
) -> List[List[float]]:
    """
    Generate embeddings for texts

    Args:
        texts: List of texts to embed
        embedding_api_url: Embedding API base URL
        embedding_api_key: Embedding API key
        embedding_model: Embedding model name
        batch_size: Batch size for API calls

    Returns:
        List of embedding vectors
    """
    generator = EmbeddingGenerator(
        api_url=embedding_api_url,
        api_key=embedding_api_key,
        model=embedding_model
    )

    embeddings = generator.generate_embeddings(texts, batch_size=batch_size)

    return embeddings
