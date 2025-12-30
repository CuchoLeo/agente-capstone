"""
Script para extraer datos actuales de la base de datos
"""
import os
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
    'sslmode': 'require'
}

def main():
    print("\n" + "="*80)
    print("EXTRACCIÓN DE DATOS - BASE DE DATOS AGENTE CAPSTONE")
    print("="*80 + "\n")
    
    try:
        # Conectar
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 1. PREDICCIONES
        print("="*80)
        print("1️⃣  PREDICCIONES DE DEMANDA (muestra de 30 registros)")
        print("="*80)
        cursor.execute("""
            SELECT 
                hospital,
                producto,
                fecha_prediccion,
                demanda_estimada,
                confidence_score
            FROM predicciones_demanda
            ORDER BY fecha_prediccion, hospital, producto
            LIMIT 30
        """)
        
        print(f"{'Hospital':<40} {'Producto':<20} {'Fecha':<12} {'Demanda':<10} {'Confianza'}")
        print("-"*80)
        for row in cursor.fetchall():
            print(f"{row[0]:<40} {row[1]:<20} {str(row[2]):<12} {row[3]:<10} {row[4]}%")
        
        # Total de predicciones
        cursor.execute("SELECT COUNT(*) FROM predicciones_demanda")
        total_pred = cursor.fetchone()[0]
        print(f"\n📊 Total de predicciones en BD: {total_pred}")
        
        # 2. RESUMEN POR HOSPITAL
        print("\n" + "="*80)
        print("2️⃣  TOP HOSPITALES CON MAYOR DEMANDA ESTIMADA")
        print("="*80)
        cursor.execute("""
            SELECT 
                hospital,
                SUM(demanda_estimada) as demanda_total,
                COUNT(*) as num_predicciones
            FROM predicciones_demanda
            GROUP BY hospital
            ORDER BY demanda_total DESC
        """)
        
        print(f"{'Hospital':<50} {'Demanda Total':<15} {'# Predicciones'}")
        print("-"*80)
        for row in cursor.fetchall():
            print(f"{row[0]:<50} {row[1]:<15} {row[2]}")
        
        # 3. RESUMEN POR PRODUCTO
        print("\n" + "="*80)
        print("3️⃣  DEMANDA POR PRODUCTO")
        print("="*80)
        cursor.execute("""
            SELECT 
                producto,
                SUM(demanda_estimada) as demanda_total,
                COUNT(DISTINCT hospital) as num_hospitales,
                AVG(confidence_score) as conf_promedio
            FROM predicciones_demanda
            GROUP BY producto
            ORDER BY demanda_total DESC
        """)
        
        print(f"{'Producto':<25} {'Demanda Total':<15} {'# Hospitales':<15} {'Conf. Promedio'}")
        print("-"*80)
        for row in cursor.fetchall():
            print(f"{row[0]:<25} {row[1]:<15} {row[2]:<15} {row[3]:.2f}%")
        
        # 4. ÓRDENES HISTÓRICAS (muestra)
        print("\n" + "="*80)
        print("4️⃣  ÓRDENES DE COMPRA HISTÓRICAS (últimas 20)")
        print("="*80)
        cursor.execute("""
            SELECT 
                orden_id,
                fecha_orden,
                nombre_organismo,
                producto_estandarizado,
                cantidad
            FROM ordenes_compra
            ORDER BY fecha_orden DESC
            LIMIT 20
        """)
        
        print(f"{'Orden ID':<15} {'Fecha':<12} {'Hospital':<35} {'Producto':<20} {'Cantidad'}")
        print("-"*80)
        for row in cursor.fetchall():
            print(f"{row[0]:<15} {str(row[1]):<12} {row[2][:34]:<35} {row[3]:<20} {row[4]}")
        
        cursor.execute("SELECT COUNT(*) FROM ordenes_compra")
        total_ordenes = cursor.fetchone()[0]
        print(f"\n📦 Total de órdenes históricas en BD: {total_ordenes}")
        
        # Rango de fechas
        cursor.execute("""
            SELECT MIN(fecha_orden), MAX(fecha_orden) 
            FROM ordenes_compra
        """)
        fecha_min, fecha_max = cursor.fetchone()
        print(f"📅 Rango de fechas: {fecha_min} a {fecha_max}")
        
        # 5. PRODUCTOS SOLVENTUM
        print("\n" + "="*80)
        print("5️⃣  CATÁLOGO DE PRODUCTOS SOLVENTUM")
        print("="*80)
        cursor.execute("""
            SELECT 
                codigo_producto,
                nombre_producto,
                categoria
            FROM productos_solventum
            ORDER BY categoria, nombre_producto
        """)
        
        print(f"{'Código':<15} {'Nombre':<40} {'Categoría'}")
        print("-"*80)
        for row in cursor.fetchall():
            print(f"{row[0]:<15} {row[1]:<40} {row[2]}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*80)
        print("✅ EXTRACCIÓN COMPLETADA")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
