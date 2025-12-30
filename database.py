"""
Configuración de conexión a base de datos PostgreSQL (AWS RDS)
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db-capstonemia.c43jwggkkhqo.us-east-2.rds.amazonaws.com'),
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'agente_capstone_db'),
    'user': os.getenv('DB_USER', 'agente_app'),
    'password': os.getenv('DB_PASSWORD', ''),
    'region': os.getenv('DB_REGION', 'us-east-2')
}

# URL JDBC (para referencia)
JDBC_URL = 'jdbc:postgresql://db-capstonemia.c43jwggkkhqo.us-east-2.rds.amazonaws.com:5432/postgres'

# SQLAlchemy Database URL
def get_database_url():
    """Construye la URL de conexión SQLAlchemy"""
    return f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

# Engine de SQLAlchemy
def get_engine():
    """Crea y retorna un engine de SQLAlchemy"""
    database_url = get_database_url()
    engine = create_engine(
        database_url,
        pool_pre_ping=True,  # Verifica conexiones antes de usar
        pool_size=10,
        max_overflow=20,
        echo=False,  # Cambiar a True para debug SQL
        connect_args={'sslmode': 'require'}  # AWS RDS requiere SSL
    )
    return engine

# Session maker para SQLAlchemy
def get_session():
    """Crea y retorna una sesión de SQLAlchemy"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

# Conexión directa con psycopg2
def get_connection():
    """Crea y retorna una conexión directa con psycopg2"""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            sslmode='require'  # AWS RDS requiere SSL
        )
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        raise

# Test de conexión
def test_connection():
    """Prueba la conexión a la base de datos"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Conexión exitosa a PostgreSQL")
        print(f"Versión: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error en conexión: {e}")
        return False

if __name__ == "__main__":
    # Ejecutar test de conexión
    test_connection()
