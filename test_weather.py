import asyncio
from services import get_weather

async def main():
    print("Testing get_weather()...")
    result = await get_weather()
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
