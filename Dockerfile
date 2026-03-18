# ════════════════════════════════════════════════════════════════════════════════
# Dockerfile para Google Cloud Run - Optimizado para FastAPI
# ════════════════════════════════════════════════════════════════════════════════
# Imagen base: python:3.11-slim (~150MB)
#   - Incluye Python 3.11 y herramientas esenciales
#   - Excluye dev tools → tamaño menor y menos vulnerabilidades
FROM python:3.11-slim

# ─── Variables de Entorno para Optimización ──────────────────────────────────
# PYTHONDONTWRITEBYTECODE: Evita que Python genere archivos .pyc
#   - Reduce tamaño de imagen en ~10%
#   - En Cloud Run el código es de solo lectura de todas formas
ENV PYTHONDONTWRITEBYTECODE=1

# PYTHONUNBUFFERED: Logs en tiempo real (sin buffering)
#   - Crítico para ver logs en tiempo real en Cloud Run
#   - Sin esto, verías logs con retraso
ENV PYTHONUNBUFFERED=1

# ─── Directorio de Trabajo ──────────────────────────────────────────────────
WORKDIR /app

# ─── Instalación de Dependencias (Layer separada para caché de Docker) ──────
# Se copia SOLO requirements.txt primero para aprovechar el cache de Docker.
# Si solo cambian tus archivos .py, Docker no rebuilda las dependencias.
COPY requirements.txt .

# Instalar dependencias de Python
#   --no-cache-dir: No guarda archivos temporales → menos espacio
#   -q (quiet): Menos output verbose
RUN pip install --no-cache-dir -q -r requirements.txt

# ─── Copiar Código Fuente ───────────────────────────────────────────────────
# Esto se copia DESPUÉS de instalar dependencias, porque cambia frecuentemente.
# Así Docker aprovecha el cache de la capa anterior (dependencias).
COPY . .

# ─── Puerto y Health Check ──────────────────────────────────────────────────
# Cloud Run automáticamente inyecta la variable de entorno PORT
# La aplicación debe escuchar en 0.0.0.0 para recibir peticiones
EXPOSE 8080

# ─── Comando de Inicio ───────────────────────────────────────────────────────
# Uvicorn es el servidor ASGI recomendado para FastAPI
#   --host 0.0.0.0: Escucha en todas las interfaces de red
#   --port ${PORT:-8080}: Lee PORT de entorno, fallback a 8080 si no existe
#   main:app: Módulo:variable que contiene la instancia de FastAPI
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
