import asyncio
from app.main import health

async def test_health():
    try:
        result = await health()
        print("Health endpoint result:", result)
    except Exception as e:
        print(f"Error calling health endpoint: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_health())
