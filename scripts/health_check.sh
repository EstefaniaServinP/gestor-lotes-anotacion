#!/bin/bash
# Health check: verifica MongoDB, las colecciones principales y la aplicación.
# Uso: ./scripts/health_check.sh   (lee MONGO_URI, MONGO_DB y PORT desde .env si existe)
set -uo pipefail

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Cargar .env sin sobrescribir variables ya definidas (igual que python-dotenv)
if [ -f "${ROOT}/.env" ]; then
    while IFS='=' read -r key value; do
        [[ "$key" =~ ^[A-Z_][A-Z0-9_]*$ ]] || continue
        [ -z "${!key:-}" ] && export "$key=$value"
    done < "${ROOT}/.env"
fi

MONGO_URI="${MONGO_URI:-mongodb://localhost:27017}"
MONGO_DB="${MONGO_DB:-planta_a}"
APP_URL="http://localhost:${PORT:-5000}"

check_passed=0
check_failed=0

run_check() {
    local name=$1
    local command=$2

    echo -n -e "${YELLOW}[CHECK]${NC} ${name}... "

    if eval "$command" &>/dev/null; then
        echo -e "${GREEN}✓ PASS${NC}"
        check_passed=$((check_passed + 1))
    else
        echo -e "${RED}✗ FAIL${NC}"
        check_failed=$((check_failed + 1))
    fi
}

echo -e "${BLUE}═══ 1. MONGODB (${MONGO_URI}) ═══${NC}\n"

run_check "Ping a MongoDB" "mongosh '${MONGO_URI}' --quiet --eval 'db.adminCommand(\"ping\")'"
run_check "Colección '${MONGO_DB}.batches' existe" "mongosh '${MONGO_URI}' --quiet --eval 'db.getSiblingDB(\"${MONGO_DB}\").getCollectionNames()' | grep -q batches"
run_check "Colección '${MONGO_DB}.segmentadores' existe" "mongosh '${MONGO_URI}' --quiet --eval 'db.getSiblingDB(\"${MONGO_DB}\").getCollectionNames()' | grep -q segmentadores"

echo -e "\n${BLUE}═══ 2. APLICACIÓN (${APP_URL}) ═══${NC}\n"

run_check "GET /api/batches responde 200" "curl -fsS '${APP_URL}/api/batches'"

echo -e "\n${BLUE}═══ 3. RESUMEN ═══${NC}\n"

echo -e "${GREEN}✓ Checks pasados:${NC} ${check_passed}"
echo -e "${RED}✗ Checks fallidos:${NC} ${check_failed}"

if [ $check_failed -eq 0 ]; then
    echo -e "\n${GREEN}✓ Todo listo${NC}\n"
    exit 0
else
    echo -e "\n${YELLOW}Troubleshooting:${NC}"
    echo -e "  1. MongoDB: ${BLUE}sudo systemctl status mongod${NC}"
    echo -e "  2. Inicializar BD: ${BLUE}python scripts/init_db.py && python scripts/load_batches.py${NC}"
    echo -e "  3. Aplicación: ${BLUE}python app.py${NC}\n"
    exit 1
fi
