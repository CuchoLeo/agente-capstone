"""
Script para entrenar el modelo de predicción de demanda
y generar predicciones para los próximos meses
"""
import pandas as pd
from datetime import datetime, timedelta
from database import get_connection
from predictor import DemandPredictor
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_historical_data():
    """
    Carga datos históricos de órdenes de compra desde la BD
    
    Returns:
        DataFrame con columnas necesarias para el entrenamiento
    """
    logger.info("📊 Cargando datos históricos desde la base de datos...")
    
    conn = get_connection()
    
    query = """
    SELECT 
        fecha_orden,
        nombre_organismo as hospital,
        producto_estandarizado,
        cantidad
    FROM ordenes_compra
    ORDER BY fecha_orden
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    logger.info(f"✅ {len(df)} registros históricos cargados")
    logger.info(f"   Rango de fechas: {df['fecha_orden'].min()} a {df['fecha_orden'].max()}")
    logger.info(f"   Hospitales: {df['hospital'].nunique()}")
    logger.info(f"   Productos: {df['producto_estandarizado'].nunique()}")
    
    return df


def train_model(historical_data):
    """
    Entrena el modelo de predicción con los datos históricos
    
    Args:
        historical_data: DataFrame con datos históricos
        
    Returns:
        DemandPredictor entrenado
    """
    logger.info("\n🧠 Entrenando modelo de predicción...")
    
    predictor = DemandPredictor(fecha_referencia='2024-01-01')
    metrics = predictor.train(historical_data, test_size=0.2)
    
    logger.info("\n📈 Métricas del modelo:")
    logger.info(f"  Train R²: {metrics['train_r2']:.3f}")
    logger.info(f"  Train MAE: {metrics['train_mae']:.1f}")
    logger.info(f"  Train RMSE: {metrics['train_rmse']:.1f}")
    logger.info(f"\n  Test R²: {metrics['test_r2']:.3f} ⭐")
    logger.info(f"  Test MAE: {metrics['test_mae']:.1f} ⭐")
    logger.info(f"  Test RMSE: {metrics['test_rmse']:.1f} ⭐")
    logger.info(f"\n  Features: {metrics['n_features']}")
    logger.info(f"  Samples: {metrics['n_samples']}")
    
    # Guardar modelo
    model_path = predictor.save_model()
    logger.info(f"\n💾 Modelo guardado en: {model_path}")
    
    return predictor, metrics


def generate_predictions(predictor, n_months=3):
    """
    Genera predicciones para los próximos N meses
    
    Args:
        predictor: DemandPredictor entrenado
        n_months: Número de meses a predecir
        
    Returns:
        DataFrame con predicciones
    """
    logger.info(f"\n🔮 Generando predicciones para los próximos {n_months} meses...")
    
    # Obtener hospitales y productos únicos de la BD
    conn = get_connection()
    
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT nombre_organismo FROM ordenes_compra ORDER BY nombre_organismo")
    hospitales = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT producto_estandarizado FROM ordenes_compra ORDER BY producto_estandarizado")
    productos = [row[0] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    # Generar combinaciones para predicción
    predictions = []
    base_date = datetime.now()
    
    for month_offset in range(1, n_months + 1):
        fecha_pred = base_date + timedelta(days=30 * month_offset)
        
        for hospital in hospitales:
            for producto in productos:
                predictions.append({
                    'hospital': hospital,
                    'producto_estandarizado': producto,
                    'fecha_prediccion': fecha_pred
                })
    
    predictions_df = pd.DataFrame(predictions)
    
    # Generar predicciones
    results = predictor.predict_batch(predictions_df)
    
    logger.info(f"✅ {len(results)} predicciones generadas")
    
    return results


def save_predictions_to_db(predictions_df, confidence_score):
    """
    Guarda las predicciones en la tabla predicciones_demanda
    
    Args:
        predictions_df: DataFrame con predicciones
        confidence_score: Score de confianza del modelo (R² * 100)
    """
    logger.info("\n💾 Guardando predicciones en la base de datos...")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Limpiar predicciones antiguas
    cursor.execute("DELETE FROM predicciones_demanda")
    logger.info("  🗑️ Predicciones antiguas eliminadas")
    
    # Insertar nuevas predicciones
    query = """
    INSERT INTO predicciones_demanda 
    (hospital, producto, fecha_prediccion, demanda_estimada, confidence_score)
    VALUES (%s, %s, %s, %s, %s)
    """
    
    total_inserted = 0
    for _, row in predictions_df.iterrows():
        try:
            cursor.execute(query, (
                row['hospital'],
                row['producto_estandarizado'],
                row['fecha_prediccion'],
                int(row['demanda_estimada']),
                round(confidence_score, 2)
            ))
            total_inserted += 1
        except Exception as e:
            logger.error(f"  ✗ Error insertando predicción: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    logger.info(f"✅ {total_inserted} predicciones guardadas en la BD")


def show_sample_predictions(predictions_df, n_samples=10):
    """
    Muestra algunas predicciones de ejemplo
    
    Args:
        predictions_df: DataFrame con predicciones
        n_samples: Número de muestras a mostrar
    """
    logger.info(f"\n📋 Muestra de predicciones generadas:")
    logger.info("=" * 100)
    
    sample = predictions_df.head(n_samples)
    
    for _, row in sample.iterrows():
        logger.info(f"  {row['hospital'][:30]:30} | {row['producto_estandarizado']:20} | "
                   f"{row['fecha_prediccion'].strftime('%Y-%m-%d')} | {row['demanda_estimada']:4d} unidades")
    
    logger.info("=" * 100)
    
    # Estadísticas
    logger.info(f"\n📊 Estadísticas de predicciones:")
    logger.info(f"  Demanda promedio: {predictions_df['demanda_estimada'].mean():.1f} unidades")
    logger.info(f"  Demanda mínima: {predictions_df['demanda_estimada'].min()} unidades")
    logger.info(f"  Demanda máxima: {predictions_df['demanda_estimada'].max()} unidades")


def main():
    """
    Flujo principal de entrenamiento y generación de predicciones
    """
    print("\n" + "=" * 80)
    print("  ENTRENAMIENTO DE MODELO PREDICTIVO - AGENTE CAPSTONE")
    print("=" * 80 + "\n")
    
    try:
        # 1. Cargar datos históricos
        historical_data = load_historical_data()
        
        if len(historical_data) < 50:
            logger.warning("⚠️  Pocos datos históricos. Se recomienda tener al menos 50 registros.")
            logger.warning("   Ejecuta: python seed_data.py")
            return
        
        # 2. Entrenar modelo
        predictor, metrics = train_model(historical_data)
        
        # Verificar calidad del modelo
        if metrics['test_r2'] < 0.5:
            logger.warning(f"⚠️  R² bajo ({metrics['test_r2']:.3f}). El modelo puede no ser muy preciso.")
            logger.warning("   Considera agregar más datos históricos o ajustar features.")
        
        # 3. Generar predicciones para próximos 3 meses
        predictions = generate_predictions(predictor, n_months=3)
        
        # 4. Mostrar muestras
        show_sample_predictions(predictions)
        
        # 5. Guardar predicciones en BD
        # Usar R² del test como confianza (convertir a porcentaje)
        confidence = max(0, min(100, metrics['test_r2'] * 100))
        save_predictions_to_db(predictions, confidence)
        
        print("\n" + "=" * 80)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 80)
        print(f"\n📊 Resumen:")
        print(f"   • Modelo entrenado con {len(historical_data)} registros")
        print(f"   • R² (Test): {metrics['test_r2']:.3f}")
        print(f"   • MAE (Test): {metrics['test_mae']:.1f} unidades")
        print(f"   • {len(predictions)} predicciones generadas y guardadas")
        print(f"   • Confianza promedio: {confidence:.1f}%")
        print(f"\n🚀 El agente ya puede consultar las predicciones del modelo real")
        print(f"   Inicia la app: python app.py\n")
        
    except Exception as e:
        logger.error(f"\n❌ Error en el proceso: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
