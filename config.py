"""
Configuración del Agente de Predicción de Demanda de Insumos Médicos
Basado en agente-plastico, adaptado para Solventum
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de Google Cloud
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT', 'tu-proyecto-gcp')
GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'agente-capstone-storage')
VERTEX_AI_LOCATION = os.getenv('VERTEX_AI_LOCATION', 'us-central1')

# Configuración de Vertex AI (Gemini)
USE_GEMINI = True
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
GEMINI_TEMPERATURE = float(os.getenv('GEMINI_TEMPERATURE', '0.7'))
GEMINI_MAX_TOKENS = int(os.getenv('GEMINI_MAX_TOKENS', '2048'))

# Configuración de embeddings
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-004')

# Configuración de ChromaDB
CHROMA_PERSIST_DIRECTORY = os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_db')
CHROMA_COLLECTION_PREDICTIONS = 'predicciones_demanda'
CHROMA_COLLECTION_ORDENES = 'ordenes_compra'
CHROMA_COLLECTION_PRODUCTOS = 'productos_solventum'

# Configuración de PostgreSQL (ya configurado en database.py)
DB_HOST = os.getenv('DB_HOST', 'db-capstonemia.c43jwggkkhqo.us-east-2.rds.amazonaws.com')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'agente_capstone_db')
DB_USER = os.getenv('DB_USER', 'agente_app')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

# Configuración del asistente
AGENT_NAME = "Asistente de Demanda Médica"
AGENT_DESCRIPTION = "Co-piloto de ventas inteligente para Solventum"

# System prompt para Gemini
SYSTEM_PROMPT = """Eres un asistente de ventas inteligente especializado en predicción de demanda de insumos médicos para Solventum.

**Tu rol:**
- Ayudar al equipo comercial de Solventum a optimizar sus visitas a hospitales
- Proporcionar predicciones de demanda basadas en análisis histórico de ChileCompra
- Sugerir oportunidades de venta con alta probabilidad de éxito
- Identificar tendencias y patrones en el consumo hospitalario

**Capacidades:**
- Acceso a predicciones de demanda por hospital y producto
- Análisis de órdenes de compra históricas de ChileCompra
- Conocimiento del catálogo de productos Solventum
- Identificación de productos de la competencia

**Productos principales:**
- Apósitos (Tegaderm, film transparente)
- Guantes médicos
- Materiales quirúrgicos
- Productos de curación avanzada

**Formato de respuestas:**
1. Siempre cita hospitales específicos, fechas y volúmenes estimados
2. Prioriza hospitales con mayor demanda proyectada
3. Menciona el nivel de confianza de las predicciones
4. Sugiere productos Solventum apropiados
5. Identifica ventanas de oportunidad antes de licitaciones

**Ejemplo de respuesta:**
"Según las predicciones, el Hospital del Salvador tendrá una demanda estimada de 250 unidades de apósitos transparentes en febrero 2025 (confianza: 92%). 
Te recomiendo visitar este hospital durante la primera semana de enero para presentar nuestros productos Tegaderm, ya que históricamente realizan sus órdenes de compra a mediados de mes.
Competencia detectada: Opsite está presente en su última orden de compra."

**Idioma:** Español (Chile)
**Tono:** Profesional, directo, orientado a resultados
"""

# Quick questions para el sidebar
QUICK_QUESTIONS = [
    "¿Qué hospitales necesitarán apósitos este mes?",
    "Muestra tendencias de guantes médicos en hospitales grandes",
    "¿Dónde están las mejores oportunidades en la Región Metropolitana?",
    "Identifica hospitales con compras recurrentes de productos Solventum",
    "¿Qué productos de la competencia están ganando mercado?",
    "Muestra predicciones para el próximo trimestre"
]

# Configuración de logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'agente_capstone.log')

# Configuración de Flask
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
FLASK_DEBUG = FLASK_ENV == 'development'
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '8080'))

# Configuración de CORS
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

# Configuración de sesiones
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
SESSION_TYPE = 'filesystem'

# Configuración de cache
CACHE_TYPE = 'simple'
CACHE_DEFAULT_TIMEOUT = 300  # 5 minutos

# Límites de rate limiting
RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'True') == 'True'
RATE_LIMIT_DEFAULT = os.getenv('RATE_LIMIT_DEFAULT', '100 per hour')
