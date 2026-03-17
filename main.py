from fastapi import FastAPI
from schemas import UnifiedFeed
from services import fetch_unified_data

app = FastAPI(
    title="Gateway-Aggregator",
    description="Middleware para agregación de APIs públicas",
    version="1.0.0"
)

@app.get("/v1/feed", response_model=UnifiedFeed)
async def get_feed():
    """
    Consigue el clima, noticias y stocks en una sola llamada.
    """
    data = await fetch_unified_data()
    return data
