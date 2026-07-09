"""Funções de inteligência financeira reservadas para alertas e sugestões.

Este módulo não é chamado diretamente na navegação atual, mas concentra regras
úteis para integração futura com Dashboard/Geral sem misturar análise com UI.
"""


def gerar_alertas(df):

    if df is None or df.empty or "Valor" not in df.columns:
        return []

    alertas = []

    saldo = df["Valor"].sum()

    if saldo < 0:
        alertas.append("🔴 Obra está no prejuízo!")

    gastos = df[df["Valor"] < 0]["Valor"].sum()

    if abs(gastos) > abs(saldo):
        alertas.append("⚠️ Despesas maiores que entrada")

    return alertas


def detectar_estouro(df, limite=1.1):

    if df is None or df.empty or "Valor" not in df.columns:
        return False

    total = df["Valor"].sum()

    return total < 0 and abs(total) > limite


def fornecedor_mais_caro(df):

    if df is None or df.empty or "Fornecedor" not in df.columns:
        return None

    ranking = (
        df.groupby("Fornecedor")["Valor"]
        .sum()
        .abs()
        .sort_values(ascending=False)
    )

    return ranking.head(1)


def curva_abc(df):

    if df is None or df.empty or "Valor" not in df.columns:
        return df

    df = df.copy()

    df["Valor"] = df["Valor"].abs()

    total = df["Valor"].sum()

    if total == 0:
        return df

    df = df.sort_values("Valor", ascending=False)

    df["%"] = df["Valor"] / total
    df["% acumulado"] = df["%"].cumsum()

    def classificar(p):
        if p <= 0.7:
            return "A"
        elif p <= 0.9:
            return "B"
        return "C"

    df["Classe"] = df["% acumulado"].apply(classificar)

    return df


def prever_estouro(df):

    if df is None or df.empty or "Valor" not in df.columns:
        return "⚠️ Sem dados"

    gastos = df[df["Valor"] < 0]["Valor"].sum()
    entradas = df[df["Valor"] > 0]["Valor"].sum()

    if entradas == 0:
        return "⚠️ Sem receita registrada"

    proporcao = abs(gastos) / entradas

    if proporcao > 1:
        return "🔴 Alta chance de prejuízo"
    elif proporcao > 0.8:
        return "🟠 Risco moderado"
    else:
        return "🟢 Saudável"


def gerar_sugestoes(df):

    if df is None or df.empty or "Valor" not in df.columns:
        return []

    sugestoes = []

    gastos = df[df["Valor"] < 0]

    if not gastos.empty and "Etapa" in df.columns:

        maior = gastos.loc[gastos["Valor"].idxmin()]

        sugestoes.append(
            f"Reduzir custos na etapa: {maior['Etapa']}"
        )

    return sugestoes

def calcular_risco_obra(df):

    if df is None or df.empty:
        return 0, "Sem dados"

    saldo = df["Valor"].sum()
    gastos = abs(df[df["Valor"] < 0]["Valor"].sum())
    entradas = df[df["Valor"] > 0]["Valor"].sum()

    score = 100

    # 🔻 prejuízo
    if saldo < 0:
        score -= 40

    # 🔻 gasto alto
    if entradas > 0:
        proporcao = gastos / entradas

        if proporcao > 1:
            score -= 30
        elif proporcao > 0.8:
            score -= 15

    # 🔻 sem entrada
    if entradas == 0:
        score -= 30

    # 🔒 limites
    score = max(0, min(100, score))

    # classificação
    if score > 70:
        nivel = "🟢 Baixo risco"
    elif score > 40:
        nivel = "🟠 Médio risco"
    else:
        nivel = "🔴 Alto risco"

    return score, nivel
