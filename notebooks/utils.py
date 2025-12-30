import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.base import BaseEstimator, TransformerMixin




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
    """η (correlation ratio) para categórica->numérica, 0..1"""
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


