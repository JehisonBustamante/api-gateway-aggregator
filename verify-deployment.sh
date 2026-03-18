#!/bin/bash
# ════════════════════════════════════════════════════════════════════════════════
# Pre-Despliegue Verification Checklist
# Ejecuta este script antes de desplegar a Google Cloud Run
#
# Uso: bash verify-deployment.sh
# ════════════════════════════════════════════════════════════════════════════════

set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🔍 PRE-DESPLIEGUE VERIFICATION CHECKLIST"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0
WARNINGS=0

# Helper function to check file
check_file() {
    local filename=$1
    local description=$2

    if [ -f "$filename" ]; then
        echo -e "${GREEN}✅${NC} $description exists"
        ((PASSED++))
    else
        echo -e "${RED}❌${NC} $description NOT found: $filename"
        ((FAILED++))
    fi
}

# Helper function to check string in file
check_content() {
    local filename=$1
    local search_string=$2
    local description=$3

    if grep -q "$search_string" "$filename" 2>/dev/null; then
        echo -e "${GREEN}✅${NC} $description"
        ((PASSED++))
    else
        echo -e "${RED}❌${NC} $description NOT found in $filename"
        ((FAILED++))
    fi
}

# Helper function for warnings
warn() {
    local description=$1
    echo -e "${YELLOW}⚠️${NC}  $description"
    ((WARNINGS++))
}

# 1. Check Files Exist
echo -e "${BLUE}📁 Archivos Requeridos${NC}"
echo "─────────────────────────────────────────────────────────────────────────────"
check_file "Dockerfile" "Dockerfile"
check_file "main.py" "main.py"
check_file "requirements.txt" "requirements.txt"
check_file "schemas.py" "schemas.py"
check_file "services.py" "services.py"
check_file ".dockerignore" ".dockerignore"
echo ""

# 2. Check Dockerfile Content
echo -e "${BLUE}🐳 Dockerfile Validación${NC}"
echo "─────────────────────────────────────────────────────────────────────────────"
check_content "Dockerfile" "python:3.11-slim" "Usa imagen slim"
check_content "Dockerfile" "PYTHONDONTWRITEBYTECODE" "PYTHONDONTWRITEBYTECODE configurado"
check_content "Dockerfile" "PYTHONUNBUFFERED" "PYTHONUNBUFFERED configurado"
check_content "Dockerfile" "0.0.0.0" "Host configurado en 0.0.0.0"
check_content "Dockerfile" "PORT" "Puerto dinámico (PORT variable)"
check_content "Dockerfile" "pip install.*--no-cache-dir" "Usa --no-cache-dir en pip"
echo ""

# 3. Check main.py Content
echo -e "${BLUE}🔧 main.py Validación${NC}"
echo "─────────────────────────────────────────────────────────────────────────────"
check_content "main.py" "import os" "Importa 'os' module"
check_content "main.py" "RedirectResponse" "Usa RedirectResponse"
check_content "main.py" "CORSMiddleware" "Usa CORSMiddleware"
check_content "main.py" "@app.get" "Tiene endpoints FastAPI"
check_content "main.py" "def root" "Tiene endpoint raíz"
check_content "main.py" "def health_check" "Tiene health check"
check_content "main.py" "os.environ.get.*PORT" "Lee PORT de ambiente"
check_content "main.py" "host=.0.0.0.0" "Host en 0.0.0.0"
echo ""

# 4. Check requirements.txt
echo -e "${BLUE}📦 requirements.txt Validación${NC}"
echo "─────────────────────────────────────────────────────────────────────────────"
check_content "requirements.txt" "fastapi" "FastAPI en requirements"
check_content "requirements.txt" "uvicorn" "Uvicorn en requirements"
check_content "requirements.txt" "httpx" "httpx en requirements"
echo ""

# 5. Optional Checks
echo -e "${BLUE}🌟 Verificaciones Adicionales${NC}"
echo "─────────────────────────────────────────────────────────────────────────────"

# Check .gcloudignore
if [ -f ".gcloudignore" ]; then
    echo -e "${GREEN}✅${NC} .gcloudignore existe (optimizará Cloud Build)"
else
    warn ".gcloudignore no encontrado (opcional pero recomendado)"
fi

# Check deploy.sh
if [ -f "deploy.sh" ]; then
    echo -e "${GREEN}✅${NC} deploy.sh existe (script de despliegue)"
else
    warn "deploy.sh no encontrado (puedes desplegar manualmente)"
fi

# Check if .env exists (should warn)
if [ -f ".env" ]; then
    warn ".env existe - Asegúrate de que NO esté en .git"
fi

echo ""

# 6. Docker availability check
echo -e "${BLUE}🐳 Docker Check${NC}"
echo "─────────────────────────────────────────────────────────────────────────────"

if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅${NC} Docker está instalado"
    ((PASSED++))

    # Try to build
    echo "   Intentando build local..."
    if docker build -t test-build . > /dev/null 2>&1; then
        echo -e "${GREEN}✅${NC} Docker build exitoso"
        ((PASSED++))

        # Get image size
        SIZE=$(docker images test-build --format "{{.Size}}")
        echo "   Tamaño de imagen: $SIZE"
    else
        echo -e "${RED}❌${NC} Docker build falló"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⚠️${NC}  Docker no encontrado - instálalo desde docker.com"
    ((WARNINGS++))
fi

echo ""

# 7. GCloud CLI check
echo -e "${BLUE}☁️  Google Cloud CLI Check${NC}"
echo "─────────────────────────────────────────────────────────────────────────────"

if command -v gcloud &> /dev/null; then
    echo -e "${GREEN}✅${NC} gcloud CLI está instalado"
    ((PASSED++))

    # Check authentication
    if gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null | grep -q "@"; then
        ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format='value(account)')
        echo -e "${GREEN}✅${NC} Autenticado como: $ACCOUNT"
        ((PASSED++))
    else
        warn "No hay sesión activa en gcloud. Ejecuta: gcloud auth login"
    fi

    # Check project
    PROJECT=$(gcloud config get-value project 2>/dev/null)
    if [ -n "$PROJECT" ]; then
        echo -e "${GREEN}✅${NC} Proyecto configurado: $PROJECT"
        ((PASSED++))
    else
        warn "No hay proyecto configurado. Ejecuta: gcloud config set project TU_PROYECTO"
    fi
else
    warn "gcloud CLI no encontrado - descárgalo desde cloud.google.com/sdk"
fi

echo ""

# 8. Summary
echo "════════════════════════════════════════════════════════════════════════════════"
echo "📊 RESUMEN"
echo "════════════════════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Pasados:${NC} $PASSED"
echo -e "${RED}❌ Fallos:${NC} $FAILED"
echo -e "${YELLOW}⚠️  Advertencias:${NC} $WARNINGS"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ¡Todo listo! Puedes proceder con el despliegue.${NC}"
    echo ""
    echo "Próximos pasos:"
    echo "  1. Local test:    docker run -p 8080:8080 $(docker images test-build --format '{{.ID}}' | head -c 12)"
    echo "  2. Push to GCR:   docker tag api-gateway-aggregator gcr.io/TU_PROYECTO/api-gateway-aggregator:latest"
    echo "  3. Desplegar:     bash deploy.sh api-gateway-aggregator us-central1 TU_PROYECTO"
    exit 0
else
    echo -e "${RED}⚠️  Hay errores que corregir antes de desplegar.${NC}"
    exit 1
fi

