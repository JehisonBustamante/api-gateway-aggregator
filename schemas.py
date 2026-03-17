from pydantic import BaseModel
from typing import List, Optional

class WeatherData(BaseModel):
    city: str
    temperature: float
    condition: str

class NewsItem(BaseModel):
    title: str
    source: str
    url: str

class StockData(BaseModel):
    symbol: str
    price: float
    change: float

class UnifiedFeed(BaseModel):
    weather: Optional[WeatherData]
    news: List[NewsItem]
    stocks: List[StockData]
