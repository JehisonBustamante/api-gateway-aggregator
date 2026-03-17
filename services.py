"""
services.py — Capa de Servicios del Gateway Agregador
=====================================================
Aquí viven las funciones que salen a buscar datos reales a APIs externas.
Cada función es asíncrona (async) para poder ejecutarse en paralelo y no
bloquear el servidor mientras espera respuestas de red.
"""

import asyncio           # Para asyncio.gather → ejecutar tareas en paralelo
import httpx             # Cliente HTTP asíncrono (moderna alternativa a requests)
import os                # Para leer variables de entorno
import time              # Para calcular la antigüedad del caché
import feedparser        # Para parsear feeds RSS/Atom
import yfinance as yf   # Librería que envuelve la API de Yahoo Finance (sin API key)

from dotenv import load_dotenv   # Para cargar variables desde el archivo .env

# ─── Carga de Variables de Entorno ──────────────────────────────────────────
# load_dotenv() lee el archivo .env y expone sus valores como variables de entorno.
# Esto nos permite guardar API keys fuera del código fuente (buena práctica de seguridad).
load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")          # Tu key de OpenWeatherMap
CITY_NAME           = os.getenv("CITY_NAME", "Santiago")         # Ciudad objetivo (default: Santiago)
UNITS               = os.getenv("UNITS", "metric")               # "metric" → Celsius
NEWS_RSS_URL        = os.getenv(                                  # URL del feed RSS de noticias
    "NEWS_RSS_URL",
    "https://news.google.com/rss/search?q=Santiago%20Chile&hl=es-419&gl=CL&ceid=CL:es-419"
)

# ─── Caché en Memoria ────────────────────────────────────────────────────────
# Un diccionario global que actúa como caché. La clave es el nombre del dato
# (ej. "weather") y el valor es una tupla (datos, timestamp).
#
# Esto evita llamar a las APIs externas en CADA petición del usuario.
# El clima de Santiago no cambia cada 2 segundos, ¡no malgastes tus cuotas!
_cache: dict = {}
CACHE_TTL = 600  # Tiempo de vida del caché: 600 segundos = 10 minutos


def _cache_get(key: str):
    """Lee del caché. Devuelve los datos si aún son válidos, o None si caducaron."""
    if key in _cache:
        data, ts = _cache[key]
        if time.time() - ts < CACHE_TTL:  # ¿Han pasado menos de 10 minutos?
            return data
    return None  # Caché vacío o expirado


def _cache_set(key: str, data):
    """Guarda datos en caché junto con el timestamp actual."""
    _cache[key] = (data, time.time())


# ─── Servicio de Clima ────────────────────────────────────────────────────────

