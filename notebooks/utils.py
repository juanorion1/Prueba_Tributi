import re
import ast
import json
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.base import BaseEstimator, TransformerMixin
from prompt import PROMPT_INSTRUCCIONES, PROMPT_DETALLE_TECNICO


resp_vacia = "SIN_DESCRIPCION_TRAS_SANITIZACION"
nivel_alerta = {"BAJA", "MEDIA", "ALTA", "CRITICA"}
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)

PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[\s\-\.]?)?(?:\(?\d{3}\)?[\s\-\.]?)\d{3}[\s\-\.]?\d{4}\b")

ADDRESS_RE = re.compile(r"""
(
    # --- US style: 135 Abbott St ---
    \b\d{1,6}\s+[A-Z0-9ÁÉÍÓÚÑa-záéíóúñ.\- ]{2,}\s+
    (St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Ln|Lane|Dr|Drive|Ct|Court|Pl|Place|Way|Pkwy|Parkway)\b
)
|
(
    # --- CO urban: Calle/Carrera/... 123 #45-67 (con letras y Sur/Este/Oeste) ---
    \b(?:calle|cl|carrera|cra|kr|avenida|av(?:\.|enida)?|transversal|trv|tv|diagonal|diag|dg|pasaje|psj)\s*
    \d{1,4}(?:ra|a|o)?[A-Za-z]{0,3}                   # 60N, 10A, 1ra, 25aa
    (?:\s*(?:norte|sur|este|oeste))?                  # opcional
    \s*(?:\#|n[°o\.]?|no\.?)\s*                        # separador (# / No / N°)
    \d{1,4}[A-Za-z]{0,3}                              # 45, 12C, 18B, 40f
    (?:\s*(?:norte|sur|este|oeste)\s*\d{0,4}[A-Za-z]{0,3})?  # sur67
    (?:\s*[-–]\s*\d{1,4}[A-Za-z]{0,3})?               # -67, -22
    \b
)
|
(
    # --- Rural / Km / Vía / Vereda ---
    \b(?:vereda)\s+[A-Za-zÁÉÍÓÚÑa-záéíóúñ ]+(?:,\s*parcela\s+[A-Za-zÁÉÍÓÚÑa-záéíóúñ0-9 ]+)?\b
)
|
(
    \b(?:kil[oó]metro|km)\s*\d+(?:[.,]\d+)?(?:\s*,?\s*(?:v[ií]a|via)\s+[A-Za-zÁÉÍÓÚÑa-záéíóúñ ]+)?\b
)
""", re.IGNORECASE | re.VERBOSE)

ADDRESS_NO_SUFFIX_RE = re.compile(
    r"\b\d{1,6}\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ'\-]{2,}"
    r"(?:\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ'\-]{2,})?\b"
)


UNIT_RE = re.compile(r"\b(?:Unit|Apt|Apartment|Suite|Ste|Piso|Interior|Int)\s*#?\s*\w+\b", re.IGNORECASE)

NAME_RE = re.compile(
    r"\b"
    r"[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+"
    r"(?:\s+[A-Z]\.?)?"                       
    r"(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3}"    
    r"\b"
)

NAME_TITLE_RE = re.compile(
    r"\b(?:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)"
    r"(?:\s+(?:[A-Z]\.?))?"                 
    r"(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,2}\b" )

NAME_ALLCAPS_RE = re.compile(
    r"\b(?:[A-ZÁÉÍÓÚÑ]{2,})(?:\s+[A-ZÁÉÍÓÚÑ]{2,}){1,3}\b"
)

PUNT_RE = re.compile(r"[,.;:-]\b")



_PLACEHOLDER_RE = re.compile(
    r"\[(?:NAME|PHONE|EMAIL|ADDRESS)\]",
    flags=re.IGNORECASE
)

def is_effectively_empty(s: str) -> bool:

    if s is None:
        return True

    text = str(s).strip()
    if text == "":
        return True

    # 1) Quita placeholders
    text = _PLACEHOLDER_RE.sub("", text)

    # 2) Quita símbolos, espacios y puntuación (incluye +, comas, etc.)
    text = re.sub(r"[^A-Za-z0-9ÁÉÍÓÚÑáéíóúñ]+", "", text)

    return text == ""

def cleanup_punctuation(t: str) -> str:
    t = re.sub(r"[,\.\-;:]{2,}", " ", t)

    t = re.sub(r"(?<=\s)[,\.\-;:]+(?=\s)", " ", t)

    t = t.strip(" ,.-;:")

    t = re.sub(r"\s+", " ", t).strip()
    return t

