"""
Aplicación Flask - Agente de Predicción de Demanda de Insums Médicos
Co-piloto de Ventas para Solventum

Basado en agente-plastico, adaptado para predicción de demanda hospitalaria
"""
import os
import logging
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession
from database import get_connection
from db_utils import get_predicciones_hospital, get_top_demanda_producto, log_consulta_copiloto
import config

# Configurar logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Inicializar Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['SESSION_TYPE'] = config.SESSION_TYPE
CORS(app, origins=config.CORS_ORIGINS)

# Inicializar Vertex AI
try:
    vertexai.init(project=config.GOOGLE_CLOUD_PROJECT, location=config.VERTEX_AI_LOCATION)
    logger.info(f"Vertex AI inicializado: {config.GOOGLE_CLOUD_PROJECT} en {config.VERTEX_AI_LOCATION}")
except Exception as e:
    logger.error(f"Error inicializando Vertex AI: {e}")

# Modelo Gemini
model = GenerativeModel(config.GEMINI_MODEL)

# Diccionario para almacenar sesiones de chat por usuario
chat_sessions = {}

def get_chat_session(user_id):
    """Obtiene o crea una sesión de chat para un usuario"""
    if user_id not in chat_sessions:
        chat_sessions[user_id] = model.start_chat()
        # Enviar system prompt como primer mensaje
        try:
            chat_sessions[user_id].send_message(config.SYSTEM_PROMPT)
        except Exception as e:
            logger.error(f"Error enviando system prompt: {e}")
    return chat_sessions[user_id]

def get_context_for_query(query):
    """
    Obtiene contexto relevante de la base de datos para una consulta
    """
    context = {
        'predicciones': [],
        'hospitales': [],
        'productos': []
    }
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Detectar entidades en la query (hospital, producto, etc)
        query_lower = query.lower()
        
        # Si menciona un hospital específico
        if 'salvador' in query_lower:
            context['predicciones'] = get_predicciones_hospital("Hospital del Salvador")
        elif 'sótero' in query_lower or 'sotero' in query_lower:
            context['predicciones'] = get_predicciones_hospital("Complejo Asistencial Dr. Sótero del Río")
        
        # Si menciona un producto
        if 'apósito' in query_lower or 'aposito' in query_lower:
            context['productos'] = get_top_demanda_producto("APOSITOS", limit=5)
        elif 'guante' in query_lower:
            context['productos'] = get_top_demanda_producto("GUANTES_MEDICOS", limit=5)
        
        # Obtener lista de hospitales con mayor demanda general
        cursor.execute("""
            SELECT DISTINCT hospital 
            FROM predicciones_demanda 
            ORDER BY hospital 
            LIMIT 10
        """)
        context['hospitales'] = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error obteniendo contexto: {e}")
    
    return context

