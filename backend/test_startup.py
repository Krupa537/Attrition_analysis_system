#!/usr/bin/env python
"""Debug startup issues"""
import sys
import traceback

print("1. Testing imports...")
try:
    from app.db import init_db
    print("   ✓ app.db imported")
except Exception as e:
    print(f"   ✗ app.db import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    from app.auth import init_auth_db
    print("   ✓ app.auth imported")
except Exception as e:
    print(f"   ✗ app.auth import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n2. Testing database initialization...")
try:
    init_db()
    print("   ✓ init_db() successful")
except Exception as e:
    print(f"   ✗ init_db() failed: {e}")
    traceback.print_exc()

try:
    init_auth_db()
    print("   ✓ init_auth_db() successful")
except Exception as e:
    print(f"   ✗ init_auth_db() failed: {e}")
    traceback.print_exc()

print("\n3. Testing app import...")
try:
    from app.main import app
    print("   ✓ app.main imported")
except Exception as e:
    print(f"   ✗ app.main import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n✓ All tests passed!")
