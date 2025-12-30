#!/bin/bash
# Script para verificar el estado del Asistente de Demanda Médica

# Colores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}📊 Estado del Asistente de Demanda Médica${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verificar proceso por PID guardado
if [ -f ".server.pid" ]; then
    PID=$(cat .server.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "Estado: ${GREEN}✅ CORRIENDO${NC}"
        echo "PID: $PID"
        
        # Obtener información del proceso
        CPU_MEM=$(ps -p $PID -o %cpu,%mem | tail -n 1)
        echo "CPU/RAM: $CPU_MEM"
        
        # Verificar puerto
        if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null ; then
            echo -e "Puerto: ${GREEN}8080 (activo)${NC}"
            echo "URL: http://127.0.0.1:8080"
        else
            echo -e "Puerto: ${RED}8080 (no disponible)${NC}"
        fi
    else
        echo -e "Estado: ${RED}❌ DETENIDO${NC}"
        echo "   (PID inválido en .server.pid)"
        rm -f .server.pid
    fi
else
    # Buscar proceso manualmente
    PIDS=$(pgrep -f "python app.py")
    if [ -n "$PIDS" ]; then
        echo -e "Estado: ${YELLOW}⚠️  CORRIENDO (sin PID guardado)${NC}"
        echo "PIDs encontrados: $PIDS"
    else
        echo -e "Estado: ${RED}❌ DETENIDO${NC}"
    fi
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Información adicional
echo ""
echo "Archivos de configuración:"
if [ -f ".env" ]; then
    echo -e "  .env: ${GREEN}✓${NC}"
else
    echo -e "  .env: ${RED}✗${NC}"
fi

if [ -f "app.py" ]; then
    echo -e "  app.py: ${GREEN}✓${NC}"
else
    echo -e "  app.py: ${RED}✗${NC}"
fi

# Mostrar logs recientes si existen
if [ -f "logs/app.log" ]; then
    echo ""
    echo "Últimas 5 líneas del log:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    tail -n 5 logs/app.log
fi
