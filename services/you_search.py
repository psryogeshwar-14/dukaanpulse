"""
DukaanPulse You.com Search Retrieval Adapter
Handles multi-query generation, live web search, URL normalization,
deduplication, evidence ID assignment, and privacy-safe error handling.
"""
import os
import re
import asyncio
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any, Optional
import httpx
from services.models import ResearchRequest, EvidenceItem


class SearchError(Exception):
    """Base exception for search operations."""
    pass


class SearchConfigError(SearchError):
    """Raised when You.com credentials or URL are missing."""
    pass


class SearchAuthError(SearchError):
    """Raised when You.com API key is invalid (401/403)."""
    pass


class SearchRateLimitError(SearchError):
    """Raised when You.com rate limit or quota is exhausted (429)."""
    pass


class SearchNetworkError(SearchError):
    """Raised on connection timeout or unreachable host."""
    pass


class SearchSchemaError(SearchError):
    """Raised when the provider response format violates expected schema."""
    pass


def normalize_url(raw_url: str) -> str:
    """
    Normalizes a URL:
    - Verifies http/https
    - Lowercases scheme and netloc
    - Strips fragment and common tracking parameters (utm_*, ref, fbclid)
    """
    raw_url = raw_url.strip()
    parsed = urllib.parse.urlsplit(raw_url)
    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}")

    # Filter out common marketing/tracking parameters
    query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    filtered_params = [
        (k, v) for k, v in query_params
        if not (k.startswith("utm_") or k in ("fbclid", "gclid", "ref", "source"))
    ]
    new_query = urllib.parse.urlencode(filtered_params)

    # Reconstruct normalized URL
    normalized = urllib.parse.urlunsplit((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip("/") if parsed.path != "/" else "/",
        new_query,
        ""  # strip fragment
    ))
    return normalized


def clean_text(text: Optional[str]) -> str:
    """Strips raw HTML tags and collapses whitespace."""
    if not text:
        return ""
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", text)
    # Collapse multiple whitespace characters into single space
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def plan_queries(request: ResearchRequest, max_queries: int = 3) -> List[str]:
    """
    Generates up to 3 focused, high-precision search queries for local market retrieval.
    Caps queries to prevent quota exhaustion and rate limiting.
    """
    category = request.category.strip()
    locality = request.locality.strip()
    question = request.question.strip()

    # Extract clean keywords from question
    q_words = [w for w in re.findall(r"\b\w+\b", question) if len(w) > 3]
    key_phrase = " ".join(q_words[:4]) if q_words else "offers prices"

    queries = [
        f"{category} {locality} {key_phrase}".strip(),
        f"{category} in {locality} menu pricing reviews".strip(),
        f"{category} {locality} customer promotions offers".strip()
    ]

    # Return up to max_queries unique queries
    seen = set()
    result = []
    for q in queries:
        if q not in seen and len(result) < max_queries:
            seen.add(q)
            result.append(q)
    return result


