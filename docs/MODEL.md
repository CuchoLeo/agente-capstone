# Modelo Predictivo - Documentación Técnica

## Resumen

El sistema utiliza un modelo de **Regresión Lineal** con scikit-learn para predecir la demanda hospitalaria de insumos médicos basándose en datos históricos de órdenes de compra.

---

## Especificaciones del Modelo

### Tipo de Modelo
**Regresión Lineal (LinearRegression de scikit-learn)**

### Objetivo
Predecir la cantidad de unidades demandadas de un producto específico por un hospital específico en una fecha futura.

### Ecuación General

```
demanda = β₀ + β₁×días + β₂×sin(2π×mes/12) + β₃×cos(2π×mes/12) + 
          Σ(βᵢ×hospital_i) + Σ(βⱼ×producto_j)
```

Donde:
- **β₀** = Intercept (demanda base)
- **β₁** = Coeficiente de tendencia temporal
- **β₂, β₃** = Coeficientes de estacionalidad
- **βᵢ** = Coeficientes para cada hospital (one-hot)
- **βⱼ** = Coeficientes para cada producto (one-hot)

---

## Features (Variables Predictoras)

El modelo utiliza **12 features** en total:

### 1. Tendencia Temporal (1 feature)

**Variable:** `dias_desde_inicio`

**Cálculo:**
```python
dias_desde_inicio = (fecha_orden - fecha_referencia).days
```

**Fecha referencia:** 2024-01-01

**Propósito:** Capturar la tendencia general de crecimiento o decrecimiento en el tiempo.

**Ejemplo:**
- 2024-01-15 → 14 días
- 2024-06-10 → 161 días
- 2025-01-28 → 393 días

**Interpretación del coeficiente:**
- β₁ > 0: Demanda creciente en el tiempo
- β₁ < 0: Demanda decreciente
- β₁ ≈ 0: Sin tendencia temporal

---

### 2. Estacionalidad (2 features)

**Variables:** `mes_sin`, `mes_cos`

**Cálculo:**
```python
import numpy as np
mes = fecha_orden.month  # 1-12
mes_sin = np.sin(2 * np.pi * mes / 12)
mes_cos = np.cos(2 * np.pi * mes / 12)
```

**Propósito:** Capturar patrones cíclicos anuales (invierno/verano).

**Ventaja de usar sin/cos:**
- Permite que Diciembre (12) y Enero (1) sean considerados "cercanos"
- Captura ciclos continuos mejor que variable categórica

**Patrón esperado en Chile:**
- **Invierno (Junio-Agosto):** Mayor demanda de productos médicos (enfermedades respiratorias)
- **Verano (Diciembre-Febrero):** Menor demanda relativa

---

### 3. Hospital (Variable Categórica → 7 Features)

**Encoding:** One-Hot Encoding

**Hospitales en el sistema:**
1. Complejo Asistencial Dr. Sótero del Río
2. Hospital Barros Luco-Trudeau
3. Hospital Clínico U. de Chile
4. Hospital Clínico Universidad de Chile
5. Hospital del Salvador
6. Hospital San José
7. Hospital Sótero del Río

**Ejemplo de encoding:**
```python
# Para "Hospital del Salvador":
hospital_features = [0, 0, 0, 0, 1, 0, 0]

# Para "Hospital San José":
hospital_features = [0, 0, 0, 0, 0, 1, 0]
```

**Propósito:** Permitir que el modelo aprenda patrones específicos por hospital.

**Razón de diferencias:**
- Tamaño del hospital (camas, pacientes)
- Especialización médica
- Presupuesto disponible
- Frecuencia de compra

---

### 4. Producto (Variable Categórica → 2 Features)

**Encoding:** One-Hot Encoding

**Productos:**
1. APOSITOS
2. GUANTES_MEDICOS

**Ejemplo de encoding:**
```python
# Para "APOSITOS":
producto_features = [1, 0]

# Para "GUANTES_MEDICOS":
producto_features = [0, 1]
```

**Propósito:** Diferenciar niveles de demanda entre tipos de productos.

**Patrones observados:**
- **APOSITOS:** Demanda base ~180-250 unidades
- **GUANTES_MEDICOS:** Demanda base ~400-600 unidades (mayor consumo)

---

## Proceso de Entrenamiento

### 1. Carga de Datos

```python
# Desde PostgreSQL
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
```

**Datos actuales:**
- 124 registros históricos
- Rango: 2024-11-15 a 2025-11-29 (12 meses)
- 7 hospitales × 2 productos

---

### 2. Feature Engineering

```python
def _prepare_features(df):
    # Tendencia temporal
    df['dias_desde_inicio'] = (df['fecha_orden'] - fecha_ref).dt.days
    
    # Estacionalidad
    df['mes'] = df['fecha_orden'].dt.month
    df['mes_sin'] = np.sin(2 * np.pi * df['mes'] / 12)
    df['mes_cos'] = np.cos(2 * np.pi * df['mes'] / 12)
    
    # One-hot encoding
    hospital_encoded = encoder.fit_transform(df[['hospital']])
    producto_encoded = encoder.fit_transform(df[['producto']])
    
    # Combinar
    X = np.column_stack([
        dias, mes_sin, mes_cos, 
        hospital_encoded, producto_encoded
    ])
    
    y = df['cantidad'].values
    
    return X, y
```

---

### 3. Validación Train/Test

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, 
    test_size=0.20,  # 20% para test
    random_state=42   # Reproducibilidad
)
```

**Distribución:**
- Train: 99 registros (80%)
- Test: 25 registros (20%)

---

### 4. Entrenamiento

```python
from sklearn.linear_model import LinearRegression

