import pandas as pd

from services.status import STATUS_PAGO, preparar_valor_status


COLUNA_ETAPA = "Etapa"
COLUNA_SERVICO = "Serviço"
COLUNA_MATERIAL = "Material"
COLUNA_CATEGORIA = "Categoria"
COLUNA_VALOR = "Valor"
COLUNA_CUSTO = "Custo"
COLUNA_TOTAL = "Total"
COLUNA_PREVISTO = "Previsto"
COLUNA_REAL = "Real"
COLUNA_DESVIO = "Desvio"
COLUNA_PERCENTUAL = "% Execução"
COLUNA_STATUS_DESVIO = "Status Desvio"

DIMENSOES_PADRAO = [
    COLUNA_ETAPA,
    COLUNA_SERVICO,
    COLUNA_MATERIAL,
    COLUNA_CATEGORIA,
]


def _numero(valor, padrao=0.0):
    try:
        if valor is None:
            return padrao
        return float(valor)
    except (TypeError, ValueError):
        return padrao


def _dataframe_vazio(colunas):
    return pd.DataFrame(columns=colunas)


def _garantir_coluna(df, coluna, valor_padrao=""):
    if coluna not in df.columns:
        df[coluna] = valor_padrao
    return df


def _coluna_valor_disponivel(df):
    for coluna in [COLUNA_CUSTO, COLUNA_TOTAL, COLUNA_VALOR]:
        if coluna in df.columns:
            return coluna
    return None


def preparar_dataframe_previsto(df_previsto):
    if df_previsto is None or df_previsto.empty:
        return _dataframe_vazio(DIMENSOES_PADRAO + [COLUNA_PREVISTO])

    previsto = df_previsto.copy()
    coluna_valor = _coluna_valor_disponivel(previsto)

    if coluna_valor is None:
        previsto[COLUNA_PREVISTO] = 0
    else:
        previsto[COLUNA_PREVISTO] = pd.to_numeric(
            previsto[coluna_valor],
            errors="coerce",
        ).fillna(0).abs()

    for coluna in DIMENSOES_PADRAO:
        _garantir_coluna(previsto, coluna, "")

    return previsto


def preparar_dataframe_real(df_real, considerar_apenas_pagos=False):
    if df_real is None or df_real.empty:
        return _dataframe_vazio(DIMENSOES_PADRAO + [COLUNA_REAL])

    real = df_real.copy()

    if COLUNA_VALOR in real.columns and "Status" in real.columns:
        real = preparar_valor_status(real)

        if considerar_apenas_pagos:
            real = real[real["StatusNormalizado"] == STATUS_PAGO]
    else:
        coluna_valor = _coluna_valor_disponivel(real)
        if coluna_valor and coluna_valor != COLUNA_VALOR:
            real[COLUNA_VALOR] = real[coluna_valor]
        elif COLUNA_VALOR not in real.columns:
            real[COLUNA_VALOR] = 0

    real[COLUNA_REAL] = pd.to_numeric(real[COLUNA_VALOR], errors="coerce").fillna(0).abs()

    for coluna in DIMENSOES_PADRAO:
        _garantir_coluna(real, coluna, "")

    return real


def agregar_por_dimensao(df, dimensao, coluna_valor):
    if df is None or df.empty:
        return _dataframe_vazio([dimensao, coluna_valor])

    dados = df.copy()
    _garantir_coluna(dados, dimensao, "")

    if coluna_valor not in dados.columns:
        dados[coluna_valor] = 0

    dados[coluna_valor] = pd.to_numeric(dados[coluna_valor], errors="coerce").fillna(0)

    return (
        dados
        .groupby(dimensao, as_index=False)
        .agg({coluna_valor: "sum"})
        .sort_values(coluna_valor, ascending=False)
    )


def calcular_previsto_por_etapa(df_previsto):
    previsto = preparar_dataframe_previsto(df_previsto)
    return agregar_por_dimensao(previsto, COLUNA_ETAPA, COLUNA_PREVISTO)


def calcular_real_por_etapa(df_real, considerar_apenas_pagos=False):
    real = preparar_dataframe_real(df_real, considerar_apenas_pagos=considerar_apenas_pagos)
    return agregar_por_dimensao(real, COLUNA_ETAPA, COLUNA_REAL)


