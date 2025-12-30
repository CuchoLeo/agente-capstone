# API Documentation - Agente Capstone

## Base URL

**Desarrollo:** `http://localhost:8000`  
**Producción:** `https://agente-capstone-*****.run.app` (pendiente)

---

## Endpoints

### 1. Página Principal

```http
GET /
```

**Descripción:** Renderiza la interfaz web del asistente conversacional.

**Response:**
- **Content-Type:** `text/html`
- **Status:** 200 OK

**HTML Template:**
- Archivo: `templates/index.html`
- Incluye: Chat UI, quick questions, logo

---

### 2. Chat con el Agente

```http
POST /api/chat
```

**Descripción:** Endpoint principal para conversación con el agente de IA.

**Request Body:**
```json
{
  "message": "¿Cuál es la demanda de apósitos para el Hospital del Salvador?"
}
```

**Response:**
```json
{
  "response": "El Hospital del Salvador tiene una demanda estimada de 205 unidades de apósitos para el próximo mes (enero 2026), con una confianza del 90.2%.",
  "context_used": true
}
```

**Headers:**
```
Content-Type: application/json
```

**Status Codes:**
- `200 OK` - Respuesta exitosa
- `400 Bad Request` - Mensaje vacío
- `500 Internal Server Error` - Error en procesamiento

**Flujo Interno:**
1. Valida que existe `message`
2. Obtiene contexto relevante de BD (`get_context_for_query`)
3. Construye prompt con contexto
4. Envía a Gemini vía Vertex AI
5. Registra consulta en `consultas_copiloto`
6. Retorna respuesta

**Ejemplo cURL:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Qué hospitales tienen mayor demanda de guantes?"
  }'
```

---

### 3. Obtener Predicciones

```http
GET /api/predictions?hospital={hospital}&producto={producto}
```

**Descripción:** Consulta predicciones filtradas por hospital y/o producto.

**Query Parameters:**
- `hospital` (opcional): Nombre del hospital (ej: "Hospital del Salvador")
- `producto` (opcional): Código del producto (ej: "APOSITOS")
- **Nota:** Al menos uno es requerido

**Response:**
```json
[
  {
    "id": 1,
    "hospital": "Hospital del Salvador",
    "producto": "APOSITOS",
    "fecha_prediccion": "2026-01-28",
    "demanda_estimada": 205,
    "confidence_score": 90.2,
    "created_at": "2025-12-29T18:30:00"
  },
  {
    "id": 2,
    "hospital": "Hospital del Salvador",
    "producto": "GUANTES_MEDICOS",
    "fecha_prediccion": "2026-01-28",
    "demanda_estimada": 500,
    "confidence_score": 90.2,
    "created_at": "2025-12-29T18:30:00"
  }
]
```

**Status Codes:**
- `200 OK` - Predicciones encontradas
- `400 Bad Request` - Sin parámetros
- `500 Internal Server Error` - Error en BD

**Ejemplos:**
```bash
# Por hospital
curl "http://localhost:8000/api/predictions?hospital=Hospital%20del%20Salvador"

# Por producto
curl "http://localhost:8000/api/predictions?producto=APOSITOS"

