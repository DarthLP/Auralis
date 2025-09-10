import os
import asyncio
from datetime import datetime

from sqlalchemy.orm import Session
import sys
import types

from app.models.crawl import CrawledPage
import app.api.crawl as crawl_api


class DummyThetaClient:
    def __init__(self, db: Session):
        self.db = db


class DummyAIScoringService:
    def __init__(self, theta_client: DummyThetaClient):
        self.theta_client = theta_client

    async def score_page(self, url: str, title: str, content: str = "", h1_headings: str = "", competitor: str = "unknown", session_id: str | None = None):
        # Minimal duck-typed result object with the attributes used in the endpoint
        class R:
            success = True
            score = 0.9
            primary_category = "news"
            secondary_categories = ["release"]
            confidence = 0.8
            reasoning = "Dummy success"
            signals = ["ai_high_value"]
        return R()


class FakeQuery:
    def __init__(self, data):
        self._data = data

    def filter(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def first(self):
        return self._data[0] if self._data else None


class FakeDB:
    def __init__(self, pages):
        self.pages = pages
        self._committed = False
        self._rolled_back = False

    def query(self, model):
        assert model == CrawledPage
        return FakeQuery(self.pages)

    def commit(self):
        self._committed = True

    def rollback(self):
        self._rolled_back = True


async def main():
    # Prepare a fake DB with one crawled page
    page = CrawledPage(
        session_id=1,
        url="https://example.com/news/launch",
        canonical_url="https://example.com/news/launch",
        content_hash=None,
        status_code=200,
        depth=0,
        size_bytes=1234,
        mime_type="text/html",
        crawled_at=datetime.utcnow(),
        primary_category="news",
        secondary_categories=[],
        score=0.45,
        signals=["news_url"],
    )
    db = FakeDB([page])

    # Monkeypatch internal imports used by the endpoint by injecting dummy modules
    dummy_ai_module = types.ModuleType("app.services.ai_scoring")
    setattr(dummy_ai_module, "AIScoringService", DummyAIScoringService)
    sys.modules["app.services.ai_scoring"] = dummy_ai_module

    dummy_theta_module = types.ModuleType("app.services.theta_client")
    setattr(dummy_theta_module, "ThetaClient", DummyThetaClient)
    sys.modules["app.services.theta_client"] = dummy_theta_module

    # Build request payload with minimal page info expected by endpoint
    pages_payload = [
        {
            "url": "https://example.com/news/launch",
            "has_minimal_content": True,
            "title": "Launch",
            "h1": "Launch",
        }
    ]

    req = crawl_api.ScorePagesRequest(pages=pages_payload, competitor="Example")

    # Call the endpoint function directly
    result = await crawl_api.score_pages_with_ai(req, db)

    updated = db.pages[0]
    print({
        "endpoint_result": result,
        "db_score_before": 0.45,
        "db_score_after": float(updated.score),
        "primary_category_after": updated.primary_category,
        "signals_after": updated.signals,
        "committed": db._committed,
        "rolled_back": db._rolled_back,
    })

    assert updated.score == 0.9
    assert result["db_updated_pages"] == 1
    assert db._committed is True


if __name__ == "__main__":
    asyncio.run(main())


