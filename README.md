# Agente Capstone: Predicción de Demanda de Insumos Médicos

> **Co-piloto de Ventas Inteligente para Solventum**

Sistema de inteligencia artificial que predice la demanda hospitalaria de insumos médicos en Chile, optimizando la estrategia comercial mediante análisis predictivo de datos públicos de ChileCompra.

---

## 🎯 Descripción

Este proyecto desarrolla un **asistente conversacional basado en IA** que permite a los vendedores de Solventum consultar predicciones de demanda hospitalaria en lenguaje natural, transformando datos públicos caóticos en decisiones tácticas accionables.

### Problema que Resuelve
- **Reducción 80%** en tiempo de análisis manual (de 1 día/semana → automatizado)
- **Targeting preciso** por hospital y producto
- **Anticipación** de ciclos de compra antes de la licitación
- **Visibilidad** de consumo real y competencia

### Innovación Principal
1. **Estandarización Semántica:** Motor NLP que procesa descripciones en texto libre de órdenes de compra
2. **Predicción Granular:** Estimación de demanda por producto × hospital × período
3. **Co-piloto Conversacional:** Interfaz en lenguaje natural para consultar predicciones

---

## 🏗️ Arquitectura Técnica

### Stack Core
- **Backend:** Flask (Python 3.11+)
- **LLM:** Google Vertex AI (Gemini)
- **Vector Database:** ChromaDB
- **Embeddings:** Google AI Embeddings, Paraphrase Multilingual MiniLM L12 V2
- **Storage:** Google Cloud Storage
- **Deployment:** Google Cloud Run (us-central1)

### Pipeline de Datos
```
ChileCompra (OC históricas)
    ↓
Limpieza y Normalización
    ↓
Estandarización Semántica (RegEx + Embeddings)
    ↓
Matching con Catálogo Solventum (Similitud Coseno >0.85)
    ↓
Análisis de Series Temporales
    ↓
Modelo Predictivo (Demanda por Hospital × Producto)
    ↓
Sistema RAG (ChromaDB)
    ↓
Asistente Conversacional (Gemini)
```

### Validación
- **Precisión del modelo de estandarización:** 95% (validado con 400 registros)
- **Metodología:** Human-in-the-loop con expertos de Solventum

---

## 🚀 Características Principales

### 1. Estandarización de Productos
Procesa descripciones en texto libre como:
```
"APÓSITO 3M TRANSPARENTE ADHESIVO 5 X 5,7 CMS TEGADERM I.V."
→ "APOSITOS"
```

### 2. Predicción de Demanda
- Granularidad: **Hospital × Producto × Tiempo**
- Productos ejemplo: Apósitos, Guantes Médicos, Film Transparente
- Volúmenes: Hasta 2M+ unidades mensuales por hospital

### 3. Co-piloto de Ventas
Consultas en lenguaje natural:
- *"¿Cuál es el hospital con mayor demanda proyectada de apósitos para el próximo mes?"*
- *"Muestra tendencia de guantes médicos en Hospital del Salvador"*
- *"Identifica oportunidades en apósitos transparentes en Región Metropolitana"*

### 4. Inteligencia de Competencia
- Identifica productos de competencia (Opsite, Leucomed, etc.)
- Visibilidad de share de mercado por categoría

---

## 📊 Resultados Esperados

| Métrica | Antes | Después |
|---------|-------|---------|
| Tiempo de análisis semanal | 8 horas | <2 horas |
| Precisión de targeting | Basado en intuición | 95% precisión |
| Visibilidad de mercado | Limitada | Competencia + Solventum |
| Decisiones | Reactivas | Proactivas |
| Aumento en ventas (reportado) | Baseline | +16% anual |

---

## 🔄 Basado en

Este proyecto adapta la arquitectura de [agente-plastico](https://github.com/CuchoLeo/agente-plastico) (RAG + Vertex AI + ChromaDB) especializado para el dominio de predicción de demanda de insumos médicos.

---

## 📂 Estructura del Proyecto

```
agente-capstone/
├── app.py                    # Aplicación Flask principal
├── storage.py                # Gestión de GCS y ChromaDB
├── config.py                 # Configuración y parámetros
├── requirements.txt          # Dependencias Python
├── Dockerfile                # Containerización
├── docs/                     # Documentación del proyecto
│   └── Ultima_verion-Informe - Predicción Demanda Insumos Médicos.pdf
├── scripts/                  # Scripts de deployment e indexación
├── static/                   # Archivos estáticos (CSS, JS)
└── templates/                # Templates HTML
```

---

## 🛠️ Estado del Proyecto

🚧 **En desarrollo**

### Completado
- [x] Análisis de requisitos
- [x] Especificaciones técnicas
- [x] Revisión de arquitectura base (agente-plastico)

### En Progreso
- [ ] Implementación de pipeline de estandarización
- [ ] Modelo predictivo de series temporales
- [ ] Sistema RAG con ChromaDB
- [ ] Interfaz conversacional

### Pendiente
- [ ] Deployment a Cloud Run
- [ ] Testing y validación
- [ ] Documentación de usuario

---

## 👥 Autor

**CuchoLeo**

---

*Última actualización: 2025-12-28*