def sanitizar_texto(texto: str) -> str:

    if texto is None:
        return resp_vacia

    t = str(texto)

    # eliminar patrones claros
    t = EMAIL_RE.sub("[EMAIL]", t)
    t = PHONE_RE.sub("[PHONE]", t)
    t = ADDRESS_NO_SUFFIX_RE.sub("[ADDRESS]",t)
    t = ADDRESS_RE.sub("[ADDRESS]", t)
    t = UNIT_RE.sub("[UNIT]", t)
    

    # Nombres propios (heurístico)
    t = NAME_RE.sub("[NAME]", t)
    t = NAME_TITLE_RE.sub("[NAME]", t)
    t = NAME_ALLCAPS_RE.sub("[NAME]", t)

    # Normalización
    t = re.sub(r"\s+", " ", t).strip()
    
    # Elimina puntuación
    t = cleanup_punctuation(t)

    return resp_vacia if is_effectively_empty(t) else t

def imputar_nulos_probabilisticamente(columna: pd.Series, random_state: int | None = 42) -> pd.Series:

    if random_state is not None:
        np.random.seed(random_state)

    col = columna.copy()

    valores_validos = col.dropna()

    if valores_validos.empty:
        raise ValueError("La columna no tiene valores no nulos para construir la distribución.")

    conteo = valores_validos.value_counts()
    probabilidades = conteo / conteo.sum()

    idx_nulos = col[col.isna()].index
    n_nulos = len(idx_nulos)

    if n_nulos == 0:
        return col  

    valores_imputados = np.random.choice(
        probabilidades.index,
        size=n_nulos,
        p=probabilidades.values
    )

    col.loc[idx_nulos] = valores_imputados

    return col


def cramers_v(x, y):
    ct = pd.crosstab(x, y)
    if ct.size == 0:
        return np.nan

    chi2 = chi2_contingency(ct, correction=False)[0]
    n = ct.to_numpy().sum()
    r, k = ct.shape

    phi2 = chi2 / n
    
    phi2corr = max(0, phi2 - ((k-1)*(r-1))/(n-1))
    rcorr = r - ((r-1)**2)/(n-1)
    kcorr = k - ((k-1)**2)/(n-1)
    denom = min((kcorr-1), (rcorr-1))

    return np.sqrt(phi2corr / denom) if denom > 0 else np.nan

def top_n_other(s, n=15):
    s = s.astype("object")
    top = s.value_counts(dropna=True).head(n).index
    return s.where(s.isin(top), "OTROS").fillna("MISSING")

def correlation_ratio_eta(categories, values):
    
    mask = (~categories.isna()) & (~values.isna())
    categories = categories[mask]
    values = values[mask].astype(float)

    if values.size < 2:
        return np.nan

    overall_mean = values.mean()
    ss_total = ((values - overall_mean) ** 2).sum()
    if ss_total == 0:
        return 0.0

    ss_between = 0.0
    for _, grp in values.groupby(categories):
        if len(grp) == 0:
            continue
        ss_between += len(grp) * (grp.mean() - overall_mean) ** 2

    eta2 = ss_between / ss_total
    return float(np.sqrt(max(0.0, eta2)))


class FrequencySamplerImputerNumeric(BaseEstimator, TransformerMixin):
    """
    Imputa NaNs en columnas numéricas muestreando aleatoriamente valores observados
    según su frecuencia por columna.
    """
    def __init__(self, random_state=42):
        self.random_state = random_state

    def fit(self, X, y=None):
        X_df = pd.DataFrame(X).copy()
        self.value_probs_ = {}

        for col in X_df.columns:
            s = pd.to_numeric(X_df[col], errors="coerce")
            vc = s.dropna().value_counts(normalize=True)

            # Si no hay valores válidos, guardamos None
            if vc.empty:
                self.value_probs_[col] = None
            else:
                self.value_probs_[col] = (vc.index.to_numpy(), vc.to_numpy())

        return self

    def transform(self, X):
        rng = np.random.default_rng(self.random_state)
        X_df = pd.DataFrame(X).copy()

        for col in X_df.columns:
            s = pd.to_numeric(X_df[col], errors="coerce")
            mask = s.isna()

            vp = self.value_probs_.get(col)
            if mask.any():
                if vp is None:
                    # fallback: si todo era NaN en fit, imputar 0.0
                    s.loc[mask] = 0.0
                else:
                    values, probs = vp
                    s.loc[mask] = rng.choice(values, size=int(mask.sum()), p=probs)

            X_df[col] = s

        return X_df.to_numpy(dtype=float)

def calc_log(x, base="10"):
    if base=="10":
        if x > 0:
            return np.log10(x)
        else:
            return 0
    else:
        if x > 0:
            return np.log(x)
        else:
            return 0 
        

def topk_proba_dict(row, classes_, k=3):
    idx = np.argsort(row)[::-1][:k]
    return {int(classes_[i]): float(row[i]) for i in idx}



