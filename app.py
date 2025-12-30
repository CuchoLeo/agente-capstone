"""
Aplicación Flask - Agente de Predicción de Demanda de Insums Médicos
Co-piloto de Ventas para Solventum

Basado en agente-plastico, adaptado para predicción de demanda hospitalaria
"""
import os
import logging
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from database import get_connection
from db_utils import (
    get_predicciones_hospital, 
    get_top_demanda_producto, 
    log_consulta_copiloto,
    get_all_hospitales_ranking,
    get_predicciones_producto_mes,
    get_predicciones_proximas,
    get_resumen_producto
)
import config
import pandas as pd

# Importar según el modo de autenticación
if config.USE_VERTEX_AI:
    import vertexai
    from vertexai.generative_models import GenerativeModel, ChatSession
else:
    import google.generativeai as genai

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

# Inicializar Gemini según el modo
if config.USE_VERTEX_AI:
    try:
        vertexai.init(project=config.GOOGLE_CLOUD_PROJECT, location=config.VERTEX_AI_LOCATION)
        model = GenerativeModel(config.GEMINI_MODEL)
        logger.info(f"Vertex AI inicializado: {config.GOOGLE_CLOUD_PROJECT} en {config.VERTEX_AI_LOCATION}")
    except Exception as e:
        logger.error(f"Error inicializando Vertex AI: {e}")
        model = None
