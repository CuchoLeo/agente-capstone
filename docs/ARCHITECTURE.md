# Arquitectura del Sistema - Agente Capstone

## Visión General

Sistema de inteligencia artificial que predice la demanda hospitalaria de insumos médicos en Chile, combinando un modelo predictivo de Machine Learning con un asistente conversacional basado en Gemini.

---

## Diagrama de Arquitectura General

```mermaid
graph TB
    subgraph "Cliente"
        UI[Interfaz Web<br/>HTML/CSS/JS]
    end
    
    subgraph "Backend - Flask Application"
        API[API REST<br/>Flask 3.0]
        Agent[Gemini Agent<br/>Vertex AI]
        Context[Context Retrieval<br/>get_context_for_query]
        Predictor[DemandPredictor<br/>Regresión Lineal]
    end
    
    subgraph "Datos Persistentes"
        DB[(PostgreSQL<br/>AWS RDS<br/>us-east-2)]
        Models[Modelos Entrenados<br/>demand_model.pkl]
    end
    
    subgraph "Servicios Externos"
        VertexAI[Google Vertex AI<br/>Gemini 1.5 Flash]
    end
    
    UI -->|HTTP Request| API
    API -->|Consulta Usuario| Context
    Context -->|Query Predicciones| DB
    Context -->|Retorna Contexto| Agent
    Agent -->|LLM Request| VertexAI
    VertexAI -->|Respuesta| Agent
    Agent -->|Respuesta NL| API
    API -->|JSON Response| UI
    
    Predictor -->|Carga Modelo| Models
    Predictor -->|Lee Históricos| DB
    Predictor -->|Guarda Predicciones| DB
    
    style UI fill:#e1f5ff
    style API fill:#fff3e0
    style Agent fill:#f3e5f5
    style DB fill:#e8f5e9
    style VertexAI fill:#fce4ec
```

---

## Flujo de Datos: Consulta del Usuario

```mermaid
sequenceDiagram
    actor User
    participant Web as Interfaz Web
    participant Flask as Flask API
    participant Context as Context Builder
    participant DB as PostgreSQL
    participant Gemini as Gemini Agent
    participant VertexAI as Vertex AI
    
    User->>Web: "¿Demanda de apósitos<br/>en Hospital Salvador?"
    Web->>Flask: POST /api/chat
    Flask->>Context: get_context_for_query()
    
    Context->>DB: SELECT * FROM predicciones_demanda<br/>WHERE hospital LIKE '%Salvador%'
    DB-->>Context: 10 registros de predicciones
    
    Context->>DB: SELECT DISTINCT hospital<br/>FROM predicciones_demanda
    DB-->>Context: Lista de hospitales
    
    Context-->>Flask: Contexto estructurado
    
    Flask->>Gemini: send_message(prompt + contexto)
    Gemini->>VertexAI: GenerativeModel.generate_content()
    VertexAI-->>Gemini: Respuesta generada
    Gemini-->>Flask: Texto en lenguaje natural
    
    Flask->>DB: INSERT INTO consultas_copiloto<br/>(usuario, consulta, respuesta)
    
    Flask-->>Web: JSON: {response: "...", context_used: true}
    Web-->>User: "El Hospital del Salvador<br/>necesitará 205 unidades..."
```

---

## Pipeline del Modelo Predictivo