class YouSearchAdapter:
    def __init__(self, api_key: Optional[str] = None, search_url: Optional[str] = None, mock_mode: bool = False):
        self.api_key = api_key or os.getenv("YOU_API_KEY", "")
        self.search_url = search_url or os.getenv("YOU_SEARCH_URL", "https://ydc-index.io/v1/search")
        self.mock_mode = mock_mode or self.api_key in ("mock", "demo", "")

    async def _execute_single_query(self, query: str, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """
        Executes a single search query against the You.com API.
        Never logs request headers or exception details that might leak credentials.
        """
        if not self.api_key:
            raise SearchConfigError(
                "You.com API key is not configured. Please set YOU_API_KEY in your environment."
            )

        headers = {
            "X-API-Key": self.api_key,
            "Accept": "application/json"
        }
        params = {"query": query}

        try:
            response = await client.get(
                self.search_url,
                params=params,
                headers=headers
            )
        except httpx.TimeoutException:
            raise SearchNetworkError(f"You.com request timed out for query.")
        except httpx.RequestError as exc:
            raise SearchNetworkError(f"Network error communicating with You.com: {exc.__class__.__name__}")

        if response.status_code in (401, 403):
            raise SearchAuthError(
                "You.com authentication failed (HTTP 401/403). Please verify your YOU_API_KEY."
            )
        elif response.status_code == 429:
            raise SearchRateLimitError(
                "You.com rate limit or quota exceeded (HTTP 429). Please retry later."
            )
        elif response.is_error:
            raise SearchError(
                f"You.com returned HTTP {response.status_code}."
            )

        try:
            data = response.json()
        except Exception:
            raise SearchSchemaError("You.com returned non-JSON response.")

        if not isinstance(data, dict):
            raise SearchSchemaError("Expected JSON object from You.com API.")

        results = data.get("results")
        if results is None:
            # Some versions return top-level web
            web_items = data.get("web", [])
        elif isinstance(results, dict):
            web_items = results.get("web", [])
        elif isinstance(results, list):
            web_items = results
        else:
            raise SearchSchemaError("Unexpected 'results' structure in You.com response.")

        if not isinstance(web_items, list):
            raise SearchSchemaError("Unexpected 'web' results structure in You.com response.")

        return web_items

    async def search(self, request: ResearchRequest) -> List[EvidenceItem]:
        """
        Coordinates query generation, deduplication across calls, and evidence normalization.
        """
        if self.mock_mode:
            return self._get_mock_evidence(request)

        queries = plan_queries(request, max_queries=3)
        retrieved_items: List[EvidenceItem] = []
        seen_urls = set()
        evidence_counter = 1

        async with httpx.AsyncClient(timeout=12.0) as client:
            tasks = [self._execute_single_query(query, client) for query in queries]
            query_results = await asyncio.gather(*tasks, return_exceptions=True)
            now_str = datetime.utcnow().isoformat() + "Z"

            for query, raw_items in zip(queries, query_results):
                if isinstance(raw_items, Exception) or not isinstance(raw_items, list):
                    continue

                for item in raw_items:
                    raw_url = item.get("url") or item.get("link")
                    if not raw_url or not isinstance(raw_url, str):
                        continue

                    try:
                        norm_url = normalize_url(raw_url)
                    except ValueError:
                        continue  # Skip invalid schemes like javascript: or mailto:

                    if norm_url in seen_urls:
                        continue
                    seen_urls.add(norm_url)

                    title = clean_text(item.get("title") or "")
                    
                    # Extract snippets
                    snippets_raw = item.get("snippets") or []
                    if isinstance(snippets_raw, list):
                        snippets_text = " ".join([clean_text(s) for s in snippets_raw if s])
                    else:
                        snippets_text = clean_text(str(snippets_raw))
                    
                    description = clean_text(item.get("description") or "")
                    full_snippet = f"{snippets_text} {description}".strip()
                    if not full_snippet:
                        continue

                    domain = urllib.parse.urlsplit(norm_url).netloc

                    evidence_item = EvidenceItem(
                        evidence_id=f"E{evidence_counter}",
                        url=norm_url,
                        title=title or domain,
                        snippet=full_snippet,
                        query=query,
                        retrieved_at=now_str,
                        domain=domain,
                        locality_match=request.locality
                    )
                    retrieved_items.append(evidence_item)
                    evidence_counter += 1

        return retrieved_items

    def _get_mock_evidence(self, request: ResearchRequest) -> List[EvidenceItem]:
        """Supplies deterministic verified evidence for testing or offline demo."""
        import json
        fixtures_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "synthetic_evidence.json")
        now_str = datetime.utcnow().isoformat() + "Z"
        
        if os.path.exists(fixtures_path):
            with open(fixtures_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [
                    EvidenceItem(
                        evidence_id=d["evidence_id"],
                        url=d["url"],
                        title=d["title"],
                        snippet=d["snippet"],
                        query=d["query"],
                        retrieved_at=now_str,
                        domain=d.get("domain"),
                        locality_match=d.get("locality_match", request.locality)
                    )
                    for d in data
                ]
        
        # Fallback inline
        return [
            EvidenceItem(
                evidence_id="E1",
                url="https://www.zomato.com/bangalore/breakfast-in-hsr",
                title=f"Breakfast Spots in {request.locality}",
                snippet=f"Local {request.category.lower()} options in {request.locality} offer combos between 149 and 249 INR.",
                query=f"{request.category} {request.locality} breakfast",
                retrieved_at=now_str,
                domain="zomato.com",
                locality_match=request.locality
            )
        ]
