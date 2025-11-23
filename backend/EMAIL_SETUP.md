# Email Alert Configuration Guide

## Overview
The Attrition Analysis System now sends automated email alerts to HR users when employees are identified as at risk of attrition.

## Features
- **Automated Alerts**: Sends email notifications when at-risk employees are detected
- **HR Email Integration**: Uses the email addresses HR users provide during signup/login
- **Risk Categorization**: Categorizes employees as Critical (≥80%), High (≥60%), or Moderate (≥50%) risk
- **Batch Notifications**: Can send alerts to multiple HR users simultaneously
- **HTML Email Templates**: Professional formatted emails with employee details

## Configuration

### Environment Variables
Set the following environment variables to configure email functionality:

#### For Gmail (Recommended for Testing)
```bash
# Windows PowerShell
$env:SMTP_SERVER = "smtp.gmail.com"
$env:SMTP_PORT = "587"
$env:SMTP_USERNAME = "your-email@gmail.com"
$env:SMTP_PASSWORD = "your-app-password"
$env:SENDER_EMAIL = "your-email@gmail.com"
```

#### For Other Email Providers
```bash
# Outlook/Office365
$env:SMTP_SERVER = "smtp.office365.com"
$env:SMTP_PORT = "587"

# Yahoo
$env:SMTP_SERVER = "smtp.mail.yahoo.com"
$env:SMTP_PORT = "587"

# Custom SMTP Server
$env:SMTP_SERVER = "smtp.your-domain.com"
$env:SMTP_PORT = "587"
```

### Gmail App Password Setup
1. Go to your Google Account settings
2. Select "Security" > "2-Step Verification" (must be enabled)
3. Scroll to "App passwords"
4. Generate a new app password for "Mail"
5. Use this 16-character password as `SMTP_PASSWORD`

### Outlook/Office365 Setup
1. Use your regular email and password
2. Ensure "Allow less secure apps" is enabled (or use OAuth2 for production)

## API Usage

### 1. Predict with Email Alerts (Default Enabled)
```bash
POST /api/predict?send_alerts=true
Body:
{
  "analysis_id": "your-analysis-id",
  "records": [
    {
      "Age": 35,
      "Department": "Sales",
      "JobSatisfaction": 2,
      ...
    }
  ]
}
```

Response includes:
```json
{
  "predictions": [...],
  "email_alerts": {
    "sent": 2,
    "failed": 0,
    "total": 2
  }
}
```

### 2. Get At-Risk Employees with Alerts
```bash
GET /api/at_risk_employees/{analysis_id}?send_alerts=true&risk_threshold=0.5
```

Response includes:
```json
{
  "total_employees": 100,
  "at_risk_count": 15,
  "critical_count": 5,
  "risk_percentage": 15.0,
  "at_risk_employees": [...],
  "email_alerts": {
    "sent": 2,
    "failed": 0,
    "total": 2
  }
}
```

## Email Alert Behavior

### When Alerts are Sent
- **Predict Endpoint**: Alerts sent automatically when `send_alerts=true` (default) and any employee has risk probability ≥ 50%
- **At-Risk Employees Endpoint**: Alerts sent only when explicitly requested with `send_alerts=true`

### Who Receives Alerts
- All HR users registered in the system receive alerts
- Uses the email address provided during HR user signup

### Alert Content
Each alert email includes:
- Total count of at-risk employees
- Employee details table with:
  - Employee ID
  - Name (if available)
  - Department
  - Risk Probability (%)
  - Risk Level (Critical/High/Moderate)
- Recommended actions for HR
- Analysis ID and timestamp

### Risk Thresholds
- **Critical**: Attrition probability ≥ 80%
- **High**: Attrition probability ≥ 60%
- **Moderate**: Attrition probability ≥ 50%

## Troubleshooting

### No Emails Sent
1. **Check Environment Variables**: Ensure all SMTP variables are set
2. **Verify Credentials**: Test your email login credentials
3. **Check Logs**: Look for warning messages in the console
4. **HR Users Exist**: Ensure at least one HR user is registered

### Authentication Errors
- **Gmail**: Use App Password, not regular password
- **Outlook**: Ensure account has SMTP enabled
- **2FA**: Use app-specific passwords if 2FA is enabled

### Email Not Received
- Check spam/junk folders
- Verify HR user email addresses are correct
- Check email provider's sending limits
- Review SMTP server logs

### Testing Email Configuration
```python
# Run in Python console to test email
from backend.app.email import send_email
send_email(
    to_email="test@example.com",
    subject="Test Email",
    body="<h1>Test</h1><p>This is a test email.</p>",
    html=True
)
```

## Security Best Practices

### Production Deployment
1. **Never commit credentials**: Keep SMTP credentials in environment variables
2. **Use OAuth2**: For Gmail/Office365, consider OAuth2 instead of passwords
3. **Encrypted connections**: Always use TLS/SSL (port 587 or 465)
4. **Rate limiting**: Implement rate limiting to prevent email spam
5. **Audit logs**: Log all email sending attempts for security auditing

### Environment Variable Management
```bash
# Create a .env file (add to .gitignore)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=your-email@gmail.com
```

## Disabling Email Alerts

### Temporarily Disable
```bash
# Don't set SMTP credentials (emails won't send, warnings shown in logs)
# OR
# Use send_alerts=false in API calls
```

### Permanently Disable
Remove the `send_alerts` logic from `main.py` or set a configuration flag.

## Future Enhancements
- Email templates customization
- Email scheduling (daily/weekly summaries)
- Department-specific alerts (notify only relevant HR)
- Email delivery status tracking
- SMS/Slack integration for critical alerts
