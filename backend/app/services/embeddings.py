from __future__ import annotations

from openai import OpenAI

from app.core.config import settings


EMBEDDING_MODEL = "text-embedding-3-small"


def create_embedding(text: str) -> list[float]:
    """
    Create an embedding vector for the supplied text.

    The OpenAI client is created only when this function is called,
    which keeps module imports safe when no API key is configured.
    """

    if not text or not text.strip():
        raise ValueError("Text must not be empty")

    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text.strip(),
    )

    return response.data[0].embedding