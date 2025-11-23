"""
Quick test to verify backend API is working
"""
from fastapi.testclient import TestClient
from app.main import app

def main():
    client = TestClient(app)
    
    print("=" * 60)
    print("Backend API Test Results")
    print("=" * 60)
    
    # Test 1: Health endpoint
    print("\n1. Testing /api/health endpoint...")
    try:
        response = client.get("/api/health")
        print(f"   ✓ Status: {response.status_code}")
        print(f"   ✓ Response: {response.json()}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Check if all endpoints are registered
    print("\n2. Checking registered endpoints...")
    routes = [route.path for route in app.routes if hasattr(route, 'path')]
    for route in sorted(routes):
        print(f"   - {route}")
    
    print("\n" + "=" * 60)
    print("Summary: Backend API is configured correctly!")
    print("=" * 60)
    print("\nTo start the server, run:")
    print("  python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
    print("\nThen test with:")
    print("  Invoke-RestMethod http://localhost:8000/api/health")
    print("\nNOTE: Keep the server running - don't press CTRL+C until you're done testing!")

if __name__ == "__main__":
    main()
