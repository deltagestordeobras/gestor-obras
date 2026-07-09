import pandas as pd

from services.status import STATUS_PAGO, STATUS_PENDENTE, preparar_valor_status


COLUNA_FORNECEDOR = "Fornecedor"
COLUNA_FORNECEDOR_LEGADO = "Descrição"
COLUNA_DATA_REFERENCIA = "DataReferencia"


def preparar_extrato(df):
    if df is None or df.empty:
        return pd.DataFrame()

    extrato = preparar_valor_status(df)

    for coluna in ["Entrada Nota", "Data Vencimento", "Data Pagto", "Criado Em", "Pago Em"]:
        if coluna in extrato.columns:
            extrato[coluna] = pd.to_datetime(extrato[coluna], errors="coerce")

    if COLUNA_FORNECEDOR not in extrato.columns:
        extrato[COLUNA_FORNECEDOR] = ""

    if COLUNA_FORNECEDOR_LEGADO in extrato.columns:
        fornecedor_legado = extrato[COLUNA_FORNECEDOR_LEGADO].fillna("").astype(str).str.strip()
        fornecedor_atual = extrato[COLUNA_FORNECEDOR].fillna("").astype(str).str.strip()
        extrato[COLUNA_FORNECEDOR] = fornecedor_atual.mask(fornecedor_atual == "", fornecedor_legado)

    if "Categoria" not in extrato.columns:
        extrato["Categoria"] = ""

    if "Etapa" not in extrato.columns:
        extrato["Etapa"] = ""

    if "Nº Nota" not in extrato.columns:
        extrato["Nº Nota"] = ""

    if "Tipo" not in extrato.columns:
        extrato["Tipo"] = ""

    extrato[COLUNA_DATA_REFERENCIA] = extrato.get("Entrada Nota")

    return extrato


def obter_opcoes_filtro(df, coluna):
    if df is None or df.empty or coluna not in df.columns:
        return ["Todos"]

    valores = (
        df[coluna]
        .dropna()
        .astype(str)
        .str.strip()
    )
    valores = sorted(valor for valor in valores.unique().tolist() if valor)

    return ["Todos"] + valores


def aplicar_filtros_extrato(
    df,
    fornecedor="Todos",
    etapa="Todos",
    categoria="Todos",
    data_inicio=None,
    data_fim=None,
):
    if df is None or df.empty:
        return pd.DataFrame()

    filtrado = df.copy()

    if fornecedor and fornecedor != "Todos" and COLUNA_FORNECEDOR in filtrado.columns:
        filtrado = filtrado[filtrado[COLUNA_FORNECEDOR].astype(str) == str(fornecedor)]

    if etapa and etapa != "Todos" and "Etapa" in filtrado.columns:
        filtrado = filtrado[filtrado["Etapa"].astype(str) == str(etapa)]

    if categoria and categoria != "Todos" and "Categoria" in filtrado.columns:
        filtrado = filtrado[filtrado["Categoria"].astype(str) == str(categoria)]

    if data_inicio is not None and COLUNA_DATA_REFERENCIA in filtrado.columns:
        filtrado = filtrado[
            filtrado[COLUNA_DATA_REFERENCIA] >= pd.to_datetime(data_inicio, errors="coerce")
        ]

    if data_fim is not None and COLUNA_DATA_REFERENCIA in filtrado.columns:
        data_fim = pd.to_datetime(data_fim, errors="coerce")
        filtrado = filtrado[filtrado[COLUNA_DATA_REFERENCIA] <= data_fim]

    return filtrado


def calcular_indicadores_extrato(df):
    if df is None or df.empty:
        return {
            "total_pago": 0,
            "total_pendente": 0,
            "saldo_obra": 0,
            "gasto_mes": 0,
        }

    extrato = preparar_valor_status(df)

    total_pago = abs(
        extrato[
            (extrato["StatusNormalizado"] == STATUS_PAGO)
            & (extrato["Valor"] < 0)
        ]["Valor"].sum()
    )

    total_pendente = abs(
        extrato[
            (extrato["StatusNormalizado"] == STATUS_PENDENTE)
            & (extrato["Valor"] < 0)
        ]["Valor"].sum()
    )

    saldo_obra = extrato["Valor"].sum()

    data_referencia = None
    if COLUNA_DATA_REFERENCIA in extrato.columns:
        data_referencia = pd.to_datetime(extrato[COLUNA_DATA_REFERENCIA], errors="coerce")
    elif "Entrada Nota" in extrato.columns:
        data_referencia = pd.to_datetime(extrato["Entrada Nota"], errors="coerce")

    if data_referencia is not None:
        hoje = pd.Timestamp.today()
        gasto_mes = abs(
            extrato[
                (extrato["Valor"] < 0)
                & (data_referencia.dt.month == hoje.month)
                & (data_referencia.dt.year == hoje.year)
            ]["Valor"].sum()
        )
    else:
        gasto_mes = 0

    return {
        "total_pago": total_pago,
        "total_pendente": total_pendente,
        "saldo_obra": saldo_obra,
        "gasto_mes": gasto_mes,
    }


def formatar_tabela_extrato(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=[
            "Entrada Nota",
            "Data Vencimento",
            "Data Pagto",
            "Fornecedor",
            "Categoria",
            "Etapa",
            "Nº Nota",
            "Valor",
            "Status",
        ])

    tabela = df.copy()

    colunas = [
        "Entrada Nota",
        "Data Vencimento",
        "Data Pagto",
        COLUNA_FORNECEDOR,
        "Categoria",
        "Etapa",
        "Nº Nota",
        "Valor",
        "Status",
    ]

    for coluna in colunas:
        if coluna not in tabela.columns:
            tabela[coluna] = ""

    tabela = tabela[colunas]
    tabela = tabela.rename(columns={COLUNA_FORNECEDOR: "Fornecedor"})

    if "Entrada Nota" in tabela.columns:
        tabela = tabela.sort_values("Entrada Nota", ascending=False, na_position="last")

    return tabela