"""
main.py — Punto de Entrada del Gateway Agregador
================================================
Aquí se define la aplicación FastAPI y todos sus endpoints.

FastAPI usa Python's async/await nativamente, lo que permite manejar
miles de peticiones concurrentes sin bloquear el hilo principal.
"""

from fastapi import FastAPI, Query   # FastAPI y Query para parámetros con validación
from schemas import UnifiedFeed      # El schema Pydantic que define la forma de la respuesta
from services import fetch_unified_data  # La función que agrega todos los datos

# ─── Instancia de la Aplicación ──────────────────────────────────────────────
# FastAPI genera automáticamente documentación interactiva en:
#   /docs  → Swagger UI (interfaz gráfica)
#   /redoc → ReDoc (versión alternativa)
app = FastAPI(
    title="Gateway-Aggregator",
    description="Middleware que agrega clima, noticias y stocks en una sola llamada.",
    version="1.0.0"
)


# ─── Endpoint Principal: /v1/feed ─────────────────────────────────────────────
@app.get("/v1/feed", response_model=UnifiedFeed)
async def get_feed(
    page:  int = Query(default=1, ge=1, description="Número de página (empieza en 1)"),
    limit: int = Query(default=5, ge=1, le=50, description="Artículos por página (máx. 50)")
):
    """
    Endpoint unificado: devuelve clima + noticias paginadas + stocks.

    Parámetros de paginación (aplicados a las noticias):
    - **page**: Qué página quieres ver. Default: 1.
    - **limit**: Cuántos artículos por página. Default: 5, máximo: 50.

    Ejemplos:
    -  `/v1/feed`             → página 1, 5 noticias
    -  `/v1/feed?page=2&limit=3` → página 2, 3 noticias
    """

    # Obtenemos TODOS los datos (clima + noticias completas + stocks)
    # fetch_unified_data hace las llamadas en paralelo internamente
    data = await fetch_unified_data()

    # ── Paginación de Noticias ────────────────────────────────────────────────
    # Calculamos el slice (trozo) del array de noticias que corresponde a esta página.
    # Ejemplo con page=2, limit=5:
    #   start = (2-1) * 5 = 5   → empezamos desde el índice 5
    #   end   =  2    * 5 = 10  → terminamos en el índice 10 (no incluido)
    #   → noticias[5:10] = artículos del 6 al 10
    start = (page - 1) * limit
    end   = start + limit
    data["news"] = data["news"][start:end]   # Slicing nativo de Python

    return data


# ─── Ejecución Directa ────────────────────────────────────────────────────────
# Este bloque solo se ejecuta cuando corres `python main.py` directamente.
# No se ejecuta cuando uvicorn importa el módulo (que es lo normal en producción).
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
