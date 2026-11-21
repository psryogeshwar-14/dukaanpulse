# DukaanPulse: Live, Cited, Margin-Aware Research-to-Action Assistant for Small Independent Cafés
**Track:** You.com Live, Cited Web-Data Track | Beyond 9TO5 Buildathon

DukaanPulse helps a small café investigate an offer, check its own unit economics, and run one bounded, measurable experiment—with live sources and visible uncertainty.

---

## 1. Product Overview & The Café Problem

Small independent café owners make pricing and promotional decisions with incomplete local-market intelligence and unforgiving cost structures. Generic AI chatbots hallucinate competitor prices and promise fake "40% revenue increases"—which can quickly bankrupt a small merchant if variable costs exceed selling price.

**DukaanPulse** bridges this gap:
1. Researches local competitor offerings and terms through **You.com's live web index**.
2. Displays an inspectable **evidence ledger** with exact quoted excerpts and timestamps.
3. Evaluates the owner's entered cost assumptions using **pure deterministic Python math**.
4. Automatically detects and flags **stale recommendations** if underlying cost assumptions change.
5. Proposes an owner-approved, bounded experiment strictly under the merchant's financial ceiling.
6. Tracks daily experimental orders, revenue, and costs in **SQLite**, calculating true **Contribution Margin** ($\text{Revenue} - \text{Variable Cost}$).

---

## 2. Technical Architecture & Component Breakdown

```
[Merchant UI] (index.html: Vanilla JS, Zero-XSS, Responsive)
       │
       ├── POST /api/economics/calculate   (Real-time deterministic calculations)
       ├── POST /api/economics/check-stale (Stale-state invalidator)
       │
       ▼ POST /api/research
[FastAPI Backend] (app.py)
       ├── [YouSearchAdapter] (services/you_search.py)
       │       └── GET https://ydc-index.io/v1/search (Caps: 3 queries, URL normalization, deduplication)
       ├── [Deterministic Economics Engine] (services/economics.py)
       │       └── Pure Python: Variable costs, Contribution, Break-even orders, Budget compliance
       ├── [Grounded Synthesis Adapter] (services/synthesis.py)
       │       └── Multi-provider (Gemini/OpenAI/mock) + Strict untrusted data isolation + 1-shot repair
       ├── [Grounding & Citation Validator] (services/validators.py)
       │       └── Verbatim quote-in-snippet verification + Budget ceiling enforcement
       └── [SQLite Storage Layer] (services/storage.py)
               └── ACID persistence for research runs, evidence ledger, approved assumptions, outcomes
```

### Which Verified You.com API is Called?
- **Endpoint:** `GET https://ydc-index.io/v1/search`
- **Headers:** `X-API-Key: os.environ['YOU_API_KEY']`, `Accept: application/json`
- **Parameters:** `query: str`
- **Where Retrieval Happens:** `services/you_search.py` -> `YouSearchAdapter._execute_single_query`
- **Retrieval Guardrails:** Maximum 3 queries per research run, URL normalization (strips `utm_*`, `fbclid`), deduplication across calls, and a 25-second timeout.

### How Citations are Validated
- Located in `services/validators.py` -> `validate_report`.
- For every observation claim, the model must provide an `evidence_id` (e.g. `E1`) and a `quote`.
- The server verifies:
  1. The `evidence_id` exists in the current research run (invented IDs like `E99` are rejected).
  2. The `quote` exists verbatim in the retrieved excerpt (allowing only documented whitespace normalization).
  3. If invalid, the system executes **at most one automated repair cycle**; if it still fails, it returns an explicit error rather than fabricating a fake AI report.

### Which Calculations are Purely Deterministic?
- Located in `services/economics.py` -> `calculate_economics`:
  - $\text{Variable Cost per Order} = \text{Ingredient Cost} + \text{Packaging Cost} + \text{Other Variable Cost}$
  - $\text{Contribution per Order} = \text{Selling Price} - \text{Variable Cost per Order}$
  - $\text{Gross Margin \%} = \frac{\text{Contribution per Order}}{\text{Selling Price}} \times 100\%$
  - $\text{Orders to Break Even on Setup} = \lceil \frac{\text{One-Time Pilot Cost}}{\text{Contribution per Order}} \rceil$ (strictly prevented if contribution $\le 0$)
  - $\text{Estimated Pilot Spend} = \text{One-Time Cost} + (\text{Planned Quantity} \times \text{Variable Cost per Order})$