# Combinado
curl "http://localhost:8000/api/predictions?hospital=Hospital%20del%20Salvador&producto=APOSITOS"
```

---

### 4. Listar Hospitales

```http
GET /api/hospitals
```

**Descripción:** Retorna todos los hospitales en el sistema con número de predicciones.

**Response:**
```json
[
  {
    "nombre": "Complejo Asistencial Dr. Sótero del Río",
    "predicciones": 6
  },
  {
    "nombre": "Hospital del Salvador",
    "predicciones": 6
  },
  {
    "nombre": "Hospital Clínico Universidad de Chile",
    "predicciones": 6
  },
  {
    "nombre": "Hospital San José",
    "predicciones": 6
  },
  {
    "nombre": "Hospital Barros Luco-Trudeau",
    "predicciones": 6
  }
]
```

**Status Codes:**
- `200 OK` - Lista retornada
- `500 Internal Server Error` - Error en BD

---

### 5. Listar Productos

```http
GET /api/productos
```

**Descripción:** Retorna catálogo de productos Solventum.

**Response:**
```json
[
  {
    "codigo": "SOL-AP-001",
    "nombre": "Apósito Transparente Tegaderm",
    "categoria": "APOSITOS",
    "descripcion": "Apósito adhesivo transparente impermeable para protección de heridas"
  },
  {
    "codigo": "SOL-AP-002",
    "nombre": "Apósito Espuma Tegaderm",
    "categoria": "APOSITOS",
    "descripcion": "Apósito de espuma absorbente para exudado moderado a alto"
  },
  {
    "codigo": "SOL-GL-001",
    "nombre": "Guantes Látex Estériles",
    "categoria": "GUANTES_MEDICOS",
    "descripcion": "Guantes de látex estériles para procedimientos médicos"
  },
  {
    "codigo": "SOL-GL-002",
    "nombre": "Guantes Nitrilo Sin Polvo",
    "categoria": "GUANTES_MEDICOS",
    "descripcion": "Guantes de nitrilo sin polvo, hipoalergénicos"
  }
]
```

**Status Codes:**
- `200 OK` - Catálogo retornado
- `500 Internal Server Error` - Error en BD

---

### 6. Estadísticas del Sistema

```http
GET /api/stats
```

**Descripción:** Retorna métricas generales del sistema.

**Response:**
```json
{
  "total_predicciones": 42,
  "total_hospitales": 7,
  "total_productos": 4,
  "total_consultas": 15
}
```

**Status Codes:**
- `200 OK` - Estadísticas retornadas
- `500 Internal Server Error` - Error en BD

---

### 7. Health Check

```http
GET /health
```

**Descripción:** Verifica estado del servicio y conexión a BD.

**Response OK:**
```json
{
  "status": "healthy",
  "service": "Agente de Predicción de Demanda - Solventum",
  "vertex_ai": true,
  "database": true
}
```

**Response Error:**
```json
{
  "status": "unhealthy",
  "error": "Connection to PostgreSQL failed"
}
```

**Status Codes:**
- `200 OK` - Servicio saludable
- `500 Internal Server Error` - Servicio con problemas

**Uso:** Ideal para monitoreo automatizado (Kubernetes, Cloud Run)

---

## Configuración de CORS

**Orígenes permitidos:**
```python
CORS_ORIGINS = ["http://localhost:8000", "https://*.run.app"]
```

**Headers permitidos:**
- `Content-Type`
- `Authorization`

---

## Rate Limiting

**Estado actual:** No implementado (desarrollo)

**Recomendaciones para producción:**
```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/api/chat', methods=['POST'])
@limiter.limit("10 per minute")
def chat():
    ...
```

---

## Autenticación

**Estado actual:** No implementado (desarrollo)

**Plan futuro:**
- JWT Tokens
- API Keys para integraciones
- OAuth 2.0 para UI

---

## Errores Comunes

### Error 400: Mensaje Vacío
```json
{
  "error": "Mensaje vacío"
}
```
**Solución:** Incluir `message` en el body del POST

### Error 500: Error en BD
```json
{
  "error": "Connection to database failed"
}
```
**Solución:** Verificar conectividad a PostgreSQL

### Error 500: Vertex AI
```json
{
  "error": "Error procesando consulta: VertexAI API failed"
}
```
**Solución:** Verificar credenciales de GCP y quotas

---

## Logging

Todos los requests se registran en `logs/agente_capstone.log`:

```
2025-12-29 20:30:15 - INFO - Query de usuario default: ¿Demanda de apósitos?
2025-12-29 20:30:17 - INFO - Respuesta generada para default: El Hospital...
```

**Niveles:**
- INFO: Requests normales
- ERROR: Errores de procesamiento
- WARNING: Situaciones anómalas

---

## Testing con Postman/Insomnia

**Collection ejemplo:**

```json
{
  "name": "Agente Capstone API",
  "requests": [
    {
      "name": "Chat Request",
      "method": "POST",
      "url": "http://localhost:8000/api/chat",
      "headers": {"Content-Type": "application/json"},
      "body": {
        "message": "¿Cuál es la demanda de guantes para enero?"
      }
    }
  ]
}
```

---

**Última actualización:** 2025-12-29
