#!/bin/bash
# ════════════════════════════════════════════════════════════════════════════════
# Script de Despliegue a Google Cloud Run
# ════════════════════════════════════════════════════════════════════════════════
# Uso: bash deploy.sh <nombre-servicio> <región> [proyecto-gcp]
# Ejemplo: bash deploy.sh api-gateway-aggregator us-central1 mi-proyecto-gcp
# ════════════════════════════════════════════════════════════════════════════════

set -e  # Detener si hay error

# ─── Validar Parámetros ─────────────────────────────────────────────────────
SERVICE_NAME=${1:-api-gateway-aggregator}
REGION=${2:-us-central1}
PROJECT_ID=${3}

if [ -z "$PROJECT_ID" ]; then
    # Intentar obtener del proyecto actual de gcloud
    PROJECT_ID=$(gcloud config get-value project)
    if [ -z "$PROJECT_ID" ]; then
        echo "❌ Error: Especifica el PROJECT_ID como tercer parámetro"
        echo "Uso: bash deploy.sh <servicio> <región> <proyecto>"
        exit 1
    fi
fi

echo "🚀 Iniciando despliegue a Google Cloud Run"
echo "   Servicio: $SERVICE_NAME"
echo "   Región: $REGION"
echo "   Proyecto: $PROJECT_ID"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ─── 1. Validar autenticación ────────────────────────────────────────────────
echo "✓ Validando autenticación..."
gcloud auth list --filter=status:ACTIVE --format='value(account)' > /dev/null 2>&1 || {
    echo "❌ No hay cuenta autenticada. Ejecuta: gcloud auth login"
    exit 1
}

# ─── 2. Construir imagen Docker ──────────────────────────────────────────────
echo "✓ Construyendo imagen Docker..."
IMAGE_URL="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
docker build -t "${IMAGE_URL}:latest" .

echo "✓ Imagen construida: ${IMAGE_URL}:latest"
echo "   Tamaño: $(docker images --format '{{.Size}}' "${IMAGE_URL}:latest")"

# ─── 3. Subir imagen a Google Container Registry ─────────────────────────────
echo "✓ Subiendo imagen a Google Container Registry..."
docker push "${IMAGE_URL}:latest"

# ─── 4. Desplegar a Cloud Run ────────────────────────────────────────────────
echo "✓ Desplegando a Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image="${IMAGE_URL}:latest" \
    --platform=managed \
    --region="$REGION" \
    --allow-unauthenticated \
    --port=8080 \
    --memory=512Mi \
    --cpu=1 \
    --timeout=60s \
    --project="$PROJECT_ID"

# ─── 5. Obtener URL del servicio ────────────────────────────────────────────
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --platform=managed \
    --region="$REGION" \
    --format='value(status.url)' \
    --project="$PROJECT_ID")

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ¡Despliegue completado exitosamente!"
echo ""
echo "📍 URL del Servicio:"
echo "   ${SERVICE_URL}"
echo ""
echo "🔗 Endpoints:"
echo "   Raíz → ${SERVICE_URL}/"
echo "   Swagger → ${SERVICE_URL}/docs"
echo "   Health Check → ${SERVICE_URL}/health"
echo "   API → ${SERVICE_URL}/v1/feed"
echo ""
echo "🔍 Comandos útiles:"
echo "   Ver logs: gcloud run logs read $SERVICE_NAME --limit 50 --region=$REGION"
echo "   Ver detalles: gcloud run services describe $SERVICE_NAME --region=$REGION"
echo "   Ejecutar localmente: docker run -p 8080:8080 ${IMAGE_URL}:latest"
echo ""
echo "🧪 Prueba rápida:"
echo "   curl ${SERVICE_URL}/health"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

