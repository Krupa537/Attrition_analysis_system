Attrition Analysis Backend

This is a minimal FastAPI backend for the Attrition Analysis system.

Quick start (Windows PowerShell):

# Create a virtual environment and install dependencies
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run the API
uvicorn app.main:app --reload --port 8000

Endpoints:
- POST /api/upload (multipart/form-data file)
- POST /api/analyze (JSON: dataset_id, target_column)
- GET /api/analyses
- GET /api/analysis/{analysis_id}
- POST /api/predict (JSON: analysis_id, records)

Notes:
- This is an MVP scaffold. Add authentication, larger-file streaming, better persistence and production config for real deployments.
