"""
Test Email Configuration Script

This script helps you test your email configuration before using it in the application.
Run this script to verify your SMTP settings are correct.
"""

import os
import sys

# Add parent directory to path to import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.email import send_email, send_attrition_alert


def test_basic_email():
    """Test sending a basic email"""
    print("\n" + "="*60)
    print("Testing Basic Email Configuration")
    print("="*60)
    
    # Check if credentials are configured
    smtp_user = os.getenv('SMTP_USERNAME')
    smtp_pass = os.getenv('SMTP_PASSWORD')
    
    if not smtp_user or not smtp_pass:
        print("\n❌ ERROR: SMTP credentials not configured!")
        print("\nPlease set environment variables:")
        print("  $env:SMTP_SERVER = 'smtp.gmail.com'")
        print("  $env:SMTP_PORT = '587'")
        print("  $env:SMTP_USERNAME = 'your-email@gmail.com'")
        print("  $env:SMTP_PASSWORD = 'your-app-password'")
        print("  $env:SENDER_EMAIL = 'your-email@gmail.com'")
        return False
    
    print(f"\n✓ SMTP Server: {os.getenv('SMTP_SERVER', 'smtp.gmail.com')}")
    print(f"✓ SMTP Port: {os.getenv('SMTP_PORT', '587')}")
    print(f"✓ Username: {smtp_user}")
    print(f"✓ Sender: {os.getenv('SENDER_EMAIL', smtp_user)}")
    
    # Get test recipient email
    test_email = input("\nEnter test recipient email address: ").strip()
    if not test_email:
        print("❌ No email address provided")
        return False
    
    print(f"\nSending test email to {test_email}...")
    
    subject = "Test Email - Attrition Analysis System"
    body = """
    <html>
    <body>
        <h2>✓ Email Configuration Test Successful!</h2>
        <p>This is a test email from the Attrition Analysis System.</p>
        <p>If you received this email, your SMTP configuration is working correctly.</p>
        <hr>
        <p style="color: #666; font-size: 12px;">
            This is an automated test message.
        </p>
    </body>
    </html>
    """
    
    success = send_email(test_email, subject, body, html=True)
    
    if success:
        print("✓ Email sent successfully!")
        print(f"Check {test_email} inbox (and spam folder)")
        return True
    else:
        print("❌ Failed to send email. Check the error message above.")
        return False


def test_attrition_alert():
    """Test sending an attrition alert email"""
    print("\n" + "="*60)
    print("Testing Attrition Alert Email")
    print("="*60)
    
    test_email = input("\nEnter HR email address for alert test: ").strip()
    if not test_email:
        print("❌ No email address provided")
        return False
    
    hr_name = input("Enter HR name (or press Enter for 'Test HR'): ").strip() or "Test HR"
    
    # Sample at-risk employees data
    sample_employees = [
        {
            'index': 0,
            'attrition_probability': 0.85,
            'risk_level': 'Critical',
            'employee_data': {
                'EmployeeID': 'EMP001',
                'Name': 'John Doe',
                'Department': 'Sales',
                'Age': 35,
                'JobSatisfaction': 2
            }
        },
        {
            'index': 1,
            'attrition_probability': 0.72,
            'risk_level': 'High',
            'employee_data': {
                'EmployeeID': 'EMP002',
                'Name': 'Jane Smith',
                'Department': 'Engineering',
                'Age': 28,
                'JobSatisfaction': 3
            }
        },
        {
            'index': 2,
            'attrition_probability': 0.58,
            'risk_level': 'Moderate',
            'employee_data': {
                'EmployeeID': 'EMP003',
                'Name': 'Bob Johnson',
                'Department': 'Marketing',
                'Age': 42,
                'JobSatisfaction': 2
            }
        }
    ]
    
    print(f"\nSending attrition alert to {test_email}...")
    print(f"Sample alert: 3 employees at risk")
    
    success = send_attrition_alert(
        hr_email=test_email,
        hr_name=hr_name,
        at_risk_employees=sample_employees,
        analysis_id='test-analysis-123'
    )
    
    if success:
        print("✓ Attrition alert sent successfully!")
        print(f"Check {test_email} inbox for the alert email")
        return True
    else:
        print("❌ Failed to send alert. Check the error message above.")
        return False


def main():
    """Main test menu"""
    print("\n" + "="*60)
    print("Email Configuration Test Tool")
    print("Attrition Analysis System")
    print("="*60)
    
    while True:
        print("\nSelect test option:")
        print("1. Test Basic Email")
        print("2. Test Attrition Alert Email")
        print("3. Run All Tests")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            test_basic_email()
        elif choice == '2':
            test_attrition_alert()
        elif choice == '3':
            print("\nRunning all tests...")
            if test_basic_email():
                print("\n" + "-"*60)
                test_attrition_alert()
        elif choice == '4':
            print("\nExiting test tool. Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-4.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
