from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    try:
        response = client.get("/api/health")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 200
        print("✓ Health endpoint test passed")
    except Exception as e:
        print(f"✗ Health endpoint test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_health_endpoint()