async def get_weather() -> dict:
    """
    Obtiene el clima actual de la ciudad configurada en .env.

    Estrategia de doble fuente:
      1. OpenWeatherMap (preciso, requiere API key)
      2. Fallback: wttr.in    (sin API key, siempre disponible)

    El resultado se guarda en caché por CACHE_TTL segundos.
    """
    # ¿Tenemos un resultado fresco en caché? Si sí, lo devolvemos directamente.
    cached = _cache_get("weather")
    if cached:
        print("[caché] Clima servido desde caché.")
        return cached

    result = None

    # ── Fuente 1: OpenWeatherMap ─────────────────────────────────────────────
    # Solo intentamos si el usuario configuró su API key en el .env
    if OPENWEATHER_API_KEY and OPENWEATHER_API_KEY != "your_api_key_here":
        try:
            url = (
                f"https://api.openweathermap.org/data/2.5/weather"
                f"?q={CITY_NAME}&appid={OPENWEATHER_API_KEY}&units={UNITS}"
            )
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                response.raise_for_status()   # Lanza excepción si status != 2xx
                data = response.json()

                result = {
                    "city":        data["name"],                              # Nombre de la ciudad
                    "temperature": data["main"]["temp"],                     # Temperatura en °C
                    "condition":   data["weather"][0]["description"].capitalize()
                }
                print(f"[OWM] Clima obtenido: {result['temperature']}°C, {result['condition']}")

        except Exception as e:
            print(f"[OWM] Error: {e}. Intentando fallback wttr.in...")

    # ── Fuente 2 (Fallback): wttr.in ─────────────────────────────────────────
    # La API gratuita de wttr.in no requiere registro ni API key.
    # Se usa si OpenWeatherMap falla o no está configurado.
    if not result:
        try:
            url = f"https://wttr.in/{CITY_NAME}?format=j1"
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                response.raise_for_status()
                json_data = response.json()

                # La respuesta de wttr.in tiene la estructura: json["data"]["current_condition"][0]
                current = json_data["data"]["current_condition"][0]
                result = {
                    "city":        CITY_NAME,
                    "temperature": float(current["temp_C"]),
                    "condition":   current["weatherDesc"][0]["value"]
                }
                print(f"[wttr.in] Clima obtenido: {result['temperature']}°C, {result['condition']}")

        except Exception as e:
            print(f"[wttr.in] Error: {e}. Devolviendo valores por defecto.")
            result = {"city": CITY_NAME, "temperature": 0.0, "condition": "Clima no disponible"}

    # Guardar en caché para no volver a llamar a la API en los próximos 10 min
    _cache_set("weather", result)
    return result


# ─── Servicio de Noticias (RSS) ───────────────────────────────────────────────

async def get_real_news() -> list:
    """
    Descarga y parsea noticias de Chile desde un feed RSS.

    Fuente por defecto: Google News Chile (sin API key requerida).
    Configurable via NEWS_RSS_URL en .env.

    El resultado se guarda en caché por CACHE_TTL segundos.
    Retorna una lista de dicts con keys: title, source, url.
    """
    # ¿Tenemos noticias frescas en caché?
    cached = _cache_get("news")
    if cached:
        print(f"[caché] Noticias servidas desde caché ({len(cached)} ítems).")
        return cached

    try:
        # Descargamos el XML del RSS de forma asíncrona con httpx.
        # Google News requiere un User-Agent real para no bloquear el request.
        print(f"[RSS] Descargando noticias desde: {NEWS_RSS_URL}")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                NEWS_RSS_URL,
                headers={"User-Agent": "Mozilla/5.0 (compatible; Aggregator/1.0)"},
                follow_redirects=True
            )
            response.raise_for_status()
            raw_xml = response.text   # El RSS viene en formato XML como texto

        # feedparser convierte el XML en un objeto Python navegable
        feed = feedparser.parse(raw_xml)
        print(f"[RSS] Feed parseado: {len(feed.entries)} entradas encontradas.")

        news_items = []
        # Limitamos a 20 artículos para tener margen de sobra para la paginación
        for entry in feed.entries[:20]:
            # Google News formatea el título como "Titular del artículo - NombreDiario"
            # Separamos para obtener la fuente al final del string
            title  = entry.get("title", "Sin título")
            source = "Google News"

            if " - " in title:
                # rsplit con maxsplit=1 divide solo por el ÚLTIMO " - "
                parts = title.rsplit(" - ", 1)
                title, source = parts[0].strip(), parts[1].strip()

            news_items.append({
                "title":  title,
                "source": source,
                "url":    entry.get("link", "#")
            })

        # Guardar en caché
        _cache_set("news", news_items)
        print(f"[RSS] {len(news_items)} noticias guardadas en caché.")
        return news_items

    except Exception as e:
        print(f"[RSS] Error cargando noticias: {e}")
        # Devolvemos al menos un ítem para no romper el schema de la API
        return [{"title": "Error cargando noticias", "source": "Sistema", "url": "#"}]


# ─── Servicio de Stocks (Yahoo Finance) ──────────────────────────────────────