def salida_estructurada(request):
    
    #if request["nivel_alerta"] not in nivel_alerta:
    #    raise ValueError(f"nivel_alerta inválido: {nivel_alerta}. Debe ser uno de {sorted(nivel_alerta)}")

    motivo_s = sanitizar_texto(request["motivo"])
    recomendacion_s = sanitizar_texto(request["recomendacion"])

    return {
        "id_propiedad": str(request["id_propiedad"]),
        "nivel_alerta": request["nivel_alerta"],
        "motivo_tecnico": motivo_s,
        "recomendacion": recomendacion_s,
    }




def percentil_en_grupo(valor, serie_grupo):

    return (serie_grupo.rank(pct=True, method="average")[serie_grupo.index[0]]
            if isinstance(serie_grupo, pd.Series) else np.nan)

def build_evidence_packet(row, df_ref, alerta_info):

    class_reg = int(row["CLASS"])
    p_true = float(row["p_true"])

    proba_dict_raw = row["y_proba_full"]
    proba_dict = ast.literal_eval(proba_dict_raw) if isinstance(proba_dict_raw, str) else proba_dict_raw

    items_sorted = sorted(
        [(int(k), float(v)) for k, v in (proba_dict or {}).items()],
        key=lambda x: x[1],
        reverse=True
    )

    if not items_sorted:
        class_pred_top1 = int(row["pred_class"])
        p_pred_max = float("nan")
        top_k = []
    else:
        class_pred_top1 = items_sorted[0][0]
        p_pred_max = items_sorted[0][1]
        top_k = items_sorted[:5]

    p_margin = (p_pred_max - p_true) if np.isfinite(p_pred_max) else float("nan")

    assmt = float(row["TOTAL_ASSMT"])
    taxes = float(row["TOTAL_TAXES"])
    exempt = float(row["TOTAL_EXEMPT"])

    tax_rate = taxes / max(assmt, 1.0)
    exempt_rate = exempt / max(assmt, 1.0)

    assmt_pct = taxes_pct = exempt_pct = np.nan
    if df_ref is not None:
        df_ref2 = df_ref.dropna(subset=["CLASS"])
        grp = df_ref2[df_ref2["CLASS"] == class_reg]
        if len(grp):
            assmt_pct  = float((grp["TOTAL_ASSMT"]  <= assmt).mean())
            taxes_pct  = float((grp["TOTAL_TAXES"]  <= taxes).mean())
            exempt_pct = float((grp["TOTAL_EXEMPT"] <= exempt).mean())

    flags = []
    if exempt > assmt:
        flags.append("exencion_mayor_que_avaluo")
    if taxes == 0 and assmt > 0:
        flags.append("impuesto_cero_con_avaluo_positivo")
    if np.isfinite(assmt_pct) and assmt_pct >= 0.99:
        flags.append("avaluo_extremo_para_clase")

    nivel = str(row["nivel_alerta"])
    
    name = " ".join( [ str(row['FIRST_NAME']), str(row['LAST_NAME'] ) ] )
    if isinstance(alerta_info, dict) and nivel in alerta_info:
        info_nivel = alerta_info[nivel]

    packet = {
        "id_propiedad": int(row["P_ID"]),
        "nivel_alerta": nivel,

        "grupos_p_true": alerta_info if isinstance(alerta_info, dict) else None,

        "info_user":{
            "full_name": name,
            "address": row['FREE_LINE_2']
        },

        "modelo": {
            "class_registrada": class_reg,
            "class_predicha": int(row["pred_class"]),
            "class_pred_top1": class_pred_top1,
            "p_true": p_true,
            "p_pred_max": p_pred_max,
            "p_margin": p_margin,
            "top_k": top_k,
        },
        "tributario": {
            "total_assmt": assmt,
            "total_exempt": exempt,
            "total_taxes": taxes,
            "tax_rate": tax_rate,
            "exempt_rate": exempt_rate,
            "assmt_pct_in_class_reg": assmt_pct,
            "taxes_pct_in_class_reg": taxes_pct,
            "exempt_pct_in_class_reg": exempt_pct,
            "flags": flags,
        },
        "ubicacion": {
            "zip": str(row["ZIP_POSTAL"]),
            "geo_cluster": int(row["geo_cluster"]),
        },
        "administrativo": {
            "levy_code_1": str(row["LEVY_CODE_1"]),
        },
        "descripcion": {
            "short_desc": str(row["SHORT_DESC"]),
        },
    }
    return packet

def openai_json_to_dict(text):
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if m:
        text = m.group(1)

    text = text.strip()

    return json.loads(text)

def genera_respuesta(client, dict_info, model):
    prompt = PROMPT_INSTRUCCIONES.replace("__INFO__TECNICA__", str(dict_info))
    prompt = prompt.replace("__PROMPT_DETALLE_TECNICO__", PROMPT_DETALLE_TECNICO)
    response = client.models.generate_content(model=model, contents=prompt, config={"temperature": 0.8}).text
    response = openai_json_to_dict(response)
    response["motivo"] = sanitizar_texto(response["motivo"])
    response["recomendacion"] = sanitizar_texto(response["recomendacion"])

    return response