```mermaid
flowchart TB
    start([Inicio: Entrenamiento]) --> load[Cargar Datos Históricos<br/>ordenes_compra]
    
    load --> feature[Feature Engineering]
    
    subgraph "Feature Engineering"
        feat1[Tendencia Temporal<br/>días desde 2024-01-01]
        feat2[Estacionalidad<br/>mes_sin, mes_cos]
        feat3[Hospital<br/>One-Hot Encoding]
        feat4[Producto<br/>One-Hot Encoding]
    end
    
    feature --> split[Train/Test Split<br/>80% / 20%]
    
    split --> train[Entrenar Modelo<br/>LinearRegression]
    
    train --> eval{Evaluar Métricas}
    
    eval -->|R² >= 0.5| save[Guardar Modelo<br/>models/demand_model.pkl]
    eval -->|R² < 0.5| warn[⚠️ Warning:<br/>Bajo Performance]
    
    warn --> save
    
    save --> predict[Generar Predicciones<br/>Próximos 3 meses]
    
    predict --> insert[Insertar en BD<br/>predicciones_demanda]
    
    insert --> finish([Fin])
    
    style start fill:#e8f5e9
    style finish fill:#e8f5e9
    style eval fill:#fff3e0
    style save fill:#e1f5ff
    style warn fill:#ffebee
```

---

## Diagrama de Entidad-Relación (ERD)

```mermaid
erDiagram
    ordenes_compra ||--o{ predicciones_demanda : "entrena modelo"
    productos_solventum ||--o{ predicciones_demanda : "categoriza"
    consultas_copiloto }o--|| predicciones_demanda : "consulta"
    
    ordenes_compra {
        int id PK
        string orden_id UK "Código único de orden"
        date fecha_orden "Fecha de la orden"
        string nombre_organismo "Hospital o institución"
        text descripcion_item "Descripción libre del producto"
        string producto_estandarizado "APOSITOS, GUANTES_MEDICOS"
        int cantidad "Unidades compradas"
        string unidad_medida "UNIDADES, CAJAS"
        decimal monto_total "Precio total en CLP"
        timestamp created_at
        timestamp updated_at
    }
    
    predicciones_demanda {
        int id PK
        string hospital "Nombre del hospital"
        string producto "APOSITOS, GUANTES_MEDICOS"
        date fecha_prediccion "Fecha de la predicción"
        int demanda_estimada "Unidades estimadas"
        decimal confidence_score "Score 0-100%"
        timestamp created_at
    }
    
    productos_solventum {
        int id PK
        string codigo_producto UK "Código SKU"
        string nombre_producto "Nombre comercial"
        string categoria "APOSITOS, GUANTES_MEDICOS"
        text descripcion "Descripción técnica"
        text_array palabras_clave "Keywords para búsqueda"
        timestamp created_at
    }
    
    consultas_copiloto {
        int id PK
        string usuario "ID del usuario"
        text consulta "Pregunta original"
        text respuesta "Respuesta del agente"
        timestamp timestamp
    }
```

---

## Componentes del Sistema

### 1. Interfaz Web (Frontend)

**Tecnología:** HTML5, CSS3, JavaScript (Vanilla)

**Responsabilidades:**
- Renderizar chat UI
- Capturar input del usuario
- Enviar requests a API
- Mostrar respuestas del agente

**Archivos:**
- `templates/index.html`
- `static/css/styles.css`
- `static/js/app.js`

---

### 2. API REST (Backend)

**Tecnología:** Flask 3.0

**Endpoints:**
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Página principal |
| `/api/chat` | POST | Conversación con agente |
| `/api/predictions` | GET | Consultar predicciones |
| `/api/hospitals` | GET | Listar hospitales |
| `/api/productos` | GET | Listar productos |
| `/api/stats` | GET | Estadísticas del sistema |
| `/health` | GET | Health check |

**Archivos:**
- `src/app.py`
- `src/config.py`

---

### 3. Modelo Predictivo

**Tecnología:** scikit-learn 1.3.2

**Algoritmo:** Regresión Lineal

**Features (12 total):**
1. `dias_desde_inicio` - Tendencia temporal
2. `mes_sin` - Estacionalidad (componente sinusoidal)
3. `mes_cos` - Estacionalidad (componente cosenoidal)
4-10. Hospital encoding (7 hospitales)
11-12. Producto encoding (2 productos)

**Métricas:**
- R² Test: 0.902
- MAE Test: 38.6 unidades
- RMSE Test: 52.2 unidades

**Archivos:**
- `src/predictor.py`
- `scripts/training/train_model.py`
- `models/demand_model.pkl`

