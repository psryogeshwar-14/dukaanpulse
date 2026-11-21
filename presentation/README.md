# DukaanPulse Presentation — README

## Files in This Folder

| File | Purpose |
|---|---|
| `index.html` | Browser-based slide deck (primary, recommended) |
| `build_pptx.py` | Script to generate an editable `.pptx` file |
| `dukaanpulse.pptx` | Editable PowerPoint (run build script to generate) |
| `speaker-notes.md` | Full speaker notes for all 6 slides |
| `judge-qa.md` | Likely judge questions with honest, prepared answers |
| `README.md` | This file |

---

## How to Present

### Option 1 — Browser (Recommended)
1. Open `index.html` in Chrome, Safari, or Firefox.
2. Use **← →** arrow keys to navigate slides.
3. Press **F** to toggle fullscreen.
4. Number keys **1–6** jump directly to any slide.
5. Swipe left/right on touch screens.
6. The slide counter (bottom center) shows your position.

### Option 2 — PowerPoint / Keynote
1. Run the PPTX build script (see below).
2. Open `dukaanpulse.pptx` in PowerPoint or Keynote.
3. Add slide transition animations manually (Fade recommended).
4. Present with Presenter View to see speaker notes.

### Option 3 — PDF
1. Open `index.html` in Chrome.
2. File → Print → Save as PDF.
3. Set layout to Landscape, disable headers/footers.

---

## Generating the PPTX

```bash
cd /path/to/paytm1

# Install python-pptx (requires network access)
pip install python-pptx

# Build the deck
python presentation/build_pptx.py
# Output: presentation/dukaanpulse.pptx
```

---

## Presentation Structure

| # | Title | Theme |
|---|---|---|
| 1 | Know what to test before you spend | Dark navy opening |
| 2 | A good offer can still be a costly guess | Light — the problem |
| 3 | Ask. Check. Test. | Light — how it works |
| 4 | Not just advice. A decision you can inspect. | Light — differentiation |
| 5 | One question. One clear next step. | Light — demo |
| 6 | Start small. Learn before spending more. | Teal closing |

---

## Live Links

- **Working prototype:** https://dukaanpulse-eight.vercel.app/
- **Source code:** https://github.com/psryogeshwar-14/dukaanpulse

---

## Notes for the Presenter

- All inputs shown in the demo are **illustrative** — not real merchant data.
- Do not claim merchant validation has occurred; it is the stated next step.
- Do not fabricate revenue metrics, user counts, or success rates.
- If the demo fails, fall back to the slide deck and describe the workflow verbally.
- The You.com API key must be configured in the deployment for live research to work.
