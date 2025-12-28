"""
Script para agregar datos de prueba al agente
Crea predicciones y productos de ejemplo en la base de datos
"""
from database import get_connection
from db_utils import insert_producto_solventum
from datetime import datetime, timedelta
import random

def seed_productos_solventum():
    """Crea catálogo de productos Solventum"""
    productos = [
        {
            'codigo': 'SOL-AP-001',
            'nombre': 'Apósito Transparente Tegaderm',
            'categoria': 'APOSITOS',
            'descripcion': 'Apósito adhesivo transparente impermeable para protección de heridas',
            'palabras_clave': ['apósito', 'film', 'transparente', 'tegaderm', 'impermeable']
        },
        {
            'codigo': 'SOL-AP-002',
            'nombre': 'Apósito Espuma Tegaderm',
            'categoria': 'APOSITOS',
            'descripcion': 'Apósito de espuma absorbente para exudado moderado a alto',
            'palabras_clave': ['apósito', 'espuma', 'absorb', 'tegaderm']
        },
        {
            'codigo': 'SOL-GL-001',
            'nombre': 'Guantes Látex Estériles',
            'categoria': 'GUANTES_MEDICOS',
            'descripcion': 'Guantes de látex estériles para procedimientos médicos',
            'palabras_clave': ['guante', 'látex', 'esteril', 'quirurgico']
        },
        {
            'codigo': 'SOL-GL-002',
            'nombre': 'Guantes Nitrilo Sin Polvo',
            'categoria': 'GUANTES_MEDICOS',
            'descripcion': 'Guantes de nitrilo sin polvo, hipoalergénicos',
            'palabras_clave': ['guante', 'nitrilo', 'hipoalergenico']
        },
    ]
    
    print("📦 Creando productos Solventum...")
    for prod in productos:
        try:
            insert_producto_solventum(
                prod['codigo'],
                prod['nombre'],
                prod['categoria'],
                prod['descripcion'],
                prod['palabras_clave']
            )
            print(f"  ✓ {prod['nombre']}")
        except Exception as e:
            print(f"  ✗ Error en {prod['nombre']}: {e}")

def seed_predicciones():
    """Crea predicciones de demanda de ejemplo"""
    hospitales = [
        'Hospital del Salvador',
        'Complejo Asistencial Dr. Sótero del Río',
        'Hospital Clínico Universidad de Chile',
        'Hospital San José',
        'Hospital Barros Luco-Trudeau'
    ]
    
    productos = ['APOSITOS', 'GUANTES_MEDICOS']
    
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n📊 Creando predicciones de demanda...")
    
    # Generar predicciones para los próximos 3 meses
    base_date = datetime.now()
    
    for i in range(3):
        fecha_pred = base_date + timedelta(days=30*i)
        
        for hospital in hospitales:
            for producto in productos:
                demanda = random.randint(100, 500)
                confidence = round(random.uniform(85, 98), 2)
                
                try:
                    cursor.execute("""
                        INSERT INTO predicciones_demanda 
                        (hospital, producto, fecha_prediccion, demanda_estimada, confidence_score)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (hospital, producto, fecha_pred.date(), demanda, confidence))
                    
                except Exception as e:
                    print(f"  ✗ Error: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"  ✓ {len(hospitales) * len(productos) * 3} predicciones creadas")

def seed_ordenes_compra():
    """Crea órdenes de compra históricas de ejemplo"""
    from db_utils import insert_orden_compra
    
    print("\n📄 Creando órdenes de compra históricas...")
    
    ordenes = [
        ('OC-2024-001', '2024-11-15', 'Hospital del Salvador', 
         'APÓSITO 3M TRANSPARENTE ADHESIVO 5X5CM TEGADERM', 'APOSITOS', 200, 'UNIDADES', 450000),
        ('OC-2024-002', '2024-11-20', 'Hospital Sótero del Río',
         'GUANTE LATEX ESTÉRIL TALLA M', 'GUANTES_MEDICOS', 500, 'CAJAS', 850000),
        ('OC-2024-003', '2024-12-01', 'Hospital Clínico U. de Chile',
         'APÓSITO ESPUMA ADHESIVO 10X10CM', 'APOSITOS', 150, 'UNIDADES', 320000),
        ('OC-2024-004', '2024-12-10', 'Hospital San José',
         'GUANTE NITRILO SIN POLVO TALLA L', 'GUANTES_MEDICOS', 300, 'CAJAS', 520000),
    ]
    
    for orden in ordenes:
        try:
            insert_orden_compra(orden)
            print(f"  ✓ {orden[0]}")
        except Exception as e:
            print(f"  ✗ Error en {orden[0]}: {e}")

def main():
    print("="*60)
    print("  SEED DE DATOS DE PRUEBA - AGENTE CAPSTONE")
    print("="*60 + "\n")
    
    seed_productos_solventum()
    seed_predicciones()
    seed_ordenes_compra()
    
    print("\n" + "="*60)
    print("✅ SEED COMPLETADO")
    print("="*60)
    print("\nEl agente ahora tiene datos de prueba para funcionar.")
    print("Puedes iniciar la aplicación con: python app.py\n")

if __name__ == "__main__":
    main()
