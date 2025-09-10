import pytest
from unittest.mock import Mock

from app.core.config import settings
from app.services.theta_client import ThetaClient


@pytest.mark.asyncio
async def test_llama_live_figure_ai_guarded():
    """
    Guarded live test for the Llama (OpenAI-compatible) endpoint using figure.ai context.
    Skips automatically if LLAMA endpoint/model are not configured.
    """
    if not settings.LLAMA_ENDPOINT or not settings.LLAMA_MODEL:
        pytest.skip("LLAMA endpoint/model not configured; skipping live test.")

    # Create a minimal mock DB session; caching is disabled in client
    mock_db = Mock()

    client = ThetaClient(mock_db)

    prompt = (
        "Return ONLY a JSON object with keys products, company, source for the domain figure.ai. "
        "No markdown, no commentary."
    )

    result = await client.complete(
        prompt=prompt,
        schema_version=settings.SCHEMA_VERSION,
        page_type="test",
        competitor="Figure",
        session_id=None,
        use_cache=False
    )

    assert isinstance(result, dict)
    # Be lenient on exact fields to avoid brittleness across models
    assert "source" in result or "products" in result or "company" in result


