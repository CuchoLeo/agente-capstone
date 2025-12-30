#!/bin/bash
# Script para reiniciar el Asistente de Demanda Médica

# Colores para output
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Reiniciando Asistente de Demanda Médica...${NC}"
echo ""

# Verificar que los scripts existen
if [ ! -f "stop.sh" ] || [ ! -f "start.sh" ]; then
    echo "❌ Error: Scripts stop.sh o start.sh no encontrados"
    exit 1
fi

# Detener el servidor
./stop.sh

# Esperar un momento
echo ""
echo "⏳ Esperando 3 segundos..."
sleep 3
echo ""

# Iniciar el servidor
./start.sh
