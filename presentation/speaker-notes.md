# DukaanPulse — Speaker Notes
*Hackathon presentation · 6 slides*

---

## Slide 1 — What Is DukaanPulse?

**Title:** Know what to test before you spend.

**Suggested script (≈ 45 seconds):**

> "Imagine a small café owner — let's call her Priya. She wants to try a breakfast bundle offer next month. She has seen a competitor doing it, but she doesn't know whether it will make money for *her* shop, with *her* costs.
>
> DukaanPulse is a research tool that helps her go from a business question to a small, bounded test — with real web evidence, her own cost numbers, and a simple record of what happened.
>
> The workflow is four steps: ask a question, collect evidence, check the costs, then run a small test."

**Notes:**
- Priya is an illustrative character — not a real customer. Do not claim user validation.
- "Live web research powered by You.com" is accurate — the app uses the You.com Search API.
- The public prototype is live at https://dukaanpulse-eight.vercel.app/

---

## Slide 2 — The Problem

**Title:** A good offer can still be a costly guess.

**Suggested script (≈ 40 seconds):**

> "Small café owners face three recurring questions: What should I offer? Can I afford it? And did it actually work?
>
> Local information is scattered. Copying what a competitor does might not make sense for a shop with different rent, different costs, or different customer habits.
>
> And even when an owner runs a promotion, there is often no structured record of whether it succeeded — so they cannot improve from it.
>
> These are the problems DukaanPulse is designed to address."

**Notes:**
- Do not say "we validated this with merchants" unless real interviews were conducted.
- Present these as the product's design hypotheses, not confirmed pain points.

---

## Slide 3 — How It Works

**Title:** Ask. Check. Test.

**Suggested script (≈ 50 seconds):**

> "The workflow has three steps.
>
> First, the owner types a plain English question — something like 'Should I try a weekday breakfast bundle?' The app sends that to You.com, retrieves relevant web pages, and an AI model synthesises the findings. Every finding is linked back to the page it came from.
>
> Second, the owner inspects the sources — opening any citation to read the original text — and enters their own ingredient costs. The economics update live.
>
> Third, if the numbers look acceptable, they approve a small experiment — say, run the offer for two weeks. The app seeds a task checklist and lets them record daily outcomes."

**Notes:**
- The You.com search is real. It requires a valid YOU_API_KEY in the environment.
- AI synthesis uses Google Gemini and verifies that all quoted text exists in the retrieved sources.
- The economics calculation is deterministic Python — it is not AI-generated.

---

## Slide 4 — What Makes It Different

**Title:** Not just advice. A decision you can inspect.

**Suggested script (≈ 40 seconds):**

> "Four things make this different from just asking an AI chatbot.
>
> One: every finding cites the source page. The owner can click and read the original.
>
> Two: the economics use the owner's own cost numbers — not industry averages.
>
> Three: gaps are labelled clearly. If a question cannot be answered from the evidence, the app says so.
>
> Four: the experiment is tracked. Outcomes are recorded in a local database, not just forgotten."

**Notes:**
- "No invisible AI guessing" refers to the quote-verification step.
- The experiment tracker stores data in SQLite — it is a local database, not a cloud service.
- Do not claim these differentiators were confirmed by user testing.

---

## Slide 5 — Working Prototype / Demo

**Title:** One question. One clear next step.

**Demo sequence (aim for 60–90 seconds total):**

1. Open https://dukaanpulse-eight.vercel.app/ in a browser.
2. Type a question: *"Should I try a weekday breakfast bundle at my café?"*
3. Click **Research** — wait for the loading state to complete.
4. Point out the evidence cards and citation chips.
5. Click one citation chip — the evidence drawer slides open with the source excerpt.
6. Close the drawer. Change the ingredient cost (e.g. bread cost from ₹20 to ₹35).
7. Show the economics updating live (contribution margin recalculates).
8. Click **Approve Experiment** — show the task checklist appearing.

**If the demo fails (fallback):**
- Show the prototype URL and explain the demo requires a live API key.
- Walk through the slides-only version verbally.

**Notes:**
- Label all inputs during the demo as "illustrative" — these are example numbers, not real research data.
- The app is a working prototype. It has not been tested with real merchants.

---

## Slide 6 — What's Next

**Title:** Start small. Learn before spending more.

**Suggested script (≈ 35 seconds):**

> "The loop is: Research, Check, Test, Learn — and repeat.
>
> Our next steps are to test this with actual café owners, improve the workflow based on what they struggle with, and build a record from real experiments.
>
> The prototype is live. Try it at the URL on screen, or scan the QR code."

**Notes:**
- Do not claim any merchant validation has occurred unless it has.
- Do not claim revenue metrics, user counts, or conversion rates.
- If asked about the business model, honest answer: not defined yet — this is a hackathon prototype.
- GitHub repo for judges who want to review code: https://github.com/psryogeshwar-14/dukaanpulse

---

## General Presentation Tips

- **Total time:** Aim for 5–7 minutes including demo, plus Q&A.
- **Demo tip:** Have the browser open and the question pre-typed before you start. The search can take 10–20 seconds.
- **If nervous:** The slides carry the message. The demo is a bonus.
- **On questions about AI accuracy:** The app verifies every AI quote against the retrieved source text. It does not fabricate citations.
- **On questions about scale:** Honestly, this is a focused prototype. It is designed to be testable with one café owner at a time.
