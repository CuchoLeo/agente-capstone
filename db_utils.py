"""
Script de utilidades para la base de datos PostgreSQL
Incluye funciones para crear tablas, queries comunes, etc.
"""
from database import get_connection, get_session, get_engine
from sqlalchemy import text
import pandas as pd

def create_tables():
    """Crea las tablas necesarias para el proyecto"""
    engine = get_engine()
    
    # Tabla para órdenes de compra de ChileCompra
    create_ordenes_compra = """
    CREATE TABLE IF NOT EXISTS ordenes_compra (
        id SERIAL PRIMARY KEY,
        orden_id VARCHAR(100) UNIQUE NOT NULL,
        fecha_orden DATE,
        nombre_organismo VARCHAR(500),
        descripcion_item TEXT,
        producto_estandarizado VARCHAR(200),
        cantidad INTEGER,
        unidad_medida VARCHAR(50),
        monto_total DECIMAL(15,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Tabla para predicciones de demanda
    create_predicciones = """
    CREATE TABLE IF NOT EXISTS predicciones_demanda (
        id SERIAL PRIMARY KEY,
        hospital VARCHAR(500),
        producto VARCHAR(200),
        fecha_prediccion DATE,
        demanda_estimada INTEGER,
        confidence_score DECIMAL(5,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Tabla para catálogo de productos Solventum
    create_productos = """
    CREATE TABLE IF NOT EXISTS productos_solventum (
        id SERIAL PRIMARY KEY,
        codigo_producto VARCHAR(100) UNIQUE NOT NULL,
        nombre_producto VARCHAR(300),
        categoria VARCHAR(100),
        descripcion TEXT,
        palabras_clave TEXT[],
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Tabla para registro de consultas del co-piloto
    create_consultas = """
    CREATE TABLE IF NOT EXISTS consultas_copiloto (
        id SERIAL PRIMARY KEY,
        usuario VARCHAR(100),
        consulta TEXT,
        respuesta TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_ordenes_compra))
        conn.execute(text(create_predicciones))
        conn.execute(text(create_productos))
        conn.execute(text(create_consultas))
        conn.commit()
    
    print("✅ Tablas creadas exitosamente")

def insert_orden_compra(data):
    """Inserta una orden de compra en la base de datos"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
    INSERT INTO ordenes_compra 
    (orden_id, fecha_orden, nombre_organismo, descripcion_item, 
     producto_estandarizado, cantidad, unidad_medida, monto_total)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (orden_id) DO UPDATE SET
        updated_at = CURRENT_TIMESTAMP;
    """
    
    cursor.execute(query, data)
    conn.commit()
    cursor.close()
    conn.close()

def get_predicciones_hospital(hospital, producto=None):
    """Obtiene predicciones para un hospital específico"""
    conn = get_connection()
    
    if producto:
        query = """
        SELECT * FROM predicciones_demanda 
        WHERE hospital = %s AND producto = %s
        ORDER BY fecha_prediccion DESC
        LIMIT 10
        """
        df = pd.read_sql_query(query, conn, params=(hospital, producto))
    else:
        query = """
        SELECT * FROM predicciones_demanda 
        WHERE hospital = %s
        ORDER BY fecha_prediccion DESC
        LIMIT 10
        """
        df = pd.read_sql_query(query, conn, params=(hospital,))
    
    conn.close()
    return df

def get_top_demanda_producto(producto, limit=5):
    """Obtiene los hospitales con mayor demanda estimada para un producto"""
    conn = get_connection()
    
    query = """
    SELECT hospital, producto, SUM(demanda_estimada) as demanda_total
    FROM predicciones_demanda
    WHERE producto = %s
    GROUP BY hospital, producto
    ORDER BY demanda_total DESC
    LIMIT %s
    """
    
    df = pd.read_sql_query(query, conn, params=(producto, limit))
    conn.close()
    return df

def insert_producto_solventum(codigo, nombre, categoria, descripcion, palabras_clave):
    """Inserta un producto del catálogo Solventum"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
    INSERT INTO productos_solventum 
    (codigo_producto, nombre_producto, categoria, descripcion, palabras_clave)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (codigo_producto) DO UPDATE SET
        nombre_producto = EXCLUDED.nombre_producto,
        descripcion = EXCLUDED.descripcion;
    """
    
    cursor.execute(query, (codigo, nombre, categoria, descripcion, palabras_clave))
    conn.commit()
    cursor.close()
    conn.close()

def log_consulta_copiloto(usuario, consulta, respuesta):
    """Registra una consulta al co-piloto de ventas"""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
    INSERT INTO consultas_copiloto (usuario, consulta, respuesta)
    VALUES (%s, %s, %s)
    """
    
    cursor.execute(query, (usuario, consulta, respuesta))
    conn.commit()
    cursor.close()
    conn.close()

def get_predicciones_producto_mes(producto, limit=10):
    """
    Obtiene ranking de hospitales con mayor demanda estimada para un producto
    incluyendo el desglose por mes
    
    Args:
        producto: Código del producto (ej: 'APOSITOS', 'GUANTES_MEDICOS')
        limit: Número máximo de hospitales a retornar
        
    Returns:
        DataFrame con columnas: hospital, producto, fecha_prediccion, demanda_estimada, confidence_score
    """
    conn = get_connection()
    
    query = """
    SELECT 
        hospital,
        producto,
        fecha_prediccion,
        demanda_estimada,
        confidence_score
    FROM predicciones_demanda
    WHERE producto = %s
    ORDER BY fecha_prediccion, demanda_estimada DESC
    LIMIT %s
    """
    
    df = pd.read_sql_query(query, conn, params=(producto, limit))
    conn.close()
    return df

def get_all_hospitales_ranking(producto=None):
    """
    Obtiene ranking de TODOS los hospitales con su demanda total estimada
    
    Args:
        producto: Opcional - filtrar por producto específico
        
    Returns:
        DataFrame con columnas: hospital, demanda_total, num_predicciones
    """
    conn = get_connection()
    
    if producto:
        query = """
        SELECT 
            hospital,
            SUM(demanda_estimada) as demanda_total,
            COUNT(*) as num_predicciones,
            AVG(confidence_score) as confidence_promedio
        FROM predicciones_demanda
        WHERE producto = %s
        GROUP BY hospital
        ORDER BY demanda_total DESC
        """
        df = pd.read_sql_query(query, conn, params=(producto,))
    else:
        query = """
        SELECT 
            hospital,
            SUM(demanda_estimada) as demanda_total,
            COUNT(*) as num_predicciones,
            AVG(confidence_score) as confidence_promedio
        FROM predicciones_demanda
        GROUP BY hospital
        ORDER BY demanda_total DESC
        """
        df = pd.read_sql_query(query, conn)
    
    conn.close()
    return df

def get_predicciones_proximas(dias=30, producto=None):
    """
    Obtiene predicciones para los próximos N días
    
    Args:
        dias: Número de días hacia adelante
        producto: Opcional - filtrar por producto
        
    Returns:
        DataFrame con todas las predicciones en el rango de fechas
    """
    conn = get_connection()
    
    if producto:
        query = """
        SELECT 
            hospital,
            producto,
            fecha_prediccion,
            demanda_estimada,
            confidence_score
        FROM predicciones_demanda
        WHERE fecha_prediccion <= CURRENT_DATE + INTERVAL '%s days'
          AND producto = %s
        ORDER BY fecha_prediccion, hospital
        """
        df = pd.read_sql_query(query, conn, params=(dias, producto))
    else:
        query = """
        SELECT 
            hospital,
            producto,
            fecha_prediccion,
            demanda_estimada,
            confidence_score
        FROM predicciones_demanda
        WHERE fecha_prediccion <= CURRENT_DATE + INTERVAL '%s days'
        ORDER BY fecha_prediccion, producto, hospital
        """
        df = pd.read_sql_query(query, conn, params=(dias,))
    
    conn.close()
    return df

def get_resumen_producto(producto):
    """
    Obtiene un resumen completo de predicciones para un producto
    
    Args:
        producto: Código del producto
        
    Returns:
        dict con información agregada del producto
    """
    conn = get_connection()
    
    query = """
    SELECT 
        COUNT(DISTINCT hospital) as num_hospitales,
        SUM(demanda_estimada) as demanda_total,
        AVG(demanda_estimada) as demanda_promedio,
        MIN(fecha_prediccion) as fecha_inicio,
        MAX(fecha_prediccion) as fecha_fin,
        AVG(confidence_score) as confidence_promedio
    FROM predicciones_demanda
    WHERE producto = %s
    """
    
    df = pd.read_sql_query(query, conn, params=(producto,))
    conn.close()
    
    if not df.empty:
        return df.iloc[0].to_dict()
    return {}

if __name__ == "__main__":
    # Crear tablas
    create_tables()
