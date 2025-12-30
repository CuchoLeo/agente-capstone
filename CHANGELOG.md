# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Planeado
- Integración con API de ChileCompra
- Sistema RAG con ChromaDB para documentos
- Deploy a Google Cloud Run
- Dashboard de analytics para vendedores
- Modelo más avanzado (XGBoost o Prophet)

---

## [0.2.0] - 2025-12-29

### Added
- ✨ **Modelo Predictivo con Machine Learning**
  - Implementación de regresión lineal con scikit-learn
  - R² de 0.902 (90.2% de precisión)
  - Features: tendencia temporal, estacionalidad, hospital, producto
  
- 📁 **Profesionalización del Repositorio**
  - Estructura de carpetas organizada (`/src`, `/scripts`, `/docs`)
  - Documentación completa del sistema
  - 5 diagramas Mermaid de arquitectura
  - Bitácora de desarrollo (BITACORA.md)
  
- 📊 **Datos Históricos Realistas**
  - Generación de 120 órdenes con tendencia y estacionalidad
  - Variabilidad por hospital y producto
  - Pico de demanda en invierno (junio-agosto)

- 📚 **Documentación Técnica**
  - `docs/ARCHITECTURE.md` - Arquitectura del sistema
  - `docs/API.md` - Documentación de endpoints
  - `docs/MODEL.md` - Explicación del modelo predictivo
  - `BITACORA.md` - Historial de desarrollo

- 🔧 **Scripts de Entrenamiento**
  - `train_model.py` - Pipeline completo de ML
  - `predictor.py` - Clase DemandPredictor
  - Persistencia de modelos con joblib

### Changed
- 🔄 Reemplazadas predicciones aleatorias por modelo entrenado
- 📝 Actualizado README.md con nueva estructura
- 🏗️ Reorganizada estructura de archivos para mayor profesionalismo

### Fixed
- 🐛 Corrección en generación de datos históricos con patrones realistas
- 🔧 Mejora en cálculo de confidence score (basado en R²)

---

## [0.1.0] - 2025-12-28

### Added
- 🚀 **Configuración Inicial del Proyecto**
  - Base de datos PostgreSQL en AWS RDS
  - Usuario específico `agente_app` con permisos
  - Database `agente_capstone_db`
  
- 🗄️ **Schema de Base de Datos**
  - Tabla `ordenes_compra` - Órdenes históricas
  - Tabla `predicciones_demanda` - Predicciones del modelo
  - Tabla `productos_solventum` - Catálogo de productos
  - Tabla `consultas_copiloto` - Log de consultas
  - Índices optimizados para queries

- 🤖 **Integración con Gemini (Vertex AI)**
  - Configuración de Vertex AI en GCP
  - Modelo: gemini-1.5-flash
  - System prompt especializado en predicción de demanda
  - Sesiones de chat por usuario

- 🌐 **Interfaz Web**
  - Flask como backend (puerto 8000)
  - Frontend HTML/CSS/JS personalizado
  - Chat en tiempo real con el agente
  - Quick questions predefinidas

- 🛠️ **API REST**
  - `/api/chat` - Conversación con agente
  - `/api/predictions` - Consultar predicciones
  - `/api/hospitals` - Listar hospitales
  - `/api/productos` - Listar productos
  - `/api/stats` - Estadísticas del sistema
  - `/health` - Health check

- 📝 **Scripts de Utilidad**
  - `setup_database.py` - Configuración inicial de BD
  - `seed_data.py` - Generación de datos de prueba
  - `start.sh` / `stop.sh` / `restart.sh` - Control del servidor
  - `status.sh` - Estado del servidor

### Security
- 🔒 Variables de entorno para credenciales (.env)
- 🚫 .gitignore configurado para archivos sensibles
- 🔐 Permisos mínimos en usuario de BD

---

## [0.0.1] - 2025-12-26

### Added
- 📋 Análisis de requisitos del proyecto
- 📐 Especificaciones técnicas
- 🏗️ Revisión de arquitectura base (agente-plastico)
- 📄 Documento de informe: Predicción Demanda Insumos Médicos.pdf

---

## Convenciones de Versionado

Este proyecto usa [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Cambios incompatibles con versiones anteriores
- **MINOR** (0.X.0): Nuevas funcionalidades compatibles
- **PATCH** (0.0.X): Correcciones de bugs

---

## Tipos de Cambios

- `Added` - Nuevas funcionalidades
- `Changed` - Cambios en funcionalidades existentes
- `Deprecated` - Funcionalidades próximas a ser removidas
- `Removed` - Funcionalidades removidas
- `Fixed` - Correcciones de bugs
- `Security` - Vulnerabilidades de seguridad

---

**Mantenido por:** CuchoLeo  
**Última actualización:** 2025-12-29