- All outcome calculations in `services/storage.py`:
  - $\text{Recorded Contribution} = \text{Recorded Revenue} - \text{Recorded Variable Cost}$

---

## 3. Setup and Launch Instructions

### Prerequisites
- Python 3.9+ or Python 3.10+
- Internet connection for initial package installation

### Installation on macOS / Linux:
```bash
# 1. Clone or navigate to the repository
cd dukaanpulse

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install locked dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
```

### Installation on Windows (PowerShell):
```powershell
# 1. Navigate to directory
cd dukaanpulse

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install locked dependencies
python -m pip install -r requirements.txt

# 4. Configure environment variables
copy .env.example .env
```

### Step 5: Configure Credentials in `.env`
Edit `.env` with your actual provider keys:
```env
# You.com Search API Credentials
YOU_API_KEY=your_actual_you_com_key
YOU_SEARCH_URL=https://ydc-index.io/v1/search

# AI Model Credentials (gemini, openai, or mock)
LLM_PROVIDER=gemini
LLM_API_KEY=your_model_key
LLM_MODEL=gemini-1.5-flash

# Database & Host
HOST=127.0.0.1
PORT=8000
DATABASE_PATH=dukaanpulse.db
```
*(Note: If `YOU_API_KEY` or `LLM_PROVIDER` is set to `mock` or left blank during local development, DukaanPulse runs in deterministic offline test mode using verified fixtures).*

### Step 6: Run the Full Test Suite
```bash
python -m pytest -v
```
*(All 33 automated tests will execute and pass in <0.3s)*

### Step 7: Launch the Server
```bash
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```
Open **`http://127.0.0.1:8000`** in your browser.

---

## 4. Benchmark Café Demonstration (3 Minutes)

1. Open `http://127.0.0.1:8000`. The primary demo values are pre-loaded:
   - **Category**: Cafe
   - **Locality**: HSR Layout, Bengaluru
   - **Question**: Should I test a weekday breakfast bundle within a budget of INR 2,000, using existing equipment?
   - **Cost Assumptions**: Selling price ₹179, Ingredient cost ₹50, Packaging ₹10, Other ₹5, Setup ₹450, Planned quantity 20.
2. Observe the **Live Economics Card**:
   - Variable Cost: ₹65.00
   - Contribution: ₹114.00 (63.7% Margin)
   - Break-Even: 4 orders
3. Click **Execute Live Research**:
   - The live progress console shows real status across planned You.com queries.
4. In Screen 3 (Report):
   - Click evidence chip `[E1]` to inspect the exact You.com snippet and source URL.
   - Note the **Material Unknowns** acknowledging what public web data cannot prove.
   - Review the proposed experiment and pre-spending validation step.
5. Demonstrate Stale Advice Protection:
   - In your thought or tests, if ingredient costs spike to ₹180, DukaanPulse flags the offer with `"DO NOT LAUNCH"` and prevents unviable approvals.
6. Click **Approve & Accept Experiment**:
   - The experiment and its approved assumptions snapshot are committed to SQLite.
7. Under Screen 4 (Tracker):
   - Record test measurements: 12 orders, ₹2,148 revenue, ₹720 variable costs.
   - Verify Total Contribution calculates strictly as ₹1,428.00.

---

## 5. Known Limitations & Honest Disclosures

- **Public Data vs. Private Reality**: Public web data cannot reveal an individual café's negotiated distributor discounts or internal kitchen spoilage rates.
- **Contribution Margin vs. Net Profit**: Contribution margin ($\text{Revenue} - \text{Variable Cost}$) deliberately excludes fixed overheads (shop rent, salaried staff, electricity).
- **Single-User MVP**: Built as a secure, local single-merchant MVP; multi-user public deployment requires authentication, tenant data isolation, and rate-limiting middleware.
- **Zero Fabricated Interviews**: Merchant interviews must be conducted by humans using the template in `docs/merchant_interview.md`.
