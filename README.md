Attrition Analysis — Fullstack MVP

This workspace contains a minimal fullstack scaffold for an Attrition Analysis system (frontend + backend + sample data).

Backend (Python / FastAPI)
- Location: `backend/`
- Quick start (PowerShell):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend (React / Vite)
- Location: `frontend/`
- Quick start (requires Node.js/npm):

```powershell
cd frontend
npm install
npm run dev
```

Sample data: `data/ibm_attrition_sample.csv`

What's implemented (MVP):
- CSV upload endpoint
- Training endpoint (logistic regression)
- Simple React UI to upload and trigger analysis
- SQLite metadata store and saved model artifacts
- Minimal unit test scaffold under `tests/`

Next steps (suggested):
- Add authentication
- Improve file streaming and large-file handling
- Expand frontend to show metrics and charts
- Add more models and hyperparameter options
- Map the provided `software test plan` and `software architecture` docs (if you upload them) to tests and design artifacts