---

### 4. Agente Conversacional

**Tecnología:** Google Vertex AI (Gemini 1.5 Flash)

**Configuración:**
- Temperature: 0.7 (balance creatividad/precisión)
- Max tokens: 2048
- System prompt: Especialista en predicción de demanda médica

**Flujo:**
1. Recibe consulta del usuario
2. Obtiene contexto relevante de BD (predicciones, hospitales)
3. Construye prompt enriquecido
4. Envía a Gemini vía Vertex AI
5. Retorna respuesta en lenguaje natural

**Archivos:**
- `src/app.py` (métodos `get_chat_session`, `get_context_for_query`)

---

### 5. Base de Datos

**Tecnología:** PostgreSQL 14.x

**Ubicación:** AWS RDS (us-east-2)

**Tablas:**
- `ordenes_compra` (120 registros)
- `predicciones_demanda` (42 predicciones)
- `productos_solventum` (4 productos)
- `consultas_copiloto` (log de interacciones)

**Índices:**
- `idx_ordenes_fecha` en `ordenes_compra(fecha_orden)`
- `idx_pred_hospital` en `predicciones_demanda(hospital)`
- `idx_pred_producto` en `predicciones_demanda(producto)`

**Archivos:**
- `src/database.py`
- `src/db_utils.py`
- `scripts/setup/setup_database.py`

---

## Flujo de Deployment

```mermaid
flowchart LR
    A[Código Local] -->|Git Push| B[GitHub<br/>CuchoLeo/agente-capstone]
    B -->|Cloud Build| C[Container Registry<br/>Docker Image]
    C -->|Deploy| D[Cloud Run<br/>GCP us-central1]
    
    D -->|Conecta| E[(PostgreSQL<br/>AWS RDS)]
    D -->|API Calls| F[Vertex AI<br/>Gemini]
    
    style A fill:#e1f5ff
    style B fill:#fff3e0
    style C fill:#f3e5f5
    style D fill:#e8f5e9
```

---

## Seguridad y Configuración

### Variables de Entorno (.env)

```bash
# Base de Datos
DB_USER=agente_app
DB_PASSWORD=***
DB_HOST=db-capstonemia.c43jwggkkhqo.us-east-2.rds.amazonaws.com
DB_PORT=5432
DB_NAME=agente_capstone_db

# Google Cloud
GOOGLE_CLOUD_PROJECT=***
VERTEX_AI_LOCATION=us-central1

# Configuración Flask
FLASK_ENV=development
FLASK_HOST=0.0.0.0
FLASK_PORT=8000
SECRET_KEY=***
```

### Consideraciones de Seguridad

1. **Credenciales:** Nunca en código, siempre en .env
2. **PostgreSQL:** Usuario con permisos mínimos necesarios
3. **CORS:** Configurado para dominios específicos
4. **Rate Limiting:** (Pendiente) Implementar en producción
5. **HTTPS:** Obligatorio en Cloud Run

---

## Escalabilidad

### Límites Actuales
- Máx. requests simultáneos: ~100 (Flask desarrollo)
- Máx. conexiones DB: 20
- Latencia promedio: ~2-3 segundos (incluye LLM)

### Mejoras Futuras
- [ ] Caché de predicciones frecuentes (Redis)
- [ ] Async processing con Celery
- [ ] Load balancer en Cloud Run
- [ ] Connection pooling optimizado
- [ ] CDN para static files

---

## Monitoreo y Logging

### Logs del Sistema
**Ubicación:** `logs/agente_capstone.log`

**Niveles:**
- INFO: Operaciones normales
- WARNING: Situaciones anómalas no críticas
- ERROR: Errores que no detienen el sistema

### Métricas a Monitorear (Futuro)
- Latencia de requests
- Tasa de error
- Uso de tokens de Gemini
- Precisión del modelo en tiempo real
- Conexiones activas a DB

---

**Última actualización:** 2025-12-29
