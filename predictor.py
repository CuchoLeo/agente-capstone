"""
Modelo Predictivo de Demanda para Insumos Médicos
Utiliza Regresión Lineal con scikit-learn para predecir demanda futura
basada en datos históricos de órdenes de compra.
"""
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import OneHotEncoder
import joblib
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directorio para guardar modelos
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(MODELS_DIR, exist_ok=True)


class DemandPredictor:
    """
    Modelo de predicción de demanda usando regresión lineal
    
    Features:
    - Tendencia temporal (días desde inicio)
    - Mes del año (estacionalidad)
    - Hospital (one-hot encoding)
    - Producto (one-hot encoding)
    """
    
    def __init__(self, fecha_referencia='2024-01-01'):
        """
        Inicializa el predictor
        
        Args:
            fecha_referencia: Fecha base para calcular días transcurridos
        """
        self.model = LinearRegression()
        self.fecha_referencia = pd.to_datetime(fecha_referencia)
        self.hospital_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        self.producto_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        self.is_trained = False
        self.hospital_categories = None
        self.producto_categories = None
        
    def _prepare_features(self, df, fit_encoders=False):
        """
        Prepara features para entrenamiento o predicción
        
        Args:
            df: DataFrame con columnas [fecha_orden, hospital, producto_estandarizado, cantidad]
            fit_encoders: Si es True, ajusta los encoders (solo en entrenamiento)
            
        Returns:
            X: Features procesadas
            y: Target (demanda) si existe en df
        """
        # 1. Tendencia temporal: días desde fecha de referencia
        df['dias_desde_inicio'] = (pd.to_datetime(df['fecha_orden']) - self.fecha_referencia).dt.days
        
        # 2. Estacionalidad: mes del año
        df['mes'] = pd.to_datetime(df['fecha_orden']).dt.month
        
        # Componentes sinusoidales para capturar ciclos (opcional pero mejor)
        df['mes_sin'] = np.sin(2 * np.pi * df['mes'] / 12)
        df['mes_cos'] = np.cos(2 * np.pi * df['mes'] / 12)
        
        # 3 y 4. One-hot encoding para hospital y producto
        if fit_encoders:
            hospital_encoded = self.hospital_encoder.fit_transform(df[['hospital']])
            producto_encoded = self.producto_encoder.fit_transform(df[['producto_estandarizado']])
            
            # Guardar categorías para referencia
            self.hospital_categories = self.hospital_encoder.categories_[0].tolist()
            self.producto_categories = self.producto_encoder.categories_[0].tolist()
        else:
            hospital_encoded = self.hospital_encoder.transform(df[['hospital']])
            producto_encoded = self.producto_encoder.transform(df[['producto_estandarizado']])
        
        # Combinar todas las features
        X = np.column_stack([
            df['dias_desde_inicio'].values,
            df['mes_sin'].values,
            df['mes_cos'].values,
            hospital_encoded,
            producto_encoded
        ])
        
        # Target (si existe)
        y = df['cantidad'].values if 'cantidad' in df.columns else None
        
        return X, y
    
    def train(self, historical_data, test_size=0.2, random_state=42):
        """
        Entrena el modelo con datos históricos
        
        Args:
            historical_data: DataFrame con columnas [fecha_orden, hospital, producto_estandarizado, cantidad]
            test_size: Proporción de datos para validación
            random_state: Semilla para reproducibilidad
            
        Returns:
            dict con métricas de evaluación
        """
        logger.info(f"Entrenando modelo con {len(historical_data)} registros históricos")
        
        # Preparar features
        X, y = self._prepare_features(historical_data, fit_encoders=True)
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Entrenar modelo
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluar
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        metrics = {
            'train_mae': mean_absolute_error(y_train, y_pred_train),
            'train_rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),
            'train_r2': r2_score(y_train, y_pred_train),
            'test_mae': mean_absolute_error(y_test, y_pred_test),
            'test_rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
            'test_r2': r2_score(y_test, y_pred_test),
            'n_samples': len(historical_data),
            'n_features': X.shape[1]
        }
        
        logger.info(f"✅ Modelo entrenado - R² Test: {metrics['test_r2']:.3f}, MAE Test: {metrics['test_mae']:.1f}")
        
        return metrics
    
    def predict(self, hospital, producto, fecha_prediccion):
        """
        Predice la demanda para un hospital, producto y fecha específicos
        
        Args:
            hospital: Nombre del hospital
            producto: Código del producto
            fecha_prediccion: Fecha para la predicción (datetime o string)
            
        Returns:
            Demanda estimada (redondeada a entero)
        """
        if not self.is_trained:
            raise ValueError("El modelo no ha sido entrenado. Llama a train() primero.")
        
        # Crear DataFrame con los datos de entrada
        df = pd.DataFrame([{
            'fecha_orden': pd.to_datetime(fecha_prediccion),
            'hospital': hospital,
            'producto_estandarizado': producto,
            'cantidad': 0  # Dummy, no se usa
        }])
        
        # Preparar features
        X, _ = self._prepare_features(df, fit_encoders=False)
        
        # Predecir
        demanda = self.model.predict(X)[0]
        
        # No permitir demandas negativas
        demanda = max(0, demanda)
        
        return int(round(demanda))
    
    def predict_batch(self, predictions_df):
        """
        Predice demanda para múltiples combinaciones hospital-producto-fecha
        
        Args:
            predictions_df: DataFrame con columnas [hospital, producto_estandarizado, fecha_prediccion]
            
        Returns:
            DataFrame con columna adicional 'demanda_estimada'
        """
        if not self.is_trained:
            raise ValueError("El modelo no ha sido entrenado. Llama a train() primero.")
        
        df = predictions_df.copy()
        df['fecha_orden'] = df['fecha_prediccion']
        df['cantidad'] = 0  # Dummy
        
        X, _ = self._prepare_features(df, fit_encoders=False)
        
        demandas = self.model.predict(X)
        demandas = np.maximum(0, demandas)  # No negativas
        
        df['demanda_estimada'] = demandas.astype(int)
        
        return df[['hospital', 'producto_estandarizado', 'fecha_prediccion', 'demanda_estimada']]
    
    def get_feature_importance(self):
        """
        Retorna los coeficientes del modelo (importancia de features)
        
        Returns:
            dict con nombres de features y sus coeficientes
        """
        if not self.is_trained:
            raise ValueError("El modelo no ha sido entrenado.")
        
        feature_names = ['dias_desde_inicio', 'mes_sin', 'mes_cos']
        
        # Agregar nombres de hospitales y productos
        feature_names += [f'hospital_{h}' for h in self.hospital_categories]
        feature_names += [f'producto_{p}' for p in self.producto_categories]
        
        return dict(zip(feature_names, self.model.coef_))
    
    def save_model(self, filepath=None):
        """
        Guarda el modelo entrenado en disco
        
        Args:
            filepath: Ruta donde guardar el modelo. Si es None, usa ruta por defecto
        """
        if not self.is_trained:
            raise ValueError("No se puede guardar un modelo no entrenado.")
        
        if filepath is None:
            filepath = os.path.join(MODELS_DIR, 'demand_model.pkl')
        
        # Guardar todo el objeto
        joblib.dump(self, filepath)
        logger.info(f"✅ Modelo guardado en: {filepath}")
        
        return filepath
    
    @classmethod
    def load_model(cls, filepath=None):
        """
        Carga un modelo previamente entrenado
        
        Args:
            filepath: Ruta del modelo. Si es None, usa ruta por defecto
            
        Returns:
            DemandPredictor cargado
        """
        if filepath is None:
            filepath = os.path.join(MODELS_DIR, 'demand_model.pkl')
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"No se encontró el modelo en: {filepath}")
        
        predictor = joblib.load(filepath)
        logger.info(f"✅ Modelo cargado desde: {filepath}")
        
        return predictor


