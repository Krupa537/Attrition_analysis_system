#!/usr/bin/env python3
"""
Quick test script to verify authentication functions work correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.auth import init_auth_db, create_hr_user, authenticate_hr_user, get_hr_user
import uuid

def test_auth():
    print("=" * 60)
    print("Testing Authentication System")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing auth database...")
    try:
        init_auth_db()
        print("   ✓ Database initialized successfully")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test user creation
    print("\n2. Testing user signup...")
    test_email = f"testuser_{uuid.uuid4().hex[:8]}@test.com"
    test_password = "password123"
    test_name = "Test User"
    test_dept = "HR"
    
    try:
        user_result = create_hr_user(test_email, test_password, test_name, test_dept)
        print(f"   ✓ User created successfully")
        print(f"   - User ID: {user_result['user_id']}")
        print(f"   - Email: {user_result['email']}")
        print(f"   - Full Name: {user_result['full_name']}")
        print(f"   - Department: {user_result['department']}")
        user_id = user_result['user_id']
    except Exception as e:
        print(f"   ✗ Error creating user: {e}")
        return False
    
    # Test login with correct password
    print("\n3. Testing login with correct password...")
    try:
        login_result = authenticate_hr_user(test_email, test_password)
        if login_result:
            print(f"   ✓ Login successful")
            print(f"   - User ID: {login_result['user_id']}")
            print(f"   - Email: {login_result['email']}")
            print(f"   - Status: {login_result['status']}")
        else:
            print(f"   ✗ Login failed - returned None")
            return False
    except Exception as e:
        print(f"   ✗ Error during login: {e}")
        return False
    
    # Test login with wrong password
    print("\n4. Testing login with wrong password...")
    try:
        login_result = authenticate_hr_user(test_email, "wrongpassword")
        if login_result is None:
            print(f"   ✓ Correctly rejected wrong password")
        else:
            print(f"   ✗ Security issue: wrong password accepted!")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test get user
    print("\n5. Testing get user by ID...")
    try:
        user = get_hr_user(user_id)
        if user:
            print(f"   ✓ User retrieved successfully")
            print(f"   - Email: {user['email']}")
            print(f"   - Full Name: {user['full_name']}")
        else:
            print(f"   ✗ User not found")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test duplicate email
    print("\n6. Testing duplicate email prevention...")
    try:
        duplicate_result = create_hr_user(test_email, "anotherpassword", "Another User")
        print(f"   ✗ Security issue: duplicate email allowed!")
        return False
    except ValueError as e:
        print(f"   ✓ Correctly prevented duplicate email: {e}")
    except Exception as e:
        print(f"   ✗ Unexpected error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = test_auth()
    sys.exit(0 if success else 1)