def build_context_string(context):
    """Construye un string de contexto para incluir en el prompt"""
    parts = []
    
    if context['predicciones'] and not context['predicciones'].empty:
        parts.append("PREDICCIONES RELEVANTES:")
        for _, pred in context['predicciones'].iterrows():
            parts.append(f"- {pred['hospital']}: {pred['producto']} - {pred['demanda_estimada']} unidades (confianza: {pred['confidence_score']}%)")
    
    if context['productos'] and not context['productos'].empty:
        parts.append("\nHOSPITALES CON MAYOR DEMANDA:")
        for _, prod in context['productos'].iterrows():
            parts.append(f"- {prod['hospital']}: {prod['demanda_total']} unidades estimadas")
    
    if context['hospitales']:
        parts.append(f"\nHOSPITALES EN EL SISTEMA: {', '.join(context['hospitales'][:5])}")
    
    return "\n".join(parts) if parts else ""

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html', 
                         agent_name=config.AGENT_NAME,
                         quick_questions=config.QUICK_QUESTIONS)

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Endpoint principal para conversación con el agente
    """
    try:
        data = request.json
        user_query = data.get('message', '')
        user_id = session.get('user_id', 'default')
        
        if not user_query:
            return jsonify({'error': 'Mensaje vacío'}), 400
        
        logger.info(f"Query de usuario {user_id}: {user_query}")
        
        # Obtener contexto relevante de la base de datos
        context = get_context_for_query(user_query)
        context_string = build_context_string(context)
        
        # Construir mensaje completo con contexto
        full_message = f"{context_string}\n\nPREGUNTA DEL USUARIO:\n{user_query}" if context_string else user_query
        
        # Obtener o crear sesión de chat
        chat_session = get_chat_session(user_id)
        
        # Enviar mensaje al modelo
        response = chat_session.send_message(
            full_message,
            generation_config={
                'temperature': config.GEMINI_TEMPERATURE,
                'max_output_tokens': config.GEMINI_MAX_TOKENS,
            }
        )
        
        response_text = response.text
        logger.info(f"Respuesta generada para {user_id}: {response_text[:100]}...")
        
        # Registrar la consulta en la base de datos
        try:
            log_consulta_copiloto(user_id, user_query, response_text)
        except Exception as e:
            logger.error(f"Error logging consulta: {e}")
        
        return jsonify({
            'response': response_text,
            'context_used': bool(context_string)
        })
        
    except Exception as e:
        logger.error(f"Error en chat endpoint: {e}", exc_info=True)
        return jsonify({'error': f'Error procesando consulta: {str(e)}'}), 500

@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    """
    Obtiene predicciones filtradas por hospital y/o producto
    """
    try:
        hospital = request.args.get('hospital')
        producto = request.args.get('producto')
        
        if hospital:
            df = get_predicciones_hospital(hospital, producto)
            return jsonify(df.to_dict(orient='records'))
        elif producto:
            df = get_top_demanda_producto(producto)
            return jsonify(df.to_dict(orient='records'))
        else:
            return jsonify({'error': 'Debe especificar hospital o producto'}), 400
            
    except Exception as e:
        logger.error(f"Error obteniendo predicciones: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    """Lista todos los hospitales en el sistema"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT hospital, COUNT(*) as num_predicciones
            FROM predicciones_demanda
            GROUP BY hospital
            ORDER BY num_predicciones DESC
        """)
        
        hospitals = [{'nombre': row[0], 'predicciones': row[1]} for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return jsonify(hospitals)
        
    except Exception as e:
        logger.error(f"Error obteniendo hospitales: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/productos', methods=['GET'])
def get_productos():
    """Lista todos los productos Solventum"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT codigo_producto, nombre_producto, categoria, descripcion
            FROM productos_solventum
            ORDER BY categoria, nombre_producto
        """)
        
        productos = [
            {
                'codigo': row[0],
                'nombre': row[1],
                'categoria': row[2],
                'descripcion': row[3]
            } for row in cursor.fetchall()
        ]
        
        cursor.close()
        conn.close()
        
        return jsonify(productos)
        
    except Exception as e:
        logger.error(f"Error obteniendo productos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Estadísticas generales del sistema"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total de predicciones
        cursor.execute("SELECT COUNT(*) FROM predicciones_demanda")
        stats['total_predicciones'] = cursor.fetchone()[0]
        
        # Total de hospitales
        cursor.execute("SELECT COUNT(DISTINCT hospital) FROM predicciones_demanda")
        stats['total_hospitales'] = cursor.fetchone()[0]
        
        # Total de productos
        cursor.execute("SELECT COUNT(*) FROM productos_solventum")
        stats['total_productos'] = cursor.fetchone()[0]
        
        # Total de consultas al co-piloto
        cursor.execute("SELECT COUNT(*) FROM consultas_copiloto")
        stats['total_consultas'] = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error obteniendo stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Verificar conexión a DB
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'service': config.AGENT_NAME,
            'vertex_ai': True,
            'database': True
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    logger.info(f"Iniciando {config.AGENT_NAME}")
    logger.info(f"Ambiente: {config.FLASK_ENV}")
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )
