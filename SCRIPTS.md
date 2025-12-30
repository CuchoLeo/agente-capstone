# Scripts de Gestión del Sistema

## Scripts Disponibles

### 🚀 `start.sh` - Iniciar el servidor

Inicia el servidor Flask en background y guarda los logs.

```bash
./start.sh
```

**Funcionalidades:**
- Verifica que existe `app.py` y `.env`
- Activa el ambiente conda `agente` automáticamente
- Verifica que el puerto 8080 esté disponible
- Inicia el servidor en background
- Guarda el PID en `.server.pid`
- Redirige logs a `logs/app.log`

**Salida exitosa:**
```
🚀 Iniciando Asistente de Demanda Médica...
🔧 Activando ambiente conda 'agente'...
✅ Iniciando servidor...
✅ Servidor iniciado exitosamente
   PID: 12345
   URL: http://127.0.0.1:8080
   Logs: logs/app.log
```

---

### 🛑 `stop.sh` - Detener el servidor

Detiene el servidor de forma segura usando múltiples métodos.

```bash
./stop.sh
```

**Métodos de detención:**
1. Usa el PID guardado en `.server.pid`
2. Busca procesos por nombre `python app.py`
3. Busca procesos usando el puerto 8080

**Salida exitosa:**
```
🛑 Deteniendo Asistente de Demanda Médica...
   Deteniendo proceso con PID: 12345
✅ Servidor detenido exitosamente
```

---

### 🔄 `restart.sh` - Reiniciar el servidor

Reinicia el servidor ejecutando `stop.sh` y luego `start.sh`.

```bash
./restart.sh
```

**Uso típico:** Después de cambios en el código o configuración.

---

### 📊 `status.sh` - Verificar estado

Muestra información detallada sobre el estado del servidor.

```bash
./status.sh
```

**Información mostrada:**
- Estado del servidor (corriendo/detenido)
- PID del proceso
- Uso de CPU y RAM
- Estado del puerto 8080
- Configuración de archivos
- Últimas 5 líneas del log

**Ejemplo de salida:**
```
📊 Estado del Asistente de Demanda Médica
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Estado: ✅ CORRIENDO
PID: 12345
CPU/RAM:  2.1  0.8
Puerto: 8080 (activo)
URL: http://127.0.0.1:8080
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Flujo de Trabajo Recomendado

### Primer uso
```bash
# 1. Asegúrate de tener configurado .env
cp .env.example .env
# Edita .env con tus credenciales

# 2. Inicia el servidor
./start.sh

# 3. Verifica que esté corriendo
./status.sh
```

### Desarrollo diario
```bash
# Ver estado
./status.sh

# Reiniciar después de cambios
./restart.sh

# Ver logs en tiempo real
tail -f logs/app.log

# Detener al finalizar
./stop.sh
```

### Debugging
```bash
# Ver logs completos
cat logs/app.log

# Ver solo errores
grep -i error logs/app.log

# Limpiar logs
rm logs/app.log

# Reiniciar desde cero
./stop.sh && ./start.sh
```

---

## Archivos Generados

- `.server.pid` - Almacena el PID del servidor corriendo
- `logs/app.log` - Logs del servidor (stdout y stderr)
- `logs/` - Directorio creado automáticamente

---

## Troubleshooting

### Puerto ya en uso
```bash
# Verificar qué proceso usa el puerto
lsof -i :8080

# Detener con el script
./stop.sh

# O manualmente
kill $(lsof -ti :8080)
```

### El servidor no inicia
```bash
# Revisar logs
cat logs/app.log

# Verificar ambiente conda
conda env list

# Verificar .env
cat .env
```

### Scripts no ejecutables
```bash
chmod +x start.sh stop.sh restart.sh status.sh
```
