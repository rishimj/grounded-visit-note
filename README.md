---
title: Grounded Visit Note
emoji: 🩺
colorFrom: blue
colorTo: yellow
sdk: docker
pinned: false
app_port: 7860
---

# Grounded Visit Note

Upload a visit transcript. The app returns a SOAP note. Click a bullet to highlight the transcript lines it came from.

Live demo: https://huggingface.co/spaces/rishimj/grounded-visit-note

No real patient data. Set `GEMINI_API_KEY` in `.env` locally (never commit it).

## Local run

```bash
# backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Sample transcripts are in `docs/`.
