"""
Unit tests for You.com Search Retrieval Adapter
"""
import pytest
import httpx
from services.models import ResearchRequest
from services.you_search import (
    normalize_url, clean_text, plan_queries, YouSearchAdapter,
    SearchConfigError, SearchAuthError, SearchRateLimitError,
    SearchNetworkError, SearchSchemaError
)


def test_normalize_url():
    raw = "https://WWW.Example.com/path/?utm_source=twitter&utm_medium=cpc&id=123#section"
    normalized = normalize_url(raw)
    assert normalized == "https://www.example.com/path?id=123"

    with pytest.raises(ValueError):
        normalize_url("javascript:alert(1)")

    with pytest.raises(ValueError):
        normalize_url("file:///etc/passwd")


def test_clean_text():
    html_sample = "<b>Special</b> offer with &nbsp;   extra   spaces<br>and details."
    cleaned = clean_text(html_sample)
    assert cleaned == "Special offer with &nbsp; extra spaces and details."
    assert clean_text("") == ""
    assert clean_text(None) == ""


def test_plan_queries_cap_and_content():
    req = ResearchRequest(
        category="Cafe",
        locality="HSR Layout, Bengaluru",
        question="Which weekday breakfast offer to test without equipment?",
        budget=2000.0,
        constraints="No new equipment"
    )
    queries = plan_queries(req, max_queries=3)
    assert len(queries) <= 3
    assert any("HSR Layout, Bengaluru" in q for q in queries)
    assert any("Cafe" in q for q in queries)


@pytest.mark.asyncio
async def test_search_mock_mode():
    req = ResearchRequest(
        category="Cafe",
        locality="HSR Layout, Bengaluru",
        question="Which weekday breakfast offer to test?",
        budget=2000.0
    )
    adapter = YouSearchAdapter(mock_mode=True)
    results = await adapter.search(req)

    assert len(results) >= 1
    assert results[0].evidence_id == "E1"
    assert results[0].url.startswith("http")
    assert len(results[0].snippet) > 10
    assert results[0].domain is not None


@pytest.mark.asyncio
async def test_search_missing_key_error():
    req = ResearchRequest(
        category="Cafe",
        locality="HSR Layout",
        question="Which offer?",
        budget=1000.0
    )
    adapter = YouSearchAdapter(api_key="", mock_mode=False)
    with pytest.raises(SearchConfigError) as exc_info:
        await adapter._execute_single_query("test query", httpx.AsyncClient())
    assert "not configured" in str(exc_info.value)


@pytest.mark.asyncio
async def test_search_auth_error_handling(monkeypatch):
    class MockResponse:
        status_code = 401
        is_error = True
        def raise_for_status(self):
            pass

    async def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = YouSearchAdapter(api_key="invalid_test_key", mock_mode=False)
    with pytest.raises(SearchAuthError) as exc_info:
        await adapter._execute_single_query("query", httpx.AsyncClient())
    assert "authentication failed" in str(exc_info.value)
    # Ensure key is not exposed in error message
    assert "invalid_test_key" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_search_rate_limit_handling(monkeypatch):
    class MockResponse:
        status_code = 429
        is_error = True

    async def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = YouSearchAdapter(api_key="valid_key", mock_mode=False)
    with pytest.raises(SearchRateLimitError):
        await adapter._execute_single_query("query", httpx.AsyncClient())


@pytest.mark.asyncio
async def test_search_unexpected_schema_handling(monkeypatch):
    class MockResponse:
        status_code = 200
        is_error = False
        def json(self):
            return {"unexpected": "payload"}

    async def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = YouSearchAdapter(api_key="valid_key", mock_mode=False)
    # web items missing or empty list
    items = await adapter._execute_single_query("query", httpx.AsyncClient())
    assert items == []


@pytest.mark.asyncio
async def test_search_empty_results(monkeypatch):
    class MockResponse:
        status_code = 200
        is_error = False
        def json(self):
            return {"results": {"web": []}}

    async def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = YouSearchAdapter(api_key="valid_key", mock_mode=False)
    items = await adapter._execute_single_query("query", httpx.AsyncClient())
    assert items == []


@pytest.mark.asyncio
async def test_search_timeout_handling(monkeypatch):
    async def mock_get(*args, **kwargs):
        raise httpx.TimeoutException("Timeout")

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = YouSearchAdapter(api_key="valid_key", mock_mode=False)
    with pytest.raises(SearchNetworkError) as exc_info:
        await adapter._execute_single_query("query", httpx.AsyncClient())
    assert "timed out" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_search_deduplicates_duplicate_urls(monkeypatch):
    class MockResponse:
        status_code = 200
        is_error = False
        def json(self):
            return {
                "results": {
                    "web": [
                        {
                            "url": "https://example.com/hsr-cafe?utm_source=ad1",
                            "title": "Cafe 1",
                            "snippets": ["Excerpt 1"]
                        },
                        {
                            "url": "https://example.com/hsr-cafe?utm_source=ad2",
                            "title": "Cafe 1 duplicate",
                            "snippets": ["Excerpt 1 duplicate"]
                        }
                    ]
                }
            }

    async def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    req = ResearchRequest(
        category="Cafe",
        locality="HSR Layout",
        question="Which breakfast combo?",
        budget=2000.0
    )
    adapter = YouSearchAdapter(api_key="valid_key", mock_mode=False)
    results = await adapter.search(req)

    # Normalized URL should result in only 1 evidence item, not 2
    urls = [r.url for r in results]
    assert len(urls) == len(set(urls))
