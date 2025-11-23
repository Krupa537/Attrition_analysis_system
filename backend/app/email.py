import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from datetime import datetime


# Email Configuration - using environment variables for security
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SENDER_EMAIL = os.getenv('SENDER_EMAIL', SMTP_USERNAME)


def send_email(to_email: str, subject: str, body: str, html: bool = True) -> bool:
    """
    Send an email using SMTP
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        html: Whether the body is HTML (default True)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("Warning: SMTP credentials not configured. Email not sent.")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        if html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        # Connect to SMTP server
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"Email sent successfully to {to_email}")
        return True
    
    except Exception as e:
        print(f"Failed to send email to {to_email}: {str(e)}")
        return False


def send_attrition_alert(hr_email: str, hr_name: str, at_risk_employees: List[Dict[str, Any]], 
                        analysis_id: str) -> bool:
    """
    Send an alert email to HR about employees at risk of attrition
    
    Args:
        hr_email: HR's email address
        hr_name: HR's full name
        at_risk_employees: List of employees at risk with their data
        analysis_id: ID of the analysis
    
    Returns:
        bool: True if email sent successfully
    """
    subject = f"⚠️ Attrition Alert: {len(at_risk_employees)} Employee(s) at Risk"
    
    # Create HTML email body
    employee_rows = ""
    for emp in at_risk_employees[:20]:  # Limit to first 20 employees in email
        emp_data = emp.get('employee_data', {})
        employee_id = emp_data.get('EmployeeID') or emp_data.get('id') or emp.get('index', 'N/A')
        name = emp_data.get('Name', 'N/A')
        department = emp_data.get('Department', 'N/A')
        risk_prob = emp.get('attrition_probability', 0) * 100
        risk_level = emp.get('risk_level', 'Unknown')
        
        # Color code based on risk level
        risk_color = '#d32f2f' if risk_level == 'Critical' else '#f57c00' if risk_level == 'High' else '#fbc02d'
        
        employee_rows += f"""
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">{employee_id}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{name}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{department}</td>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; color: {risk_color};">{risk_prob:.1f}%</td>
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; color: {risk_color};">{risk_level}</td>
        </tr>
        """
    
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            .header {{ background-color: #d32f2f; color: white; padding: 20px; }}
            .content {{ padding: 20px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th {{ background-color: #f5f5f5; padding: 10px; text-align: left; border: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>⚠️ Attrition Risk Alert</h2>
        </div>
        <div class="content">
            <p>Dear {hr_name},</p>
            
            <p>This is an automated alert from the Attrition Analysis System.</p>
            
            <p><strong>We have identified {len(at_risk_employees)} employee(s) at risk of attrition.</strong></p>
            
            <p>Please review the following employees and consider taking proactive measures:</p>
            
            <table>
                <thead>
                    <tr>
                        <th>Employee ID</th>
                        <th>Name</th>
                        <th>Department</th>
                        <th>Risk Probability</th>
                        <th>Risk Level</th>
                    </tr>
                </thead>
                <tbody>
                    {employee_rows}
                </tbody>
            </table>
            
            {f'<p><em>Note: Showing top 20 of {len(at_risk_employees)} at-risk employees</em></p>' if len(at_risk_employees) > 20 else ''}
            
            <p style="margin-top: 30px;">
                <strong>Recommended Actions:</strong><br>
                • Schedule one-on-one meetings with high-risk employees<br>
                • Review compensation and career development opportunities<br>
                • Address work environment concerns<br>
                • Consider retention strategies for critical employees
            </p>
            
            <p style="margin-top: 20px; color: #666; font-size: 12px;">
                Analysis ID: {analysis_id}<br>
                Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                This is an automated message from the Attrition Analysis System.
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_email(hr_email, subject, html_body, html=True)


def send_batch_attrition_alerts(hr_users: List[Dict[str, str]], at_risk_employees: List[Dict[str, Any]], 
                                analysis_id: str) -> Dict[str, int]:
    """
    Send attrition alerts to multiple HR users
    
    Args:
        hr_users: List of HR user dictionaries with 'email' and 'full_name' keys
        at_risk_employees: List of employees at risk
        analysis_id: ID of the analysis
    
    Returns:
        dict: Summary with 'sent', 'failed', 'total' counts
    """
    sent = 0
    failed = 0
    
    for hr_user in hr_users:
        hr_email = hr_user.get('email')
        hr_name = hr_user.get('full_name', 'HR Team')
        
        if hr_email:
            success = send_attrition_alert(hr_email, hr_name, at_risk_employees, analysis_id)
            if success:
                sent += 1
            else:
                failed += 1
        else:
            failed += 1
    
    return {
        'sent': sent,
        'failed': failed,
        'total': len(hr_users)
    }
