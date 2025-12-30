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

def seed_ordenes_compra():
    """
    Crea órdenes de compra históricas REALISTAS para los últimos 12 meses
    Con tendencia, estacionalidad y variabilidad natural
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n📄 Creando órdenes de compra históricas (12 meses)...")
    
    hospitales = [
        'Hospital del Salvador',
        'Complejo Asistencial Dr. Sótero del Río',
        'Hospital Clínico Universidad de Chile',
        'Hospital San José',
        'Hospital Barros Luco-Trudeau'
    ]
    
    # Configuración de productos con demanda base diferente
    productos_config = {
        'APOSITOS': {
            'demanda_base': 180,
            'tendencia_mensual': 5,  # Crecimiento de 5 unidades por mes
            'estacionalidad': [1.0, 0.95, 1.05, 1.1, 1.15, 1.2, 1.25, 1.2, 1.1, 1.05, 1.0, 0.95],  # Pico en invierno
            'variabilidad': 20
        },
        'GUANTES_MEDICOS': {
            'demanda_base': 400,
            'tendencia_mensual': 8,
            'estacionalidad': [0.9, 0.95, 1.0, 1.05, 1.15, 1.25, 1.3, 1.25, 1.15, 1.05, 1.0, 0.95],  # Pico en invierno
            'variabilidad': 40
        }
    }
    
    # Factores por hospital (algunos hospitales compran más)
    hospital_factor = {
        'Hospital del Salvador': 1.0,
        'Complejo Asistencial Dr. Sótero del Río': 1.4,  # Hospital más grande
        'Hospital Clínico Universidad de Chile': 1.2,
        'Hospital San José': 0.9,
        'Hospital Barros Luco-Trudeau': 1.1
    }
    
    # Generar órdenes para los últimos 12 meses
    fecha_actual = datetime.now()
    orden_counter = 1
    
    query = """
    INSERT INTO ordenes_compra 
    (orden_id, fecha_orden, nombre_organismo, descripcion_item, 
     producto_estandarizado, cantidad, unidad_medida, monto_total)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (orden_id) DO UPDATE SET
        cantidad = EXCLUDED.cantidad,
        monto_total = EXCLUDED.monto_total,
        updated_at = CURRENT_TIMESTAMP;
    """
    
    total_ordenes = 0
    
    # Por cada mes en los últimos 12 meses
    for mes_offset in range(12, 0, -1):
        fecha_mes = fecha_actual - timedelta(days=30 * mes_offset)
        mes_del_año = fecha_mes.month
        
        # Por cada hospital
        for hospital in hospitales:
            # Por cada producto
            for producto, config in productos_config.items():
                # Calcular demanda con tendencia, estacionalidad y ruido
                demanda_base = config['demanda_base']
                tendencia = config['tendencia_mensual'] * (12 - mes_offset)  # Crecimiento acumulado
                estacionalidad = config['estacionalidad'][mes_del_año - 1]
                factor_hospital = hospital_factor[hospital]
                
                # Demanda = base + tendencia, ajustada por estacionalidad y hospital
                demanda = (demanda_base + tendencia) * estacionalidad * factor_hospital
                
                # Agregar ruido aleatorio (±variabilidad%)
                ruido = random.uniform(-config['variabilidad'], config['variabilidad'])
                demanda = int(demanda + ruido)
                demanda = max(50, demanda)  # Mínimo 50 unidades
                
                # Generar descripción según producto
                if producto == 'APOSITOS':
                    descripcion = random.choice([
                        'APÓSITO 3M TRANSPARENTE ADHESIVO 5X5CM TEGADERM',
                        'APÓSITO ESPUMA ADHESIVO 10X10CM TEGADERM',
                        'APÓSITO FILM TRANSPARENTE TEGADERM ROLL'
                    ])
                    precio_unitario = random.uniform(800, 1500)
                else:  # GUANTES_MEDICOS
                    descripcion = random.choice([
                        'GUANTE LÁTEX ESTÉRIL TALLA M',
                        'GUANTE NITRILO SIN POLVO TALLA L',
                        'GUANTE QUIRÚRGICO ESTÉRIL TALLA 7.5'
                    ])
                    precio_unitario = random.uniform(500, 900)
                
                monto_total = int(demanda * precio_unitario)
                
                orden_id = f'OC-2024-{str(orden_counter).zfill(4)}'
                
                try:
                    cursor.execute(query, (
                        orden_id,
                        fecha_mes.date(),
                        hospital,
                        descripcion,
                        producto,
                        demanda,
                        'UNIDADES',
                        monto_total
                    ))
                    total_ordenes += 1
                    orden_counter += 1
                except Exception as e:
                    print(f"  ✗ Error en {orden_id}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"  ✓ {total_ordenes} órdenes históricas creadas (12 meses)")
    print(f"    - Con tendencia creciente mensual")
    print(f"    - Con estacionalidad (pico en invierno)")
    print(f"    - Con variabilidad realista por hospital")


def seed_predicciones():
    """
    Esta función ya no genera predicciones aleatorias.
    Las predicciones ahora se generarán con train_model.py usando el modelo entrenado.
    """
    print("\n📊 Las predicciones se generarán con train_model.py")
    print("    (usando datos históricos reales)")


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
