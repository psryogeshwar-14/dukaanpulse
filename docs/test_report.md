# DukaanPulse Comprehensive Verification & Test Report
**Execution Environment:** macOS Darwin, Python 3.9.6, Pytest 8.4.2  
**Date:** November 21, 2026  
**Overall Status:** 33/33 PASSED (100% Automated Tests Passing)

---

## 1. Automated Test Suite (PASSED)

| File | Test Function | Verified Behavior | Status |
|---|---|---|---|
| `test_search_adapter.py` | `test_normalize_url` | Strips tracking tags (`utm_*`, `fbclid`), validates HTTP/HTTPS | **PASSED** |
| `test_search_adapter.py` | `test_clean_text` | Strips HTML tags, collapses whitespace | **PASSED** |
| `test_search_adapter.py` | `test_plan_queries_cap_and_content` | Caps search queries at 3, extracts targeted keywords | **PASSED** |
| `test_search_adapter.py` | `test_search_mock_mode` | Deterministic fixture loading with `E1`, `E2`, `E3` structure | **PASSED** |
| `test_search_adapter.py` | `test_search_missing_key_error` | Missing You.com key raises `SearchConfigError` | **PASSED** |
| `test_search_adapter.py` | `test_search_auth_error_handling` | HTTP 401/403 raises `SearchAuthError` without key leakage | **PASSED** |
| `test_search_adapter.py` | `test_search_rate_limit_handling` | HTTP 429 quota exhaustion raises `SearchRateLimitError` | **PASSED** |
| `test_search_adapter.py` | `test_search_unexpected_schema_handling` | Malformed response structure raises `SearchSchemaError` | **PASSED** |
| `test_search_adapter.py` | `test_search_empty_results` | Handles empty results array cleanly | **PASSED** |
| `test_search_adapter.py` | `test_search_timeout_handling` | Request timeout (>25s) raises `SearchNetworkError` | **PASSED** |
| `test_search_adapter.py` | `test_search_deduplicates_duplicate_urls` | Identical URLs across multiple queries deduplicated | **PASSED** |
| `test_validators.py` | `test_valid_report` | Strictly validates JSON schema, citations, and budget | **PASSED** |
| `test_validators.py` | `test_invented_evidence_id` | Rejects unretrieved IDs (e.g. `E99`) with specific error | **PASSED** |
| `test_validators.py` | `test_quote_not_in_snippet` | Rejects fabricated quotes absent from excerpt | **PASSED** |
| `test_validators.py` | `test_budget_ceiling_violation` | Rejects experiments exceeding merchant input budget | **PASSED** |
| `test_validators.py` | `test_insufficient_evidence_status` | Enforces null experiment on `insufficient_evidence` | **PASSED** |
| `test_validators.py` | `test_extract_json_block` | Robustly parses fenced/unfenced JSON with commentary | **PASSED** |
| `test_validators.py` | `test_prompt_injection_in_source` | Untrusted source instructions strictly treated as data | **PASSED** |
| `test_validators.py` | `test_unsupported_citation_mapping` | Rejects valid quote paired with incorrect source ID | **PASSED** |
| `test_economics.py` | `test_positive_contribution` | Calculates ₹114 contribution, 63.7% margin, 4 break-even orders | **PASSED** |
| `test_economics.py` | `test_zero_setup_cost` | Handles ₹0 setup cost with 0 break-even orders | **PASSED** |
| `test_economics.py` | `test_zero_contribution_no_division_by_zero` | Zero contribution: prevents division by zero, flags unviable | **PASSED** |
| `test_economics.py` | `test_negative_contribution` | Negative contribution: prevents negative division, advises DO NOT LAUNCH | **PASSED** |
| `test_economics.py` | `test_over_budget_pilot` | Flags pilot exceeding budget ceiling | **PASSED** |
| `test_economics.py` | `test_invalid_negative_or_zero_price` | Rejects negative/zero prices via Pydantic validator | **PASSED** |
| `test_economics.py` | `test_stale_advice_detection` | Detects altered cost assumptions and marks advice STALE | **PASSED** |
| `test_storage.py` | `test_save_and_retrieve_research` | Saves research run & evidence ledger into SQLite | **PASSED** |
| `test_storage.py` | `test_experiment_and_outcome_tracking` | Accepts experiment, logs daily outcomes, aggregates metrics | **PASSED** |
| `test_api.py` | `test_health_endpoint` | `GET /api/health` configuration and database status | **PASSED** |
| `test_api.py` | `test_research_flow_and_validation` | `POST /api/research` end-to-end flow & 422 error checks | **PASSED** |
| `test_api.py` | `test_root_serves_index_html` | `GET /` serves Single Page Application | **PASSED** |
| `test_api.py` | `test_economics_calculation_endpoint` | `POST /api/economics/calculate` deterministic calculations | **PASSED** |
| `test_api.py` | `test_stale_economics_check_endpoint` | `POST /api/economics/check-stale` detects changed assumptions | **PASSED** |

---

## 2. Failed Tests (FAILED)

*None. Zero test failures.*

---

## 3. Not Run / Requires Human Credentials Verification (NOT RUN)

| Item | Reason | Action Required by Human |
|---|---|---|
| **Live Authenticated You.com Call** | Automated test suite uses offline synthetic fixtures to avoid spending paid quota or requiring checked-in secrets. | Supply `YOU_API_KEY` in `.env` and execute smoke test. |
| **Live Authenticated LLM Call** | Automated test suite uses deterministic mock synthesis to ensure reproducible regression testing. | Supply `LLM_API_KEY` in `.env` with provider (`gemini` or `openai`). |
| **Real Merchant In-Person Interviews** | Ethical AI protocol forbids synthetic interviews or fabricated merchant testimonials. | Conduct 3 human interviews using `docs/merchant_interview.md`. |
| **Public Multi-User Deployment** | Single-user local demo MVP architecture; public deployment requires auth and rate-limiting. | Plan public deployment after hackathon demo approval. |

---

## 4. Manual Browser Verification Journey (Reproducible Steps)

1. Start server: `python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000`
2. Open `http://127.0.0.1:8000` in Google Chrome or Safari.
3. Verify pre-loaded HSR Layout café values.
4. Test interactive economics card:
   - Change ingredient cost to ₹180: Observe live warning *"DO NOT LAUNCH. Every order loses money."*
   - Restore ingredient cost to ₹50: Observe green *"FINANCIALLY VIABLE"*.
5. Click **Execute Live Research**:
   - Observe live progress console steps 1 through 5.
6. In Report Screen:
   - Click evidence chip `[E1]`: Verify modal drawer opens showing source excerpt, query, retrieval timestamp, and live link.
   - Press `Escape` key: Verify modal closes cleanly.
   - Inspect Pre-Spending Validation Step and Stop Conditions.
7. Click **Approve & Accept Experiment**:
   - Verify transition to Screen 4 (Tracker).
   - Enter Day 1 test figures: 12 orders, ₹2,148 revenue, ₹720 variable costs.
   - Click **Save Daily Measurement**:
   - Verify Total Contribution displays ₹1,428.00 (66.5% Gross Margin).
8. Restart server process (`Ctrl+C` then re-run uvicorn):
   - Refresh browser: Verify SQLite persisted all research and experiment outcomes.
