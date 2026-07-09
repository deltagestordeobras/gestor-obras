import pandas as pd


STATUS_PENDENTE = "Pendente"
STATUS_PAGO = "Pago"


def normalizar_status(valor):
    texto = str(valor or "").strip()

    if "pago" in texto.lower():
        return STATUS_PAGO

    if texto.lower() == STATUS_PENDENTE.lower():
        return STATUS_PENDENTE

    return texto


def serie_status_normalizado(serie):
    return serie.fillna("").apply(normalizar_status)


def preparar_valor_status(df):
    df = df.copy()
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    df["StatusNormalizado"] = serie_status_normalizado(df["Status"])
    return df