def calcular_previsto_por_servico(df_previsto):
    previsto = preparar_dataframe_previsto(df_previsto)
    return agregar_por_dimensao(previsto, COLUNA_SERVICO, COLUNA_PREVISTO)


def calcular_real_por_servico(df_real, considerar_apenas_pagos=False):
    real = preparar_dataframe_real(df_real, considerar_apenas_pagos=considerar_apenas_pagos)
    return agregar_por_dimensao(real, COLUNA_SERVICO, COLUNA_REAL)


def calcular_previsto_por_material(df_previsto):
    previsto = preparar_dataframe_previsto(df_previsto)
    return agregar_por_dimensao(previsto, COLUNA_MATERIAL, COLUNA_PREVISTO)


def calcular_real_por_material(df_real, considerar_apenas_pagos=False):
    real = preparar_dataframe_real(df_real, considerar_apenas_pagos=considerar_apenas_pagos)
    return agregar_por_dimensao(real, COLUNA_MATERIAL, COLUNA_REAL)


def calcular_previsto_por_categoria(df_previsto):
    previsto = preparar_dataframe_previsto(df_previsto)
    return agregar_por_dimensao(previsto, COLUNA_CATEGORIA, COLUNA_PREVISTO)


def calcular_real_por_categoria(df_real, considerar_apenas_pagos=False):
    real = preparar_dataframe_real(df_real, considerar_apenas_pagos=considerar_apenas_pagos)
    return agregar_por_dimensao(real, COLUNA_CATEGORIA, COLUNA_REAL)


def comparar_previsto_real(previsto, real, dimensao=COLUNA_ETAPA):
    previsto_df = previsto.copy() if previsto is not None else _dataframe_vazio([dimensao, COLUNA_PREVISTO])
    real_df = real.copy() if real is not None else _dataframe_vazio([dimensao, COLUNA_REAL])

    _garantir_coluna(previsto_df, dimensao, "")
    _garantir_coluna(real_df, dimensao, "")

    if COLUNA_PREVISTO not in previsto_df.columns:
        coluna_valor = _coluna_valor_disponivel(previsto_df)
        previsto_df[COLUNA_PREVISTO] = (
            pd.to_numeric(previsto_df[coluna_valor], errors="coerce").fillna(0).abs()
            if coluna_valor else 0
        )

    if COLUNA_REAL not in real_df.columns:
        coluna_valor = _coluna_valor_disponivel(real_df)
        real_df[COLUNA_REAL] = (
            pd.to_numeric(real_df[coluna_valor], errors="coerce").fillna(0).abs()
            if coluna_valor else 0
        )

    comparativo = previsto_df[[dimensao, COLUNA_PREVISTO]].merge(
        real_df[[dimensao, COLUNA_REAL]],
        on=dimensao,
        how="outer",
    )

    comparativo[COLUNA_PREVISTO] = pd.to_numeric(
        comparativo[COLUNA_PREVISTO],
        errors="coerce",
    ).fillna(0)
    comparativo[COLUNA_REAL] = pd.to_numeric(
        comparativo[COLUNA_REAL],
        errors="coerce",
    ).fillna(0)

    comparativo[COLUNA_DESVIO] = comparativo[COLUNA_REAL] - comparativo[COLUNA_PREVISTO]
    comparativo[COLUNA_PERCENTUAL] = comparativo.apply(
        lambda row: (row[COLUNA_REAL] / row[COLUNA_PREVISTO] * 100)
        if row[COLUNA_PREVISTO] > 0 else 0,
        axis=1,
    )
    comparativo[COLUNA_STATUS_DESVIO] = comparativo.apply(classificar_desvio, axis=1)

    return comparativo.sort_values(COLUNA_DESVIO, ascending=False)


def classificar_desvio(row):
    previsto = _numero(row.get(COLUNA_PREVISTO, 0))
    real = _numero(row.get(COLUNA_REAL, 0))
    percentual = _numero(row.get(COLUNA_PERCENTUAL, 0))

    if previsto <= 0 and real > 0:
        return "Não previsto"

    if real > previsto:
        return "Estourado"

    if percentual >= 80:
        return "Atenção"

    if real <= previsto:
        return "Dentro do previsto"

    return "Sem dados"


