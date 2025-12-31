PROMPT_DETALLE_TECNICO = """
El siguiente descripción técnica muestra las descripciones de las variables entregadas para el análisis.

### Campos raíz
- **`id_propiedad`**: Identificador de la propiedad (`P_ID`).
- **`nivel_alerta`**: Nivel de alerta pre-asignado por la lógica del sistema. Valores esperados: `"BAJA"`, `"MEDIA"`, `"ALTA"`, `"CRITICA"`.

### Identificación del usuario
- **`name`**: Nombre del usuario del registro
- **`lastname`**: Apellido del usuario del registro
- **`address`**: Dirección de residencia del usuario del registro
---

### `modelo` (señales del modelo predictivo)
- **`class_registrada`**: Clase oficial registrada (`CLASS`).
- **`class_predicha`**: Clase predicha por el modelo (`pred_class`).
- **`class_pred_top1`**: Clase top-1 según el diccionario de probabilidades top-5 (útil si se guardan solo top-k).
- **`p_true`**: Probabilidad asignada por el modelo a la **clase registrada**.
- **`p_pred_max`**: Probabilidad máxima (clase top-1).
- **`p_margin`**: Diferencia `p_pred_max - p_true`. Indica conflicto entre registro y predicción.
- **`top_k`**: Top 3 clases con sus probabilidades: `[(clase, prob), ...]`.

**Interpretación típica:**
- `p_true` bajo + `p_margin` alto ⇒ alta probabilidad de inconsistencia (registro no “parece” de esa clase).
- `p_true` alto ⇒ el registro es consistente con el modelo.

---

### `tributario` (evidencia cuantitativa)
- **`total_assmt`**: Valor tasado (`TOTAL_ASSMT`).
- **`total_exempt`**: Exenciones (`TOTAL_EXEMPT`).
- **`total_taxes`**: Impuestos totales (`TOTAL_TAXES`).
- **`tax_rate`**: Tasa efectiva estimada: `TOTAL_TAXES / max(TOTAL_ASSMT, 1)`.
- **`exempt_rate`**: Proporción exenta estimada: `TOTAL_EXEMPT / max(TOTAL_ASSMT, 1)`.
- **`assmt_pct_in_class_reg`**: Percentil empírico de `TOTAL_ASSMT` dentro de la clase registrada.
- **`taxes_pct_in_class_reg`**: Percentil empírico de `TOTAL_TAXES` dentro de la clase registrada.
- **`exempt_pct_in_class_reg`**: Percentil empírico de `TOTAL_EXEMPT` dentro de la clase registrada.
- **`flags`**: Banderas de inconsistencia tributaria.

#### Flags implementadas (actuales)
- **`exencion_mayor_que_avaluo`**: `TOTAL_EXEMPT > TOTAL_ASSMT`.
- **`impuesto_cero_con_avaluo_positivo`**: `TOTAL_TAXES == 0` y `TOTAL_ASSMT > 0`.
- **`avaluo_extremo_para_clase`**: `assmt_pct_in_class_reg >= 0.99` (avalúo extremo vs su clase registrada).

---

### `ubicacion` (contexto geográfico sin PII)
- **`zip`**: Código postal (`ZIP_POSTAL`).
- **`geo_cluster`**: Cluster geográfico precomputado (agrupación espacial).

---

### `administrativo` (contexto de régimen/levy)
- **`levy_code_1`**: Código de levy (`LEVY_CODE_1`).

---

### `descripcion` (contexto semántico)
- **`short_desc`**: Descripción corta de la propiedad (`SHORT_DESC`).

"""

PROMPT_INSTRUCCIONES = """
Tu tarea es generar un motivo y una recomendacion apartir de información tributaria, al igual que del resultado
de un modelo de clasificación de usuarios, donde se genera un nivel de alerta según la probabilidad de pertenecer
a uno de los grupos particulares.

## Nivel de alerta
El nivel de alerta está dividido en 4 tipos: CRITICO, ALTO, MEDIANO y BAJO, donde CRITICO tiene la probabilidad más baja
de todas, mientras que BAJO tiene la probabilidad más alta de todas.

## Generación de `motivo` y `recomendacion`
- Teniendo en cuenta que se tiene la probabilidad de pertenencia a un grupo particular, se quiere generar un `motivo` y una `recomendacion` 
al respecto de esta probabilidad.  
- La generación de estas explicaciones tienen que estar basada en los datos proporcionados, teniendo en cuenta también el 
contexto que se te dio inicialmente.
- Puedes ser imaginativo con las razones que vas a dar, pero debes de basarte principalmente en los datos.
- Estas variables serían usadas en la sección **Formato Salida**

## Uso esperado por el LLM
El LLM debe basar el `motivo_tecnico` y la `recomendacion` en:
1. Señales del modelo (`p_true`, `p_pred_max`, `p_margin`, `top_k`, conflicto entre `class_registrada` y `class_predicha`).
2. Evidencia tributaria (montos, ratios, percentiles y `flags`).
3. Contexto adicional (ZIP/cluster, levy, short_desc).

## Diccionario de información
- El siguiente diccionario cuenta con el detalle técnico de cada registro de la información tributaria. 
- La descripción de cada variable en el diccionario se encontará en la sección **Descripción técnica**

- {info_tecnica}

## Descripción técnica
{PROMPT_DETALLE_TECNICO}

## Consideraciones
- Para determinar si un valor de probabilidad es alto, o bajo, vas a utilizar los valores entregados en grupos_p_true.
- Puedes ser imaginativo en tus respuestas, pero DEBES DE BASARTE ÚNICAMENTE en los datos proporcionados
- Las explicaciones deben de ser entendibles y accionables para analistas, equipo de planeación urbana y directivos.
  * Por esta razón las razones que se den no pueden ser muy técnicas, pero tampoco muy sencillas.  Debe tener un buen nivel explicativo
- Si consideras necesario, utiliza los nombres y direcciones proporcionadas.

## Formato de salida
- Debes de entregar la salida en el siguiente formato json:
    {{
        "id_propiedad": id_propiedad,
        "nivel_alerta": nivel_alerta,
        "motivo": motivo,
        "recomendacion": recomendacion
    }}

- No debes de entregar tu análisis, solo lo que se te pide

## Ejemplos

"""
