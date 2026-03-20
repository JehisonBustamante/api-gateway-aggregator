import httpx
import asyncio

async def test_wttr():
    CITY_NAME = "Santiago"
    try:
        url = f"https://wttr.in/{CITY_NAME}?format=j1"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            json_data = response.json()
            current = json_data["data"]["current_condition"][0]
            condition = current["weatherDesc"][0]["value"]
            temp = current["temp_C"]
            print(f"City: {CITY_NAME}")
            print(f"Condition: {condition}")
            print(f"Temperature: {temp}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_wttr())