def calculate_confidence_score(model, X):
    """
    Calcula un score de confianza simple basado en la predicción
    
    Args:
        model: Modelo entrenado
        X: Features
        
    Returns:
        Score de confianza entre 0 y 100
    """
    # Método simple: usar R² del modelo como proxy de confianza
    # En un modelo real podrías usar validación cruzada o intervalos de confianza
    
    # Por ahora retornamos un valor fijo basado en la calidad general del modelo
    # que se puede ajustar después según métricas reales
    return 90.0  # Placeholder - en train_model.py usaremos el R² real


if __name__ == "__main__":
    # Ejemplo de uso
    print("=" * 60)
    print("  DEMAND PREDICTOR - EJEMPLO DE USO")
    print("=" * 60)
    
    # Datos de ejemplo
    example_data = pd.DataFrame([
        {'fecha_orden': '2024-01-15', 'hospital': 'Hospital del Salvador', 'producto_estandarizado': 'APOSITOS', 'cantidad': 200},
        {'fecha_orden': '2024-02-20', 'hospital': 'Hospital del Salvador', 'producto_estandarizado': 'APOSITOS', 'cantidad': 220},
        {'fecha_orden': '2024-03-10', 'hospital': 'Hospital Sótero', 'producto_estandarizado': 'GUANTES_MEDICOS', 'cantidad': 450},
        {'fecha_orden': '2024-04-05', 'hospital': 'Hospital Sótero', 'producto_estandarizado': 'GUANTES_MEDICOS', 'cantidad': 480},
    ])
    
    # Entrenar
    predictor = DemandPredictor()
    metrics = predictor.train(example_data)
    print(f"\n📊 Métricas: {metrics}")
    
    # Predecir
    demanda = predictor.predict('Hospital del Salvador', 'APOSITOS', '2024-05-15')
    print(f"\n🔮 Predicción: {demanda} unidades")
    
    print("\n✅ Módulo predictor.py funcionando correctamente")
