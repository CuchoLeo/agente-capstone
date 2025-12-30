#!/bin/bash
# Script para detener el Asistente de Demanda Médica

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🛑 Deteniendo Asistente de Demanda Médica...${NC}"

# Método 1: Usar el PID guardado
if [ -f ".server.pid" ]; then
    PID=$(cat .server.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "   Deteniendo proceso con PID: $PID"
        kill $PID
        sleep 1
        
        # Verificar si se detuvo
        if ps -p $PID > /dev/null 2>&1; then
            echo "   Proceso aún corriendo, forzando detención..."
            kill -9 $PID
        fi
        
        rm -f .server.pid
        echo -e "${GREEN}✅ Servidor detenido exitosamente${NC}"
        exit 0
    else
        echo "⚠️  El PID guardado ($PID) no corresponde a un proceso activo"
        rm -f .server.pid
    fi
fi

# Método 2: Buscar por nombre de proceso
PIDS=$(pgrep -f "python app.py")
if [ -n "$PIDS" ]; then
    echo "   Encontrados procesos: $PIDS"
    kill $PIDS
    sleep 1
    
    # Verificar y forzar si es necesario
    REMAINING=$(pgrep -f "python app.py")
    if [ -n "$REMAINING" ]; then
        echo "   Forzando detención de procesos restantes..."
        pkill -9 -f "python app.py"
    fi
    
    echo -e "${GREEN}✅ Servidor detenido exitosamente${NC}"
    exit 0
fi

# Método 3: Buscar por puerto
PORT_PID=$(lsof -ti:8080)
if [ -n "$PORT_PID" ]; then
    echo "   Encontrado proceso usando puerto 8080: $PORT_PID"
    kill $PORT_PID
    sleep 1
    
    # Verificar y forzar si es necesario
    if lsof -ti:8080 > /dev/null; then
        echo "   Forzando detención..."
        kill -9 $PORT_PID
    fi
    
    echo -e "${GREEN}✅ Servidor detenido exitosamente${NC}"
    exit 0
fi

echo -e "${RED}ℹ️  No se encontró ningún servidor corriendo${NC}"
