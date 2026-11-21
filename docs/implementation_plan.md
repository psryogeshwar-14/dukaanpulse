# DukaanPulse Implementation Plan & Stage Checklist
**Track:** You.com Live, Cited Web-Data Track (Beyond 9TO5 Buildathon)  
**Version:** 3.0.0-FINAL  
**Date:** November 21, 2026  
**Status:** ALL STAGES COMPLETED & VERIFIED (33/33 Tests Passing)

---

## 9-Stage Execution Checklist

- [x] **Stage 1: Understand the Product and Audit the Workspace**
  - [x] Inspect existing codebase, dependencies, tests, and configuration.
  - [x] Preserve working code without rewriting stack.
  - [x] Initial audit saved in `docs/status_audit.md`.

- [x] **Stage 2: Lock the MVP Scope and Architecture**
  - [x] Primary demo: Café in HSR Layout, Bengaluru (Weekday breakfast bundle, INR 2,000 budget, existing equipment).
  - [x] Tech stack: FastAPI + plain HTML/CSS/JS + SQLite + Pydantic + httpx + pytest.
  - [x] Complete user journey: Merchant input → Live You.com research → Evidence ledger → Grounded findings → Merchant cost inputs → Economics calculation → Experiment proposal → Owner approval → Outcome tracking.
  - [x] Explicitly excluded: payments, POS, auto-purchasing, customer messaging, scraping profiles, speculative uplift forecasting.

- [x] **Stage 3: Implement Real You.com Retrieval**
  - [x] You.com search adapter (`services/you_search.py`) calling `GET https://ydc-index.io/v1/search` with `X-API-Key`.
  - [x] Query planner capped at max 3 focused queries.
  - [x] URL normalization (stripping `utm_*`, `fbclid`), deduplication across calls, and evidence ID assignment (`E1`, `E2`, ...).
  - [x] Strict error handling: 401/403 auth errors, 429 quota exhaustion, timeout (25s), and schema errors.
  - [x] Redacted response fixture (`fixtures/search_response_redacted.json`) and synthetic evidence (`fixtures/synthetic_evidence.json`).
  - [x] Tested and verified via unit tests.

- [x] **Stage 4: Build Grounded AI Synthesis and Citations**
  - [x] Grounded prompt with untrusted web data isolation and strict JSON schema (`services/synthesis.py`).
  - [x] Server-side quote-in-excerpt verification and budget ceiling enforcement (`services/validators.py`).
  - [x] One-shot repair cycle upon validation failure; clear error on repair exhaustion.
  - [x] Status support for `ready`, `insufficient_evidence`, and `needs_owner_input`.
  - [x] Multi-provider support (Gemini, OpenAI, Groq, deterministic test fixture).

- [x] **Stage 5: Add Merchant Economics and Experiment Design**
  - [x] Pure deterministic Python formulas in `services/economics.py`:
    - `variable_cost_per_order = ingredient_cost + packaging_cost + other_variable_cost`
    - `contribution_per_order = selling_price - variable_cost_per_order`
    - `orders_to_cover_setup_cost = ceil(one_time_pilot_cost / contribution_per_order)` (division by zero strictly prevented if contribution <= 0)
    - Budget check: `one_time_pilot_cost + planned_quantity * variable_cost_per_order <= max_pilot_budget`
    - Rejection of negative and non-finite inputs.
    - Stale recommendation invalidation via `check_stale_advice`.
  - [x] Pre-spending validation step, duration days, and explicit stop/revise conditions.

- [x] **Stage 6: Build the Evidence-First Interface and Persistence**
  - [x] Screen 1: Café profile setup, 3 one-click showcase scenario presets, and live interactive unit economics card.
  - [x] Screen 2: Real-time research progress console with elapsed timer and transparent step tracking.
  - [x] Screen 3: Verified report with clickable evidence chips, interactive modal drawer, live cost sensitivity/stale simulator, and printable Staff SOP Card.
  - [x] Screen 4: Experiment tracker with approved assumptions snapshot, daily measurement entry form, and cumulative contribution margin KPI ledger.
  - [x] SQLite thread-safe persistence in `services/storage.py` with ACID transactions and restart persistence.
  - [x] XSS immunity: zero unsafe `innerHTML`, strict textContent and DOM node creation.

- [x] **Stage 7: Test the Application Honestly**
  - [x] 33 automated tests passing in 0.29s (`tests/test_search_adapter.py`, `tests/test_validators.py`, `tests/test_economics.py`, `tests/test_storage.py`, `tests/test_api.py`).
  - [x] End-to-end integration smoke test script (`smoke_test.py`) passing 100%.
  - [x] Updated `docs/test_report.md` separating Passed, Failed, and Not Run / Human items.

- [x] **Stage 8: Prepare the Demo and Merchant Validation**
  - [x] Author 3-minute hackathon pitch script in `docs/demo_script.md` following the 11-step sequence.
  - [x] Author ethical merchant interview questionnaire in `docs/merchant_interview.md`.

- [x] **Stage 9: Handover and Final Completion Gate**
  - [x] Cross-platform 1-click startup scripts (`start.sh` for macOS/Linux, `start.bat` for Windows).
  - [x] Updated comprehensive `README.md` with complete documentation, architecture diagrams, and honest disclosures.
  - [x] 12-point final status table completed with honest disclosures.
