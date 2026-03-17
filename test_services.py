import asyncio
from services import get_weather, get_real_news

async def main():
    print("Testing get_weather()...")
    weather = await get_weather()
    print(f"Weather Result: {weather}")
    
    print("\nTesting get_real_news()...")
    news = await get_real_news()
    print(f"News Count: {len(news)}")
    if news:
        print(f"First news item: {news[0]}")
    else:
        print("NEWS LIST IS EMPTY")

if __name__ == "__main__":
    asyncio.run(main())
