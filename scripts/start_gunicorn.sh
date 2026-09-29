#!/bin/bash

# Script para iniciar el gestor de lotes con Gunicorn (producción)
# Uso: ./scripts/start_gunicorn.sh

# Ejecutar desde la raíz del proyecto (donde están app.py y gunicorn_config.py)
cd "$(dirname "$0")/.." || exit 1

echo "🚀 Iniciando Gestor de Lotes con Gunicorn"
echo "=================================================="
echo ""

# Verificar que gunicorn esté instalado
if ! command -v gunicorn &> /dev/null; then
    echo "⚠️  Gunicorn no instalado. Instalando..."
    pip install gunicorn==21.2.0
fi

# Variables de entorno (MONGO_URI, MONGO_DB, etc. se leen de .env desde db.py)
export GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"

echo "📊 Configuración:"
echo "   - Workers: $GUNICORN_WORKERS"
echo "   - Bind: ${BIND_ADDRESS:-0.0.0.0:5000}"
echo ""

# Iniciar con Gunicorn
echo "🔥 Iniciando Gunicorn..."
gunicorn -c gunicorn_config.py app:app

# Si falla, mostrar ayuda
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Error al iniciar Gunicorn"
    echo ""
    echo "Alternativas:"
    echo "  1. Modo desarrollo (1 solo núcleo):"
    echo "     python app.py"
    echo ""
    echo "  2. Gunicorn manual:"
    echo "     gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 app:app"
    echo ""
fi
