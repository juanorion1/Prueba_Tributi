# Prueba Técnica – Sistema de Clasificación y Explicación de Tasación de Propiedades

## Objetivo
Diseñar e implementar una solución de IA end-to-end que combine:
- Machine Learning clásico para clasificación de propiedades.
- Una capa de control y sanitización de información.
- Un componente explicativo basado en LLMs.

El sistema busca detectar posibles inconsistencias en la clasificación de propiedades y generar explicaciones claras, estructuradas y seguras para distintos perfiles de usuario.

---

## Alcance
La solución cubre:
- Entrenamiento y evaluación de un modelo de clasificación.
- Identificación de casos con baja confianza en la clase registrada.
- Generación de alertas estructuradas.
- Explicaciones automáticas usando un modelo de lenguaje.
- Propuesta de evaluación del sistema completo.

---

## Estructura del proyecto
```text
.
├── notebooks/        # Notebooks con el desarrollo paso a paso
├── src/              # Funciones auxiliares (sanitización, validaciones, utilidades)
├── README.md
├── requirements.txt
