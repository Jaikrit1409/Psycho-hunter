from unittest.mock import patch

import pytest

from app.services.embeddings import create_embedding


def test_create_embedding_rejects_empty_text():
    with pytest.raises(ValueError, match="Text must not be empty"):
        create_embedding("")


def test_create_embedding_requires_api_key():
    with patch(
        "app.services.embeddings.settings.OPENAI_API_KEY",
        "",
    ):
        with pytest.raises(
            RuntimeError,
            match="OPENAI_API_KEY is not configured",
        ):
            create_embedding("Hello world")


def test_create_embedding_returns_vector():
    fake_embedding = [0.1, 0.2, 0.3]

    class FakeEmbeddings:
        def create(self, *, model, input):
            assert model == "text-embedding-3-small"
            assert input == "Hello world"

            return type(
                "Response",
                (),
                {
                    "data": [
                        type(
                            "Embedding",
                            (),
                            {"embedding": fake_embedding},
                        )()
                    ]
                },
            )()

    class FakeClient:
        def __init__(self, api_key):
            assert api_key == "test-key"
            self.embeddings = FakeEmbeddings()

    with patch(
        "app.services.embeddings.settings.OPENAI_API_KEY",
        "test-key",
    ):
        with patch(
            "app.services.embeddings.OpenAI",
            FakeClient,
        ):
            result = create_embedding("Hello world")

    assert result == fake_embedding