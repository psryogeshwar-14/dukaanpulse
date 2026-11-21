# DukaanPulse: Vercel Deployment Guide

DukaanPulse has been pre-configured for seamless serverless deployment to **Vercel** via Python Serverless Functions.

---

## 1. Project Files Pre-Configured for Vercel

The following deployment configuration files have been created in the workspace:

- [`vercel.json`](file:///Users/psryogeshwar/Documents/Documents/Project/paytm1/vercel.json): Configures URL rewrites to route all web and API traffic through `@vercel/python` serverless handler.
- [`api/index.py`](file:///Users/psryogeshwar/Documents/Documents/Project/paytm1/api/index.py): Serverless ASGI entrypoint that dynamically loads `app.py`.
- [`app.py`](file:///Users/psryogeshwar/Documents/Documents/Project/paytm1/app.py): Automatically detects the `VERCEL` environment variable and shifts default SQLite storage to `/tmp/dukaanpulse.db` to prevent read-only filesystem errors.
- [`requirements.txt`](file:///Users/psryogeshwar/Documents/Documents/Project/paytm1/requirements.txt): Bundles all required runtime dependencies for Vercel's Python build system.

---

## 2. Serverless Storage Considerations

> [!IMPORTANT]
> **Ephemeral Filesystem on Serverless:**
> Vercel Lambda functions have an ephemeral, read-only root directory. While DukaanPulse writes to `/tmp/dukaanpulse.db` so the app runs smoothly in serverless execution, data in `/tmp` resets when container instances spin down.
> 
> For **permanent multi-user persistence** in production, configure an external cloud database (such as **Turso / libSQL**, **Supabase Postgres**, or **Neon**) by setting the `DATABASE_URL` environment variable.

---

## 3. Required Environment Variables in Vercel

When deploying in the Vercel Dashboard (**Project Settings → Environment Variables**), add the following:

| Variable Name | Example / Value | Description |
|---|---|---|
| `YOU_API_KEY` | `your_you_com_key` | Required for live web retrieval |
| `YOU_SEARCH_URL` | `https://ydc-index.io/v1/search` | Search endpoint URL |
| `LLM_PROVIDER` | `gemini` (or `openai`) | Synthesis AI engine |
| `LLM_API_KEY` | `your_model_key` | Provider API key |
| `LLM_MODEL` | `gemini-1.5-flash` | Selected model name |

---

## 4. Deployment Methods

### Option A: Deploy via GitHub (Recommended)
1. Push your project to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Prepare DukaanPulse for Vercel deployment"
   git branch -M main
   # Add your remote and push:
   # git remote add origin https://github.com/your-username/dukaanpulse.git
   # git push -u origin main
   ```
2. Navigate to [vercel.com/new](https://vercel.com/new).
3. Import your repository.
4. Under **Environment Variables**, paste the keys listed in Section 3.
5. Click **Deploy**. Vercel will build the Python environment and provide your live production URL (e.g. `https://dukaanpulse.vercel.app`).

### Option B: Deploy via Vercel CLI
If you prefer deploying directly from your terminal:
```bash
# 1. Login to your Vercel account
npx vercel login

# 2. Deploy preview
npx vercel

# 3. Deploy to production
npx vercel --prod
```