# Tickers a seguir: IPSA (índice bursátil chileno) + blue chips locales
# Yahoo Finance usa sufijo ".SN" para acciones de la Bolsa de Santiago
STOCK_TICKERS = os.getenv(
    "STOCK_TICKERS",
    "^IPSA,FALABELLA.SN,COPEC.SN,BSANTANDER.SN"
).split(",")


def _fetch_stocks_sync() -> list:
    """
    Función SINCRÓNICA que usa yfinance para obtener cotizaciones.

    yfinance es síncrono por diseño (usa requests internamente),
    por eso la llamamos desde asyncio.to_thread para no bloquear el servidor.
    """
    results = []

    for ticker_symbol in STOCK_TICKERS:
        try:
            # yf.Ticker crea un objeto con toda la info de ese símbolo
            ticker = yf.Ticker(ticker_symbol.strip())

            # fast_info es más rápido que .info — solo trae los campos esenciales
            info = ticker.fast_info

            # Precio actual y precio de cierre anterior para calcular el cambio
            current_price = info.last_price
            prev_close    = info.previous_close

            # Si no hay datos (mercado cerrado, símbolo incorrecto), saltamos
            if current_price is None or prev_close is None:
                print(f"[stocks] Sin datos para {ticker_symbol}, omitiendo.")
                continue

            # Calculamos el cambio porcentual respecto al cierre anterior
            # Fórmula: ((precio_actual - cierre_anterior) / cierre_anterior) * 100
            change_pct = round((current_price - prev_close) / prev_close * 100, 2)

            results.append({
                "symbol": ticker_symbol.strip(),
                "price":  round(float(current_price), 2),
                "change": change_pct    # Positivo = sube, Negativo = baja
            })
            print(f"[stocks] {ticker_symbol}: ${current_price:.2f} ({change_pct:+.2f}%)")

        except Exception as e:
            print(f"[stocks] Error obteniendo {ticker_symbol}: {e}")

    return results


async def get_real_stocks() -> list:
    """
    Versión asíncrona del fetcher de stocks.

    asyncio.to_thread ejecuta la función síncrona _fetch_stocks_sync en un
    thread separado del pool de threads de Python, evitando bloquear el
    event loop de asyncio (que maneja todas las peticiones del servidor).
    """
    cached = _cache_get("stocks")
    if cached:
        print(f"[caché] Stocks servidos desde caché ({len(cached)} tickers).")
        return cached

    print(f"[stocks] Descargando cotizaciones de: {STOCK_TICKERS}")

    # asyncio.to_thread → convierte una función síncrona en una corrutina awaitable
    stocks = await asyncio.to_thread(_fetch_stocks_sync)

    if stocks:  # Solo cacheamos si obtuvimos datos reales
        _cache_set("stocks", stocks)

    return stocks


# ─── Función Agregadora Principal ─────────────────────────────────────────────

async def fetch_unified_data() -> dict:
    """
    Lanza TODAS las peticiones en PARALELO usando asyncio.gather.

    Sin asyncio.gather, haríamos:
        clima    → esperar → noticias → esperar → stocks → esperar  (secuencial)
    Con asyncio.gather:
        clima    ──────────┐
        noticias ──────────┤→ resultado combinado  (paralelo, mucho más rápido)
        stocks   ──────────┘

    Retorna un dict con weather, news y stocks listos para el endpoint.
    """
    print("[aggregator] Iniciando fetch paralelo de datos (clima + noticias + stocks)...")

    # Las tres corrutinas se ejecutan concurrentemente, no una tras otra
    weather, news, stocks = await asyncio.gather(
        get_weather(),
        get_real_news(),
        get_real_stocks()   # ← ¡Ahora los stocks son reales!
    )

    print(
        f"[aggregator] Completado: "
        f"clima={weather['city']}, noticias={len(news)}, stocks={len(stocks)}"
    )

    return {
        "weather": weather,
        "news":    news,
        "stocks":  stocks
    }
