Attrition Analysis Backend

This is a minimal FastAPI backend for the Attrition Analysis system.

Quick start (Windows PowerShell):

# Create a virtual environment and install dependencies
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run the API
uvicorn app.main:app --reload --port 8000

## Email Alerts Configuration (New Feature)

The system now sends automated email alerts to HR when employees are at risk of attrition.

### Setup Email Credentials:
```powershell
$env:SMTP_SERVER = "smtp.gmail.com"
$env:SMTP_PORT = "587"
$env:SMTP_USERNAME = "your-email@gmail.com"
$env:SMTP_PASSWORD = "your-app-password"
$env:SENDER_EMAIL = "your-email@gmail.com"
```

### Test Email Configuration:
```powershell
python test_email_config.py
```

📖 See [EMAIL_SETUP.md](EMAIL_SETUP.md) for detailed configuration instructions.

Endpoints:
- POST /api/upload (multipart/form-data file)
- POST /api/analyze (JSON: dataset_id, target_column)
- GET /api/analyses
- GET /api/analysis/{analysis_id}
- POST /api/predict (JSON: analysis_id, records, send_alerts=true) **[NEW: Sends email alerts]**
- GET /api/at_risk_employees/{analysis_id}?send_alerts=true **[NEW: Includes email alerts]**
- POST /api/auth/signup (JSON: email, password, full_name, department)
- POST /api/auth/login (JSON: email, password)
- GET /api/auth/users

Notes:
- This is an MVP scaffold. Add authentication, larger-file streaming, better persistence and production config for real deployments.

