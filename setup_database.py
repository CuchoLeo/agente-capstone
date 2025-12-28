"""
Script para configurar la base de datos del proyecto
- Crear usuario específico para la aplicación
- Crear database dedicado
- Crear tablas necesarias
- Asignar permisos
"""
import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

# Credenciales del usuario admin (postgres)
ADMIN_USER = os.getenv('DB_USER', 'postgres')
ADMIN_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', 'db-capstonemia.c43jwggkkhqo.us-east-2.rds.amazonaws.com')
DB_PORT = os.getenv('DB_PORT', '5432')

# Configuración del nuevo usuario de aplicación
APP_USER = 'agente_app'
APP_PASSWORD = 'Capstone2025!Secure#'
APP_DATABASE = 'agente_capstone_db'

def create_user_and_database():
    """Crear usuario y database para la aplicación"""
    print("🔧 Conectando a PostgreSQL como administrador...")
    
    try:
        # Conectar a la base de datos por defecto
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database='postgres',
            user=ADMIN_USER,
            password=ADMIN_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Conexión exitosa\n")
        
        # Verificar si el usuario ya existe
        cursor.execute(
            "SELECT 1 FROM pg_roles WHERE rolname=%s",
            (APP_USER,)
        )
        user_exists = cursor.fetchone()
        
        if not user_exists:
            print(f"👤 Creando usuario: {APP_USER}")
            cursor.execute(
                sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
                    sql.Identifier(APP_USER)
                ),
                (APP_PASSWORD,)
            )
            print(f"✅ Usuario '{APP_USER}' creado exitosamente\n")
        else:
            print(f"ℹ️  Usuario '{APP_USER}' ya existe\n")
        
        # Verificar si la database ya existe
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname=%s",
            (APP_DATABASE,)
        )
        db_exists = cursor.fetchone()
        
        if not db_exists:
            print(f"🗄️  Creando database: {APP_DATABASE}")
            # AWS RDS no permite especificar OWNER, crear sin owner
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(APP_DATABASE)
                )
            )
            print(f"✅ Database '{APP_DATABASE}' creada exitosamente\n")
        else:
            print(f"ℹ️  Database '{APP_DATABASE}' ya existe\n")
        
        # Otorgar permisos al usuario
        print(f"🔐 Otorgando permisos a {APP_USER}...")
        cursor.execute(
            sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
                sql.Identifier(APP_DATABASE),
                sql.Identifier(APP_USER)
            )
        )
        print(f"✅ Permisos de database otorgados\n")
        
        cursor.close()
        conn.close()
        
        # Ahora conectar al nuevo database para otorgar permisos de schema
        print(f"🔐 Otorgando permisos de schema public...")
        conn_db = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=APP_DATABASE,
            user=ADMIN_USER,
            password=ADMIN_PASSWORD
        )
        conn_db.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor_db = conn_db.cursor()
        
        # Otorgar permisos en el schema public
        cursor_db.execute(
            sql.SQL("GRANT ALL ON SCHEMA public TO {}").format(
                sql.Identifier(APP_USER)
            )
        )
        cursor_db.execute(
            sql.SQL("GRANT CREATE ON SCHEMA public TO {}").format(
                sql.Identifier(APP_USER)
            )
        )
        print(f"✅ Permisos de schema otorgados\n")
        
        cursor_db.close()
        conn_db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_tables():
    """Crear tablas en el nuevo database"""
    print(f"📊 Creando tablas en {APP_DATABASE}...")
    
    try:
        # Conectar al nuevo database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=APP_DATABASE,
            user=APP_USER,
            password=APP_PASSWORD
        )
        cursor = conn.cursor()
        
        # Tabla para órdenes de compra de ChileCompra
        print("  → Creando tabla 'ordenes_compra'...")
        cursor.execute("""
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
        """)
        
        # Índices para optimización
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ordenes_fecha ON ordenes_compra(fecha_orden);
        CREATE INDEX IF NOT EXISTS idx_ordenes_organismo ON ordenes_compra(nombre_organismo);
        CREATE INDEX IF NOT EXISTS idx_ordenes_producto ON ordenes_compra(producto_estandarizado);
        """)
        
        # Tabla para predicciones de demanda
        print("  → Creando tabla 'predicciones_demanda'...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS predicciones_demanda (
            id SERIAL PRIMARY KEY,
            hospital VARCHAR(500),
            producto VARCHAR(200),
            fecha_prediccion DATE,
            demanda_estimada INTEGER,
            confidence_score DECIMAL(5,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_pred_hospital ON predicciones_demanda(hospital);
        CREATE INDEX IF NOT EXISTS idx_pred_producto ON predicciones_demanda(producto);
        CREATE INDEX IF NOT EXISTS idx_pred_fecha ON predicciones_demanda(fecha_prediccion);
        """)
        
        # Tabla para catálogo de productos Solventum
        print("  → Creando tabla 'productos_solventum'...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos_solventum (
            id SERIAL PRIMARY KEY,
            codigo_producto VARCHAR(100) UNIQUE NOT NULL,
            nombre_producto VARCHAR(300),
            categoria VARCHAR(100),
            descripcion TEXT,
            palabras_clave TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos_solventum(categoria);
        """)
        
        # Tabla para registro de consultas del co-piloto
        print("  → Creando tabla 'consultas_copiloto'...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS consultas_copiloto (
            id SERIAL PRIMARY KEY,
            usuario VARCHAR(100),
            consulta TEXT,
            respuesta TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_consultas_timestamp ON consultas_copiloto(timestamp);
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Todas las tablas creadas exitosamente\n")
        return True
        
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False

def update_env_file():
    """Actualizar archivo .env con las nuevas credenciales"""
    print("📝 Actualizando archivo .env...")
    
    env_content = f"""# Credenciales de Base de Datos PostgreSQL (AWS RDS)
# Usuario de la aplicación (usar en producción)
DB_USER={APP_USER}
DB_PASSWORD={APP_PASSWORD}
DB_HOST={DB_HOST}
DB_PORT={DB_PORT}
DB_NAME={APP_DATABASE}
DB_REGION=us-east-2

# Credenciales de administrador (solo para mantenimiento)
DB_ADMIN_USER={ADMIN_USER}
DB_ADMIN_PASSWORD={ADMIN_PASSWORD}
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Archivo .env actualizado\n")

def main():
    print("="*60)
    print("    CONFIGURACIÓN DE BASE DE DATOS - AGENTE CAPSTONE")
    print("="*60 + "\n")
    
    # Paso 1: Crear usuario y database
    if not create_user_and_database():
        print("\n❌ Error en la configuración inicial")
        sys.exit(1)
    
    # Paso 2: Crear tablas
    if not create_tables():
        print("\n❌ Error creando tablas")
        sys.exit(1)
    
    # Paso 3: Actualizar .env
    update_env_file()
    
    print("="*60)
    print("✅ CONFIGURACIÓN COMPLETADA EXITOSAMENTE")
    print("="*60)
    print("\n📋 Resumen de configuración:")
    print(f"   • Database: {APP_DATABASE}")
    print(f"   • Usuario: {APP_USER}")
    print(f"   • Password: {APP_PASSWORD}")
    print(f"   • Host: {DB_HOST}")
    print(f"   • Puerto: {DB_PORT}")
    print("\n🔒 El archivo .env ha sido actualizado con las nuevas credenciales")
    print("⚠️  IMPORTANTE: No compartir estas credenciales públicamente\n")

if __name__ == "__main__":
    main()
