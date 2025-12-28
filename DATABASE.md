# Configuración de Base de Datos PostgreSQL

Este directorio contiene los módulos de conexión y utilidades para la base de datos PostgreSQL en AWS RDS.

## 📋 Archivos

### `database.py`
Módulo principal de conexión a la base de datos. Incluye:
- Configuración de conexión a PostgreSQL (AWS RDS)
- Soporte para SQLAlchemy y psycopg2
- Funciones de test de conexión
- Pool de conexiones configurado

### `db_utils.py`
Utilidades y queries comunes:
- Creación de tablas del proyecto
- Funciones para insertar órdenes de compra
- Consultas de predicciones de demanda
- Gestión de catálogo de productos Solventum
- Logging de consultas del co-piloto

## 🔧 Configuración

### 1. Crear archivo `.env`
Copia `.env.example` a `.env` y completa las credenciales:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:
```env
DB_USER=tu_usuario
DB_PASSWORD=tu_password
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

## 🚀 Uso

### Test de conexión
```python
from database import test_connection

# Probar conexión
test_connection()
```

### Crear tablas
```python
from db_utils import create_tables

# Crear todas las tablas necesarias
create_tables()
```

### Ejemplos de uso

#### Insertar orden de compra
```python
from db_utils import insert_orden_compra

data = (
    "OC-123456",  # orden_id
    "2025-01-15",  # fecha_orden
    "Hospital del Salvador",  # nombre_organismo
    "APÓSITO 3M TRANSPARENTE ADHESIVO 5X5CM",  # descripcion_item
    "APOSITOS",  # producto_estandarizado
    100,  # cantidad
    "UNIDADES",  # unidad_medida
    250000  # monto_total
)

insert_orden_compra(data)
```

#### Consultar predicciones
```python
from db_utils import get_predicciones_hospital, get_top_demanda_producto

# Predicciones para un hospital
predicciones = get_predicciones_hospital("Hospital del Salvador", "APOSITOS")
print(predicciones)

# Top hospitales con mayor demanda
top_hospitales = get_top_demanda_producto("APOSITOS", limit=5)
print(top_hospitales)
```

#### Usando SQLAlchemy
```python
from database import get_session
from sqlalchemy import text

session = get_session()

# Query usando SQLAlchemy
result = session.execute(
    text("SELECT * FROM ordenes_compra LIMIT 10")
)

for row in result:
    print(row)

session.close()
```

#### Usando psycopg2 directo
```python
from database import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM ordenes_compra")
count = cursor.fetchone()[0]
print(f"Total órdenes: {count}")

cursor.close()
conn.close()
```

## 📊 Esquema de Base de Datos

### Tabla: `ordenes_compra`
Almacena órdenes de compra históricas de ChileCompra.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | SERIAL | ID autoincrementable |
| orden_id | VARCHAR(100) | ID único de la orden |
| fecha_orden | DATE | Fecha de la orden |
| nombre_organismo | VARCHAR(500) | Hospital/institución |
| descripcion_item | TEXT | Descripción original del ítem |
| producto_estandarizado | VARCHAR(200) | Producto estandarizado |
| cantidad | INTEGER | Cantidad solicitada |
| unidad_medida | VARCHAR(50) | Unidad (UNIDADES, CAJAS, etc) |
| monto_total | DECIMAL(15,2) | Monto total en CLP |

### Tabla: `predicciones_demanda`
Almacena predicciones generadas por el modelo.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | SERIAL | ID autoincrementable |
| hospital | VARCHAR(500) | Nombre del hospital |
| producto | VARCHAR(200) | Producto estandarizado |
| fecha_prediccion | DATE | Fecha de la predicción |
| demanda_estimada | INTEGER | Unidades estimadas |
| confidence_score | DECIMAL(5,2) | Score de confianza (0-100) |

### Tabla: `productos_solventum`
Catálogo de productos Solventum.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | SERIAL | ID autoincrementable |
| codigo_producto | VARCHAR(100) | Código único del producto |
| nombre_producto | VARCHAR(300) | Nombre del producto |
| categoria | VARCHAR(100) | Categoría (APOSITOS, GUANTES, etc) |
| descripcion | TEXT | Descripción detallada |
| palabras_clave | TEXT[] | Array de palabras clave |

### Tabla: `consultas_copiloto`
Log de consultas al asistente de IA.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | SERIAL | ID autoincrementable |
| usuario | VARCHAR(100) | Usuario que hizo la consulta |
| consulta | TEXT | Pregunta del usuario |
| respuesta | TEXT | Respuesta del asistente |
| timestamp | TIMESTAMP | Fecha y hora de la consulta |

## 🔒 Seguridad

- **NUNCA** subir el archivo `.env` a Git
- Usar variables de entorno en producción (Cloud Run secrets)
- Mantener credenciales seguras
- Usar SSL para conexiones en producción

## 📌 Conexión

**Host:** `db-capstonemia.c43jwggkkhqo.us-east-2.rds.amazonaws.com`  
**Puerto:** `5432`  
**Base de datos:** `postgres`  
**Región AWS:** `us-east-2`  
**URL JDBC:** `jdbc:postgresql://db-capstonemia.c43jwggkkhqo.us-east-2.rds.amazonaws.com:5432/postgres`
