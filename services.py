import asyncio

async def get_mock_weather():
    await asyncio.sleep(0.1)  # Simulando latencia
    return {"city": "Santiago", "temperature": 22.5, "condition": "Despejado"}

async def get_mock_news():
    await asyncio.sleep(0.1)
    return [
        {"title": "Sernac lanza nueva plataforma", "source": "BioBio", "url": "https://example.com/1"},
        {"title": "Dólar cierra a la baja en Chile", "source": "DF", "url": "https://example.com/2"}
    ]

async def fetch_unified_data():
    # Lanzamos todas las peticiones en paralelo (Poder asíncrono)
    weather_task = get_mock_weather()
    news_task = get_mock_news()
    
    # Esperamos a que todas terminen
    weather, news = await asyncio.gather(weather_task, news_task)
    
    return {
        "weather": weather,
        "news": news,
        "stocks": [{"symbol": "IPSA", "price": 6500.2, "change": 0.5}]
    }
