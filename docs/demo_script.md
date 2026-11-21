# DukaanPulse 3-Minute Live Demonstration Script
**Track:** You.com Live, Cited Web-Data Track | Beyond 9TO5 Buildathon

---

### [0:00 - 0:25] The Problem & The Independent Café Context
> *"Judges, independent café owners make pricing and promotional decisions with two major handicaps: incomplete local market intelligence and tight, unforgiving cost structures.*
> 
> *Generic AI chatbots hallucinate competitor prices and promise fake 40% revenue increases. But an offer that looks popular on social media can easily bankrupt a café if its unit economics don't work.*
> 
> *That is why we built **DukaanPulse**: a live, cited, margin-aware research-to-action assistant for independent cafés."*

---

### [0:25 - 0:50] Step 1 & 2: Café Scenario & Live You.com Research
*(In browser at `http://127.0.0.1:8000`)*
> *"Let's take our benchmark case: a café in HSR Layout, Bengaluru asks:*
> **'Should I test a weekday breakfast bundle within a budget of INR 2,000, using existing equipment?'**
> 
> *We hit **Execute Live Research**. Watch the live console: DukaanPulse formulates up to 3 focused queries, queries the **You.com Search API**, strips tracking parameters, and compiles an inspectable evidence ledger in real time."*

---

### [0:50 - 1:20] Step 3 & 4: Inspecting Grounded Sources & Visible Uncertainty
*(Click on Evidence Chip `[E1]`)*
> *"Notice: every claim is tied to an explicit source chip. When I click `[E1]`, our evidence inspector opens.*
> 
> *You can inspect the exact returned excerpt from You.com, the search query, the retrieval timestamp—distinct from the publication date—and the safe HTTPS link.*
> 
> *Notice too what DukaanPulse does NOT do: it explicitly lists **Material Unknowns**—such as early morning footfall before 8:30 AM—admitting what public web data cannot prove."*

---

### [1:20 - 1:50] Step 5 & 6: Merchant Unit Economics & Contribution Calculation
*(Scroll to the Unit Economics Card)*
> *"Next comes the vital business bridge: the owner's unit economics. These costs are clearly labeled as **Owner Assumptions**.*
> 
> *Selling price: ₹179. Ingredient cost: ₹50. Packaging: ₹10. Other: ₹5. One-time setup: ₹450.*
> 
> *Our deterministic Python engine calculates: variable cost is ₹65, leaving a **Contribution Margin of ₹114 per bundle** (63.7% margin). It explicitly calculates that 4 orders cover the ₹450 setup cost. We label this 'Contribution', not net profit, because fixed rent is excluded."*

---

### [1:50 - 2:20] Step 7, 8 & 9: Dynamic Stale-State Defense & Invalidating Bad Advice
*(Demonstrate changing ingredient cost to ₹180 in the inputs)*
> *"Now watch what happens if market conditions change. Suppose milk and coffee bean costs surge to ₹180 per bundle.*
> 
> *Instantly, DukaanPulse flags the offer: **DO NOT LAUNCH. Unit variable costs exceed selling price. Every order loses money.***
> 
> *If an experiment was already generated, our system flags it as **STALE** and disables the approval button. DukaanPulse never allows an old positive recommendation to remain active when the underlying cost assumptions break down."*

---

### [2:20 - 2:45] Step 10 & 11: Owner Acceptance & Simulated Outcome Tracking
*(Restore viable costs, click 'Approve & Accept Experiment', switch to Tracker)*
> *"With viable economics restored, the owner clicks **Approve & Accept Experiment**.*
> 
> *This locks the approved assumptions snapshot into SQLite and launches our **Experiment Tracker**. Let's log Day 1: 12 orders, ₹2,148 revenue, ₹720 variable costs.*
> 
> *The ledger records a verified contribution of ₹1,428. Everything persists reliably across server restarts."*

---

### [2:45 - 3:00] Closing Statement
> *"Closing line:*
> **'DukaanPulse helps a small café investigate an offer, check its own economics, and run one measurable experiment—with live sources and visible uncertainty.'**
> *Thank you!"*