else:
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(config.GEMINI_MODEL)
        logger.info(f"Gemini API configurado con modelo: {config.GEMINI_MODEL}")
    except Exception as e:
        logger.error(f"Error configurando Gemini API: {e}")
        model = None

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
    Obtiene contexto relevante de la base de datos para una consulta.
    
    Esta función analiza la pregunta del usuario y consulta la BD para traer
    datos REALES que el agente puede usar en su respuesta.
    """
    context = {
        'predicciones_detalle': pd.DataFrame(),
        'ranking_hospitales': pd.DataFrame(),
        'resumen': {},
        'tipo_consulta': 'general'
    }
    
    try:
        query_lower = query.lower()
        
        # Detectar si pregunta por un PRODUCTO específico
        producto_detectado = None
        if 'apósito' in query_lower or 'aposito' in query_lower or 'tegaderm' in query_lower:
            producto_detectado = 'APOSITOS'
            context['tipo_consulta'] = 'producto_apositos'
        elif 'guante' in query_lower:
            producto_detectado = 'GUANTES_MEDICOS'
            context['tipo_consulta'] = 'producto_guantes'
        
        # Detectar si pregunta por un HOSPITAL específico
        hospital_detectado = None
        if 'salvador' in query_lower:
            hospital_detectado = "Hospital del Salvador"
            context['tipo_consulta'] = 'hospital_especifico'
        elif 'sótero' in query_lower or 'sotero' in query_lower:
            hospital_detectado = "Complejo Asistencial Dr. Sótero del Río"
            context['tipo_consulta'] = 'hospital_especifico'
        elif 'san josé' in query_lower or 'san jose' in query_lower:
            hospital_detectado = "Hospital San José"
            context['tipo_consulta'] = 'hospital_especifico'
        elif 'barros luco' in query_lower:
            hospital_detectado = "Hospital Barros Luco-Trudeau"
            context['tipo_consulta'] = 'hospital_especifico'
        
        # CONSULTA 1: Si pregunta por un producto específico
        if producto_detectado:
            # Obtener ranking completo de hospitales para ese producto
            context['ranking_hospitales'] = get_all_hospitales_ranking(producto=producto_detectado)
            
            # Obtener predicciones detalladas del próximo mes
            context['predicciones_detalle'] = get_predicciones_proximas(dias=90, producto=producto_detectado)
            
            # Obtener resumen estadístico
            context['resumen'] = get_resumen_producto(producto_detectado)
            
            logger.info(f"Contexto para {producto_detectado}: {len(context['ranking_hospitales'])} hospitales, {len(context['predicciones_detalle'])} predicciones")
        
        # CONSULTA 2: Si pregunta por un hospital específico
        elif hospital_detectado:
            context['predicciones_detalle'] = get_predicciones_hospital(hospital_detectado)
            logger.info(f"Contexto para {hospital_detectado}: {len(context['predicciones_detalle'])} predicciones")
        
        # CONSULTA 3: Pregunta general (traer datos de TODOS los productos/hospitales)
        else:
            # Si menciona palabras como "qué", "cuál", "necesitar", traer ranking general
            if any(word in query_lower for word in ['qué', 'que', 'cuál', 'cual', 'necesitar', 'demandar', 'comprar']):
                # Traer ranking de hospitales por demanda total
                context['ranking_hospitales'] = get_all_hospitales_ranking()
                
                # Traer todas las predicciones próximas
                context['predicciones_detalle'] = get_predicciones_proximas(dias=90)
                
                logger.info(f"Contexto general: {len(context['ranking_hospitales'])} hospitales, {len(context['predicciones_detalle'])} predicciones")
        
    except Exception as e:
        logger.error(f"Error obteniendo contexto de BD: {e}", exc_info=True)
    
    return context

def build_context_string(context):
    """
    Construye un string formateado con los datos de la BD para incluir en el prompt.
    Este será el contexto REAL que Gemini usará para responder.
    """
    parts = []
    
    # 1. Ranking de hospitales (si existe)
    if isinstance(context['ranking_hospitales'], pd.DataFrame) and not context['ranking_hospitales'].empty:
        parts.append("=== DATOS REALES DE LA BASE DE DATOS ===\n")
        parts.append("📊 RANKING DE HOSPITALES POR DEMANDA ESTIMADA (próximos 3 meses):")
        
        for idx, row in context['ranking_hospitales'].iterrows():
            parts.append(
                f"  {idx+1}. {row['hospital']}: "
                f"{int(row['demanda_total'])} unidades totales "
                f"(confianza: {row['confidence_promedio']:.1f}%)"
            )
        
        parts.append("")  # Línea en blanco
    
    # 2. Predicciones detalladas (si existen)
    if isinstance(context['predicciones_detalle'], pd.DataFrame) and not context['predicciones_detalle'].empty:
        parts.append("📅 PREDICCIONES DETALLADAS:")
        
        # Agrupar por hospital para mejor legibilidad
        for hospital in context['predicciones_detalle']['hospital'].unique()[:7]:  # Top 7
            hospital_preds = context['predicciones_detalle'][
                context['predicciones_detalle']['hospital'] == hospital
            ]
            
            parts.append(f"\n  🏥 {hospital}:")
            for _, pred in hospital_preds.iterrows():
                fecha = pred['fecha_prediccion'].strftime('%Y-%m') if hasattr(pred['fecha_prediccion'], 'strftime') else str(pred['fecha_prediccion'])
                parts.append(
                    f"     • {pred['producto']}: {int(pred['demanda_estimada'])} unidades "
                    f"({fecha})"
                )
        
        parts.append("")
    
    # 3. Resumen estadístico (si existe)
    if context['resumen']:
        parts.append("📈 RESUMEN ESTADÍSTICO:")
        res = context['resumen']
        if 'demanda_total' in res:
            parts.append(f"  • Demanda total estimada: {int(res['demanda_total'])} unidades")
        if 'num_hospitales' in res:
            parts.append(f"  • Hospitales involucrados: {int(res['num_hospitales'])}")
        if 'demanda_promedio' in res:
            parts.append(f"  • Demanda promedio por hospital: {int(res['demanda_promedio'])} unidades")
        parts.append("")
    
    # 4. Instrucción para el agente
    if parts:
        parts.append("⚠️ IMPORTANTE: Usa SOLO estos datos reales de la base de datos para responder.")
        parts.append("Menciona números específicos, hospitales y fechas exactas de las predicciones.\n")
    
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
