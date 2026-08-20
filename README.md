# Complaint Classification System

## Architecture
- **Frontend**: React + Vite, Google login, chat UI (`/frontend`)
- **Backend**: Flask on Vercel serverless (`/backend`), stateless — the
  frontend carries `complaint_data` on every request, so nothing depends on
  server memory surviving between calls (important since Vercel functions
  are not guaranteed to persist state).
- **Slot filling** (location/time/contact): spaCy NER + regex, fully offline,
  no external API call — replaces the old Gemini dependency.
- **Classification**: zero-shot via Hugging Face Inference API
  (`facebook/bart-large-mnli`) — one lightweight HTTPS call, no model
  weights bundled, so it still fits inside a normal Vercel function.
- **Department emails**: stored in MongoDB Atlas, looked up at send time.
- **Sending**: SMTP from the existing "safety bot" mail account.

## Local setup

### Backend
```
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in real values
python seed_departments.py   # seeds dummy department emails into Mongo
python api/index.py          # runs on localhost:5000
```

### Frontend
```
cd frontend
npm install
cp .env.example .env   # set VITE_API_URL to your backend URL
npm run dev
```

## Deploying to Vercel
Deploy `/backend` and `/frontend` as **two separate Vercel projects**
(don't deploy the repo root — Vercel needs a project root per app).

For each project, set the env vars from its `.env.example` in
**Vercel Dashboard → Project → Settings → Environment Variables**, then
redeploy (Vite bakes env vars in at build time, so a var added after a
build won't take effect until you rebuild).

After both are deployed, set `VITE_API_URL` (frontend) to the backend's
live Vercel URL, and `GOOGLE_CLIENT_ID` (backend) to match the same OAuth
client used in the frontend's `VITE_GOOGLE_CLIENT_ID`.

## Known limitations to revisit later
- Only one complaint "type" flow is implemented (description → location →
  time → contact) — matches the current single-section scope.
- HF Inference API's free tier can have cold-start latency on the first
  call after idle time — fine for a demo, worth caching/upgrading later.
- No persistence of past complaints yet — add a `complaints` collection in
  Mongo if you want a history/audit trail.