def calcular_desvios_orcamentarios(comparativo):
    if comparativo is None or comparativo.empty:
        return {
            "previsto_total": 0,
            "real_total": 0,
            "desvio_total": 0,
            "percentual_execucao": 0,
            "itens_estourados": 0,
            "itens_nao_previstos": 0,
            "itens_em_atencao": 0,
        }

    dados = comparativo.copy()

    previsto_total = pd.to_numeric(dados[COLUNA_PREVISTO], errors="coerce").fillna(0).sum()
    real_total = pd.to_numeric(dados[COLUNA_REAL], errors="coerce").fillna(0).sum()
    desvio_total = real_total - previsto_total
    percentual_execucao = (real_total / previsto_total * 100) if previsto_total > 0 else 0

    return {
        "previsto_total": previsto_total,
        "real_total": real_total,
        "desvio_total": desvio_total,
        "percentual_execucao": percentual_execucao,
        "itens_estourados": int((dados[COLUNA_STATUS_DESVIO] == "Estourado").sum()),
        "itens_nao_previstos": int((dados[COLUNA_STATUS_DESVIO] == "Não previsto").sum()),
        "itens_em_atencao": int((dados[COLUNA_STATUS_DESVIO] == "Atenção").sum()),
    }


def gerar_alertas_desvio(comparativo):
    if comparativo is None or comparativo.empty:
        return []

    alertas = []

    for _, row in comparativo.iterrows():
        nome = ""
        for coluna in DIMENSOES_PADRAO:
            if coluna in row and str(row.get(coluna, "")).strip():
                nome = str(row.get(coluna)).strip()
                break

        if not nome:
            nome = "Item sem identificação"

        status = row.get(COLUNA_STATUS_DESVIO, "")
        desvio = _numero(row.get(COLUNA_DESVIO, 0))
        percentual = _numero(row.get(COLUNA_PERCENTUAL, 0))

        if status == "Não previsto":
            alertas.append(f"{nome}: custo real sem previsão de R$ {row[COLUNA_REAL]:,.2f}")
        elif status == "Estourado":
            alertas.append(f"{nome}: estourou o previsto em R$ {desvio:,.2f}")
        elif status == "Atenção":
            alertas.append(f"{nome}: já consumiu {percentual:.1f}% do previsto")

    return alertas


def calcular_percentual_execucao(comparativo):
    if comparativo is None or comparativo.empty:
        return 0

    previsto_total = pd.to_numeric(
        comparativo[COLUNA_PREVISTO],
        errors="coerce",
    ).fillna(0).sum()
    real_total = pd.to_numeric(
        comparativo[COLUNA_REAL],
        errors="coerce",
    ).fillna(0).sum()

    return (real_total / previsto_total * 100) if previsto_total > 0 else 0


def gerar_comparativo_por_dimensao(
    df_previsto,
    df_real,
    dimensao=COLUNA_ETAPA,
    considerar_apenas_pagos=False,
):
    previsto = preparar_dataframe_previsto(df_previsto)
    real = preparar_dataframe_real(df_real, considerar_apenas_pagos=considerar_apenas_pagos)

    previsto_agrupado = agregar_por_dimensao(previsto, dimensao, COLUNA_PREVISTO)
    real_agrupado = agregar_por_dimensao(real, dimensao, COLUNA_REAL)

    comparativo = comparar_previsto_real(
        previsto_agrupado,
        real_agrupado,
        dimensao=dimensao,
    )

    return {
        "comparativo": comparativo,
        "resumo": calcular_desvios_orcamentarios(comparativo),
        "alertas": gerar_alertas_desvio(comparativo),
    }


def gerar_auditoria_previsto_real(
    df_previsto,
    df_real,
    considerar_apenas_pagos=False,
):
    auditoria = {}

    for dimensao in DIMENSOES_PADRAO:
        auditoria[dimensao] = gerar_comparativo_por_dimensao(
            df_previsto,
            df_real,
            dimensao=dimensao,
            considerar_apenas_pagos=considerar_apenas_pagos,
        )

    return auditoria