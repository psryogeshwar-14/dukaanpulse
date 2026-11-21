# DukaanPulse Initial Workspace & Component Audit
**Date:** November 21, 2026  
**Auditor:** Lead Full-Stack & AI Engineer (Antigravity)  
**Track:** You.com Live, Cited Web-Data Track | Beyond 9TO5 Buildathon

---

## 1. Executive Status Table

| Component | Status | Details & Current State |
|---|---|---|
| **FastAPI Backend (`app.py`)** | **Partially Implemented** | Health check, research pipeline, experiment lifecycle, and outcome routes exist. Needs dedicated unit economics endpoints and stale-state invalidator. |
| **Domain Models (`services/models.py`)** | **Partially Implemented** | Research request, evidence items, observations, and outcome records defined. Needs merchant cost input schemas and economics result models. |
| **Merchant Economics Engine (`services/economics.py`)** | **Missing** | Deterministic Python calculation of variable cost per order, contribution per order, break-even order count, and budget checks not yet implemented. |
| **You.com Search Adapter (`services/you_search.py`)** | **Implemented (Live Not Verified)** | 3-query planner, deduplication, URL normalization, evidence ID assignment, and error handling complete. Live authenticated call pending `YOU_API_KEY`. |
| **AI Synthesis Adapter (`services/synthesis.py`)** | **Implemented (Live Not Verified)** | Multi-provider architecture (Gemini, OpenAI, Groq, mock) with 1-shot repair and prompt injection defense. Live call pending `LLM_API_KEY`. |
| **Citation & Grounding Validator (`services/validators.py`)** | **Implemented** | Strict quote-in-excerpt verification, evidence ID existence check, and budget ceiling enforcement pass all unit tests. |
| **SQLite Storage & Persistence (`services/storage.py`)** | **Partially Implemented** | ACID tables for research runs, evidence ledger, experiments, and outcomes. Needs persistence of owner cost assumptions snapshot. |
| **Evidence-First Frontend (`index.html`)** | **Partially Implemented** | Responsive SPA with Setup, Progress, Report, and Outcome Tracker screens. Needs interactive Merchant Cost & Economics Calculator card and stale-state UI banners. |
| **Automated Test Suite (`tests/`)** | **Partially Implemented** | 20 unit/integration tests passing (retrieval, validators, storage, API). Needs comprehensive economics and assumption invalidation tests. |
| **Fixtures (`fixtures/`)** | **Implemented** | Redacted You.com response and synthetic evidence fixtures clearly separated from live mode. |
| **Environment & Secrets (`.env.example`, `.env`)** | **Implemented** | `.env.example` provides placeholders only. Real secrets strictly excluded from tracking, logs, and client code. |
| **Documentation & Pitch Package (`docs/`)** | **Partially Implemented** | `implementation_plan.md`, `test_report.md`, and `demo_script.md` present. Needs `status_audit.md` and `merchant_interview.md`. |

---

## 2. Identified Deficits & Required Enhancements

1. **Merchant Unit Economics Layer**:
   - Small café owners cannot evaluate whether to launch an offer without knowing their unit economics. We must introduce `services/economics.py` with deterministic formulas for ingredient costs, packaging, one-time pilot costs, contribution margins, and break-even order counts.
2. **Assumption Stale-State Management**:
   - If an owner adjusts cost parameters (e.g., ingredient costs rise from ₹45 to ₹120), previously generated positive advice must be flagged as `stale` immediately. The app must never let positive advice remain active when its cost foundation is invalid.
3. **Owner Assumption Transparency**:
   - Every cost must be distinctly labeled as an "Owner-Entered Assumption" rather than a web-retrieved market fact.
4. **Merchant Validation Toolkit**:
   - `docs/merchant_interview.md` must be created with structured questions for human interviews to prevent ungrounded claims.
