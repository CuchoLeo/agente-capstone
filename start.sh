#!/bin/bash
# Script para iniciar el Asistente de Demanda Médica

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Iniciando Asistente de Demanda Médica...${NC}"

# Verificar que estamos en el directorio correcto
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py no encontrado. Ejecuta este script desde el directorio del proyecto."
    exit 1
fi

# Verificar que existe el archivo .env
if [ ! -f ".env" ]; then
    echo "⚠️  Advertencia: archivo .env no encontrado. Copiando desde .env.example"
    cp .env.example .env
    echo "📝 Por favor configura tus credenciales en .env antes de continuar"
    exit 1
fi

# Activar ambiente conda si está disponible
if command -v conda &> /dev/null; then
    echo "🔧 Activando ambiente conda 'agente'..."
    eval "$(conda shell.bash hook)"
    conda activate agente 2>/dev/null || echo "⚠️  No se pudo activar ambiente 'agente'"
fi

# Verificar si ya está corriendo
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  El servidor ya está corriendo en el puerto 8080"
    echo "   Usa ./stop.sh para detenerlo primero"
    exit 1
fi

# Crear directorio para logs si no existe
mkdir -p logs

# Iniciar el servidor en background
echo -e "${GREEN}✅ Iniciando servidor...${NC}"
nohup python app.py > logs/app.log 2>&1 &
SERVER_PID=$!

# Guardar PID en archivo
echo $SERVER_PID > .server.pid

# Esperar un momento para verificar que inició correctamente
sleep 2

# Verificar que el proceso sigue corriendo
if ps -p $SERVER_PID > /dev/null; then
    echo -e "${GREEN}✅ Servidor iniciado exitosamente${NC}"
    echo -e "   PID: $SERVER_PID"
    echo -e "   URL: ${BLUE}http://127.0.0.1:8080${NC}"
    echo -e "   Logs: logs/app.log"
    echo -e "\n📊 Para ver los logs en tiempo real:"
    echo -e "   tail -f logs/app.log"
    echo -e "\n🛑 Para detener el servidor:"
    echo -e "   ./stop.sh"
else
    echo "❌ Error: El servidor no pudo iniciarse"
    echo "   Revisa los logs en logs/app.log para más detalles"
    rm -f .server.pid
    exit 1
fi