model = LinearRegression()
model.fit(X_train, y_train)
```

**Output del entrenamiento:**
- Coeficientes (β): 12 valores
- Intercept (β₀): 1 valor

---

### 5. Evaluación

```python
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Predicciones
y_pred_train = model.predict(X_train)
y_pred_test = model.predict(X_test)

# Métricas
train_r2 = r2_score(y_train, y_pred_train)
test_r2 = r2_score(y_test, y_pred_test)
test_mae = mean_absolute_error(y_test, y_pred_test)
test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
```

---

## Métricas del Modelo

### Resultados Obtenidos

```
Dataset de Entrenamiento:
  R² (Train):    0.955
  MAE (Train):   30.1 unidades
  RMSE (Train):  37.3 unidades

Dataset de Test:
  R² (Test):     0.902 ⭐
  MAE (Test):    38.6 unidades ⭐
  RMSE (Test):   52.2 unidades ⭐

Configuración:
  Features:      12
  Samples:       124
  Train/Test:    80/20
```

### Interpretación de Métricas

#### R² (Coeficiente de Determinación)

**Valor:** 0.902 (Test)

**Significado:** El modelo explica el **90.2%** de la variabilidad en la demanda.

**Escala de interpretación:**
- R² > 0.9: Excelente
- 0.7 < R² < 0.9: Bueno
- 0.5 < R² < 0.7: Moderado
- R² < 0.5: Pobre

**Nuestro modelo:** Excelente predicción

---

#### MAE (Mean Absolute Error)

**Valor:** 38.6 unidades (Test)

**Significado:** En promedio, el modelo se equivoca por **±39 unidades**.

**Contexto:**
- Demanda promedio APOSITOS: ~200 unidades → Error ~19%
- Demanda promedio GUANTES: ~500 unidades → Error ~8%

**Interpretación:** Error aceptable dado el rango de demanda.

---

#### RMSE (Root Mean Squared Error)

**Valor:** 52.2 unidades (Test)

**Significado:** Penaliza más los errores grandes. RMSE > MAE indica que hay algunos outliers.

**Relación RMSE/MAE:** 52.2 / 38.6 = 1.35

**Interpretación:** Error distribuido razonablemente, sin outliers extremos.

---

## Proceso de Predicción

### Input

```python
hospital = "Hospital del Salvador"
producto = "APOSITOS"
fecha_prediccion = "2026-01-28"
```

### Procesamiento

1. **Calcular features:**
   ```python
   dias = (2026-01-28) - (2024-01-01) = 393 días
   mes = 1  # Enero
   mes_sin = sin(2π × 1/12) = 0.5
   mes_cos = cos(2π × 1/12) = 0.866
   hospital_encoding = [0, 0, 0, 0, 1, 0, 0]  # Salvador
   producto_encoding = [1, 0]  # Apósitos
   ```

2. **Aplicar modelo:**
   ```python
   X = [393, 0.5, 0.866, 0, 0, 0, 0, 1, 0, 0, 1, 0]
   demanda = model.predict(X)
   ```

3. **Post-procesamiento:**
   ```python
   demanda = max(0, round(demanda))  # No negativo, entero
   ```

### Output

```python
demanda_estimada = 205  # unidades
confidence_score = 90.2  # R² × 100
```

---

## Limitaciones y Consideraciones

### Limitaciones Actuales

1. **Asume relaciones lineales:**
   - No captura interacciones complejas entre variables
   - Puede fallar si hay cambios bruscos de tendencia

2. **Datos sintéticos:**
   - Modelo entrenado con datos generados, no reales de ChileCompra
   - Rendimiento puede variar con datos reales

3. **Features limitadas:**
   - No considera precio, competencia, eventos especiales
   - No incluye factores externos (pandemias, cambios regulatorios)

4. **Ventana temporal fija:**
   - Solo predice hasta 3 meses
   - No adaptado para predicciones a largo plazo (>6 meses)

---

### Mejoras Futuras

1. **Modelos más complejos:**
   - Random Forest (mejor para no-linealidades)
   - XGBoost (mayor precisión)
   - Prophet (especializado en series temporales)

2. **Más features:**
   - Precio histórico del producto
   - Eventos especiales (pandemias, emergencias)
   - Temporadas de licitaciones
   - Índices económicos

3. **Validación más robusta:**
   - Cross-validation temporal
   - Backtesting con datos reales
   - Métricas por segmento (hospital, producto)

4. **Reentrenamiento automático:**
   - Pipeline mensual de actualización
   - Detección de drift en el modelo

---

## Uso del Modelo

### Script de Entrenamiento

```bash
python scripts/training/train_model.py
```

**Salida:**
```
📊 Cargando datos históricos...
✅ 124 registros cargados

🧠 Entrenando modelo...
✅ Modelo entrenado - R² Test: 0.902

🔮 Generando predicciones...
✅ 42 predicciones generadas

💾 Guardando en BD...
✅ Proceso completado
```

---

### API de Predicción

```python
from src.predictor import DemandPredictor

# Cargar modelo entrenado
predictor = DemandPredictor.load_model()

# Predecir
demanda = predictor.predict(
    hospital="Hospital del Salvador",
    producto="APOSITOS",
    fecha_prediccion="2026-02-15"
)

print(f"Demanda estimada: {demanda} unidades")
```

---

## Referencias

- **scikit-learn Linear Regression:** https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html
- **Feature Engineering for Time Series:** https://www.kaggle.com/learn/feature-engineering
- **R² Interpretation:** https://statisticsbyjim.com/regression/interpret-r-squared-regression/

---

**Última actualización:** 2025-12-29
