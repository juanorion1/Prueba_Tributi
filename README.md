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
├── data/
├── notebooks/
├── README.md
├── requirements.txt

### data/
- En esta carepta se debe de encontrar el archivo 2024_Property_Tax_Roll.csv

### notebooks/
- En la carpeta notebooks se encontrará todo el desarrollo realizado según lo pedido en la prueba.
- Para lograr ejecutar los notebooks, se debe tener la carpeta data creada
- El orden en el que se deben de ejecutar los notebooks para verificar la prueba, está dado por el número inicial del nombre.

--- 

# Método para validación de explicaciones de LLM (propuesta)
- Validación de datos en la salida:
  * Se debe validar id_propiedad, nivel_alerta sea el mismo que en la data original.
- Se propondrá un método de validación de métricas, donde se necesitará intervención humana si alguna está por debajo
de un límite pre-establecido.
- Las métricas a validar serían:
  * Groundedness: Verificar que no alucine.
  * Numeric Consistency: Teniendo en cuenta que estamos trabajando con probabilidades, esta métrica serviría para determinar si el modelo está interpretando bien estos resultados.
  * Rule Compliance: Validación de las reglas explícitas indicadas en el prompt.
  * Actionability: Determina si la recomendación ayuda a tomar decisiones.
  * Specificity Score: Determina si una decisión puede ser accionable o no.
  * Readability: Ayuda a determinar que el texto entregado sea entendible
  * Schema Validity: Detecta errores sintácticos en el formato
  * Field Completeness: Detecta si hay campus faltantes
- Estas métricas las dividiría en 3 secciones y tomaría la mediana entre ellas: 
  * Coherentes con los datos: Groundedness, Numeric Consistency, Rule Compliance.
  * Entendibles y accionables: Actionability, Specificity Score, Readability
  * Formato definido: Schema Validity, Field Completeness
- Para cada sección de las anteriores, les daría un peso según nivel de importancia. Propondría por ejemplo
  * peso_coherencia = 0.3
  * peso_entendible = 0.5
  * peso_formato = 0.2
- Definir un threshold a partir del cual un humanmo debería de verificar lo que está sucediendo.