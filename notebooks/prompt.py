PROMPT_DETALLE_TECNICO = """
El siguiente descripción técnica muestra las descripciones de las variables entregadas para el análisis.

### Campos raíz
- **`id_propiedad`**: Identificador de la propiedad (`P_ID`).
- **`nivel_alerta`**: Nivel de alerta pre-asignado por la lógica del sistema. Valores esperados: `"BAJA"`, `"MEDIA"`, `"ALTA"`, `"CRITICA"`.

### Identificación del usuario
- **`fullname`**: Nombre del usuario del registro
- **`address`**: Dirección de residencia del usuario del registro
---

### `modelo` (señales del modelo predictivo)
- **`class_registrada`**: Clase oficial registrada (`CLASS`).
- **`class_predicha`**: Clase predicha por el modelo (`pred_class`).
- **`class_pred_top1`**: Clase top-1 según el diccionario de probabilidades top-5 (útil si se guardan solo top-k).
- **`p_true`**: Probabilidad asignada por el modelo a la **clase registrada**.
- **`p_pred_max`**: Probabilidad máxima (clase top-1).
- **`p_margin`**: Diferencia `p_pred_max - p_true`. Indica conflicto entre registro y predicción.
- **`top_k`**: Top 5 clases con sus probabilidades: `[(clase, prob), ...]`.

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
Tu tarea es generar un motivo y una recomendacion a partir de información tributaria, al igual que del resultado
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

## Uso esperado por el modelo
El modelo debe basar el `motivo` y la `recomendacion` en:
- Todo lo que considere útil para formar la explicación que aparezca en la información de la sección **Descripción técnica**

## Diccionario de información
- El siguiente diccionario(info_tecnica) cuenta con el detalle técnico de cada registro de la información tributaria. 
- La descripción de cada variable en el diccionario se encontará en la sección **Descripción técnica**
- info_tecnica = __INFO__TECNICA__

## Descripción técnica
__PROMPT_DETALLE_TECNICO__

## Consideraciones
- Para determinar si un valor de probabilidad es alto, o bajo, vas a utilizar los valores entregados en grupos_p_true.
- Puedes ser imaginativo en tus respuestas, pero DEBES DE BASARTE ÚNICAMENTE en los datos proporcionados
- Las explicaciones deben de ser entendibles y accionables para analistas, equipo de planeación urbana y directivos.
  * Por este motivo las razones que se den no pueden ser muy técnicas, pero tampoco muy sencillas.
- Si consideras necesario, utiliza los nombres y direcciones proporcionadas, pero esta información no sería del todo necesaria.

## Formato de salida
- Debes de entregar la salida en el siguiente formato json:
    {
        "id_propiedad": id_propiedad,
        "nivel_alerta": nivel_alerta,
        "motivo": motivo,
        "recomendacion": recomendacion
    }

- BAJO NINGUNA CIRCUNSTANCIA debes de entregar tu análisis, ÚNICAMENTE VAS A ENTREGAR lo que se te pide

## Ejemplos
Los siguientes ejemplos muestran la manera en como se te entregará la información y la manera en como debes entregarla.
### Ejemplo 1
info_tecnica = 
{'id_propiedad': 3386, 'nivel_alerta': 'BAJA', 'grupos_p_true': {'median': {'ALTA': 0.813552475, 'BAJA': 0.995016455, 'CRITICA': 0.37041493000000003, 'MEDIA': 0.94688535}}, 'info_user': {'full_name': 'nan nan', 'address': 'ATTN: LIDIA PIERCE, DIRECTOR OF FINANCE'}, 'modelo': {'class_registrada': 79, 'class_predicha': 79, 'class_pred_top1': 79, 'p_true': 0.9939751, 'p_pred_max': 0.9939751029014587, 'p_margin': 2.901458739934526e-09, 'top_k': [(79, 0.9939751029014587), (72, 0.0028921025805175304), (71, 0.0011459117522463202)]}, 'tributario': {'total_assmt': 1798300.0, 'total_exempt': 1798300.0, 'total_taxes': 0.0, 'tax_rate': 0.0, 'exempt_rate': 1.0, 'assmt_pct_in_class_reg': 0.5456570155902004, 'taxes_pct_in_class_reg': 1.0, 'exempt_pct_in_class_reg': 0.5456570155902004, 'flags': ['impuesto_cero_con_avaluo_positivo']}, 'ubicacion': {'zip': '02906', 'geo_cluster': 2}, 'administrativo': {'levy_code_1': 'E01'}, 'descripcion': {'short_desc': 'School'}}

salida_modelo = {
  "id_propiedad": 3386,
  "nivel_alerta": "BAJA",
  "motivo": "La clasificación registrada (CLASS=79, 'School') coincide con la predicción del modelo (top1=79) y presenta una confianza extremadamente alta (p_true=0.993975; p_margin≈0). Aunque se detecta la bandera 'impuesto_cero_con_avaluo_positivo' (TOTAL_ASSMT=1,798,300 con TOTAL_TAXES=0), el patrón es consistente con una propiedad institucional con exención total (TOTAL_EXEMPT=1,798,300; exempt_rate=1.0) y un levy específico (LEVY_CODE_1='E01'). En conjunto, no hay señales de error de clase; el punto a revisar es solo la coherencia administrativa de la exención/levy.",
  "recomendacion": "Mantener la clase 'School' sin cambios. Validar en la normativa municipal que el LEVY_CODE_1='E01' corresponde a exención total para este tipo de predio y confirmar que la exención aplica al 100% del avalúo (TOTAL_EXEMPT=TOTAL_ASSMT). Si el código de exención/levy no corresponde, actualizar el régimen tributario o documentar el motivo del impuesto cero."
}

### Ejemplo 2
info_tecnica = 
{'id_propiedad': 35005, 'nivel_alerta': 'CRITICA', 'grupos_p_true': {'median': {'ALTA': 0.813552475, 'BAJA': 0.995016455, 'CRITICA': 0.37041493000000003, 'MEDIA': 0.94688535}}, 'info_user': {'full_name': 'Harry Gendel', 'address': '1814 State St'}, 'modelo': {'class_registrada': 1, 'class_predicha': 1, 'class_pred_top1': 1, 'p_true': 0.64330965, 'p_pred_max': 0.6433096528053284, 'p_margin': 2.80532841401282e-09, 'top_k': [(1, 0.6433096528053284), (2, 0.1673332005739212), (23, 0.1454978883266449)]}, 'tributario': {'total_assmt': 424000.0, 'total_exempt': 0.0, 'total_taxes': 7780.4, 'tax_rate': 0.018349999999999998, 'exempt_rate': 0.0, 'assmt_pct_in_class_reg': 0.7489983022071307, 'taxes_pct_in_class_reg': 0.8831918505942276, 'exempt_pct_in_class_reg': 0.8136502546689304, 'flags': []}, 'ubicacion': {'zip': '02906', 'geo_cluster': 3}, 'administrativo': {'levy_code_1': 'NO01'}, 'descripcion': {'short_desc': 'Single Family'}}

salida_modelo = {
  "id_propiedad": 35005,
  "nivel_alerta": "CRITICA",
  "motivo": "Aunque el modelo predice la misma clase registrada (CLASS=1, 'Single Family'), la confianza es relativamente baja para este grupo: p_true=0.6433, muy por debajo de la mediana reportada para 'CRITICA' (≈0.3704) pero también muy lejos de los niveles típicos de 'BAJA' (mediana≈0.9950). Además, el modelo asigna probabilidades relevantes a clases alternativas (top_k incluye CLASS=2 con 0.1673 y CLASS=23 con 0.1455), lo que sugiere ambigüedad estructural en los atributos tributarios/administrativos para una vivienda unifamiliar. Los percentiles muestran impuestos relativamente altos dentro de su clase (taxes_pct_in_class_reg≈0.883), reforzando que el caso no es 'típico' dentro de CLASS=1.",
  "recomendacion": "Marcar el caso para revisión tributaria/catastral: (1) verificar si existen características físicas o administrativas que lo acerquen a CLASS=2 o CLASS=23 (p. ej. conversión a multifamiliar, uso mixto, o error de registro), (2) revisar consistencia entre avalúo e impuestos (TOTAL_ASSMT=424,000; TOTAL_TAXES=7,780.4; tax_rate≈0.01835) frente a comparables del mismo ZIP (02906) y geo_cluster=3, y (3) si se confirma uso no unifamiliar, actualizar CLASS o documentar la excepción."
}


### Ejemplo 3
info_tecnica = 
{'id_propiedad': 10250, 'nivel_alerta': 'ALTA', 'grupos_p_true': {'median': {'ALTA': 0.813552475, 'BAJA': 0.995016455, 'CRITICA': 0.37041493000000003, 'MEDIA': 0.94688535}}, 'info_user': {'full_name': 'Gilberto Morente', 'address': '40 Waverly St'}, 'modelo': {'class_registrada': 1, 'class_predicha': 1, 'class_pred_top1': 1, 'p_true': 0.86051834, 'p_pred_max': 0.8605183362960815, 'p_margin': -3.70391850523788e-09, 'top_k': [(1, 0.8605183362960815), (2, 0.1254243105649948), (23, 0.013796959072351456)]}, 'tributario': {'total_assmt': 233100.0, 'total_exempt': 0.0, 'total_taxes': 2438.12, 'tax_rate': 0.01045954525954526, 'exempt_rate': 0.0, 'assmt_pct_in_class_reg': 0.17106960950764008, 'taxes_pct_in_class_reg': 0.16828522920203734, 'exempt_pct_in_class_reg': 0.8136502546689304, 'flags': []}, 'ubicacion': {'zip': '02907', 'geo_cluster': 7}, 'administrativo': {'levy_code_1': 'OO01'}, 'descripcion': {'short_desc': 'Single Family'}}
salida_modelo ={ 
  "id_propiedad": 10250,
  "nivel_alerta": "ALTA",
  "motivo": "El modelo coincide con la clase registrada (CLASS=1, 'Single Family') pero con confianza moderada: p_true=0.8605, cercano a la mediana del grupo 'ALTA' (≈0.8136) y bastante por debajo del comportamiento típico de 'BAJA' (mediana≈0.9950). Existen alternativas con probabilidad no despreciable (CLASS=2 con 0.1254), indicando que algunos patrones del registro se parecen a otra clase. En lo tributario, los valores son relativamente bajos dentro de la clase (assmt_pct_in_class_reg≈0.171; taxes_pct_in_class_reg≈0.168), lo cual puede explicar parte de la ambigüedad: el caso cae en una zona de atributos menos representativa para el modelo.",
  "recomendacion": "Solicitar revisión ligera (no urgente): confirmar que la descripción 'Single Family' coincide con la realidad física del predio y descartar que sea 2-familias o configuración similar (por la probabilidad alternativa hacia CLASS=2). Complementar con verificación de comparables del ZIP 02907 y geo_cluster=7 para validar que avalúo e impuestos (TOTAL_ASSMT=233,100; TOTAL_TAXES=2,438.12; tax_rate≈0.01046) estén en rango. Si la clasificación está bien, mantener CLASS=1 y registrar este caso como 'baja representatividad' para recalibración futura."
}


### Ejemplo 4
info_tecnica = 
{'id_propiedad': 5413, 'nivel_alerta': 'MEDIA', 'grupos_p_true': {'median': {'ALTA': 0.813552475, 'BAJA': 0.995016455, 'CRITICA': 0.37041493000000003, 'MEDIA': 0.94688535}}, 'info_user': {'full_name': 'WILLIAM OGARA', 'address': '111 Arlington Ave'}, 'modelo': {'class_registrada': 2, 'class_predicha': 2, 'class_pred_top1': 2, 'p_true': 0.9247756, 'p_pred_max': 0.9247756004333496, 'p_margin': 4.3334957844365363e-10, 'top_k': [(2, 0.9247756004333496), (1, 0.06957420706748962), (23, 0.005412918049842119)]}, 'tributario': {'total_assmt': 589500.0, 'total_exempt': 0.0, 'total_taxes': 10817.36, 'tax_rate': 0.01835005937234945, 'exempt_rate': 0.0, 'assmt_pct_in_class_reg': 0.8908428050611195, 'taxes_pct_in_class_reg': 0.9389520337407964, 'exempt_pct_in_class_reg': 0.9066409321609836, 'flags': []}, 'ubicacion': {'zip': '02906', 'geo_cluster': 2}, 'administrativo': {'levy_code_1': 'NO01'}, 'descripcion': {'short_desc': '2 -5 Family'}}
salida_modelo = {
  "id_propiedad": 5413,
  "nivel_alerta": "MEDIA",
  "motivo": "La clase registrada (CLASS=2, '2 -5 Family') coincide con la predicción del modelo y el top-1, con p_true=0.9248 (confianza alta pero menor que lo típico de 'BAJA', cuya mediana≈0.9950). El modelo aún asigna una probabilidad secundaria notable a CLASS=1 (0.0696), lo cual sugiere que algunos rasgos se parecen a vivienda unifamiliar. En lo tributario, el caso está alto dentro de su clase (assmt_pct_in_class_reg≈0.891 y taxes_pct_in_class_reg≈0.939), lo que puede hacerlo menos “promedio” y moverlo a una zona de decisión más sensible.",
  "recomendacion": "Revisión focalizada: verificar que el predio efectivamente opera como 2–5 familias y no como unifamiliar (por la probabilidad secundaria hacia CLASS=1). Contrastar con registros de unidades/uso y, si existe evidencia de conversión o subdivisión reciente, actualizar atributos catastrales manteniendo coherencia con el avalúo e impuestos (TOTAL_ASSMT=589,500; TOTAL_TAXES=10,817.36; tax_rate≈0.01835). Si la clase está confirmada, mantener CLASS=2 y documentar que el valor/impuesto alto dentro de la clase explica el nivel 'MEDIA'."
}
"""
