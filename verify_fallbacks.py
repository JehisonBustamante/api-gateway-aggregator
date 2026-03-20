import asyncio
import time
from services import _cache, _cache_set, get_weather, get_real_news

async def verify_fallbacks():
    print("--- Verifying Fallbacks ---")
    
    # 1. Weather Fallback
    print("\nTesting Weather Fallback...")
    # Inject stale data
    _cache_set("weather", {"city": "Santiago", "temperature": 25.0, "condition": "Sunny"})
    # Manually expire it (set timestamp back 1 hour)
    _cache["weather"] = (_cache["weather"][0], time.time() - 3600)
    
    # Now get_weather should fail OpenWeatherMap (wrong key) and wttr.in (if we mock it or if it fails)
    # Since we can't easily mock httpx here ohne monkeypatching, we just rely on the fact that 
    # OpenWeatherMap WILL fail with the placeholder key. 
    # If wttr.in also fails or if we simular it:
    
    print("Calling get_weather() (should fallback to stale cache if wttr.in fails)...")
    result = await get_weather()
    print(f"Weather Result: {result}")
    
    # 2. News Fallback
    print("\nTesting News Fallback...")
    # Inject stale news
    _cache_set("news", [{"title": "Old News", "source": "Old", "url": "#"}])
    _cache["news"] = (_cache["news"][0], time.time() - 3600)
    
    # We want to force a failure in httpx for news. 
    # A simple way is to temporarily change the NEWS_RSS_URL to something invalid if we could,
    # but let's just observe if it fails naturally or if we can see the logic.
    
    print("Calling get_real_news() (should use stale if API fails)...")
    news = await get_real_news()
    print(f"News Count: {len(news)}")
    if news and news[0]['title'] == "Old News":
        print("SUCCESS: Used stale news fallback.")
    else:
        print(f"INFO: Fetched fresh news (Count: {len(news)})")

if __name__ == "__main__":
    asyncio.run(verify_fallbacks())
