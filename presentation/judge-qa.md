# DukaanPulse — Judge Q&A Prep
*Honest answers only. No fabricated metrics.*

---

## Product & Value

**Q: What problem are you solving?**
> Small café owners lack a structured way to research a local business idea, check whether it makes financial sense with *their* costs, and record whether it worked. DukaanPulse walks them through that process step by step.

**Q: Have you talked to any café owners?**
> Not yet in a formal validation sense. The product is built around a plausible workflow. Our next step is to put it in front of real owners and learn from how they use it.

**Q: How is this different from just asking ChatGPT?**
> Three differences: (1) every finding is sourced — you can read the original page; (2) the economics use the owner's own numbers, not AI estimates; (3) the experiment is tracked locally so outcomes are recorded, not forgotten.

**Q: What if the owner does not understand the evidence?**
> That is a real UX challenge we have not fully solved. The current interface is text-heavy. A next iteration would simplify the evidence presentation for lower-literacy users.

---

## Technology

**Q: Does the AI make up results?**
> The AI synthesis step verifies every quoted sentence against the retrieved source text. If the text is not found in the source, it is not included. This is not a complete guarantee, but it reduces fabrication significantly.

**Q: What if You.com is unavailable?**
> The app has a mock mode that returns structured placeholder output. This is used in development and as a fallback.

**Q: What does the tech stack look like?**
> FastAPI backend in Python, SQLite for the experiment database, vanilla JavaScript frontend, deployed on Vercel. No heavy framework dependencies.

**Q: Is the data private?**
> Currently, research results are stored server-side in SQLite (on Vercel's ephemeral filesystem). For a production version, proper user data isolation and a persistent database would be essential.

**Q: Can it handle multiple users?**
> The current prototype has no authentication. It is designed as a single-user tool. Multi-tenant support is not implemented.

---

## Business

**Q: What is your business model?**
> Not defined yet. This is a hackathon prototype. Possible directions: a subscription tool for independent shop owners, a white-label research assistant for small business networks, or integration with POS or inventory systems.

**Q: Who is your target customer?**
> Independent café or small food business owners who make regular pricing and offer decisions without a research team.

**Q: What would make a merchant pay for this?**
> If it saves them from running a promotion that loses money, it has clear ROI. That needs to be demonstrated with real usage data — which we do not have yet.

**Q: How would you distribute this?**
> We have not planned distribution. Possible channels: small business associations, food entrepreneur communities, café supply companies.

---

## Honesty / Limitations

**Q: What does not work yet?**
> - No user authentication or multi-user support.
> - The experiment outcome tracking is minimal — just free-text daily notes.
> - No merchant validation has been done.
> - The economics model is simplified (contribution margin only, no overhead allocation).
> - The interface is not localised into regional languages.

**Q: Can it handle Indian market specifics?**
> The research uses You.com web search, which can find Indian market content. However, the economics model uses generic contribution margin logic — it does not know about GST, FSSAI requirements, or region-specific pricing norms.

**Q: What is the biggest risk?**
> That café owners find the evidence too abstract or the interface too complex. The product needs real usability testing to find out.

---

*Reminder: never invent customer testimonials, revenue figures, or usage statistics when answering judges.*
