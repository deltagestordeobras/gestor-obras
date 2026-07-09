import pandas as pd

# =====================================================
# 🔧 CONFIGURAÇÕES GLOBAIS (NÍVEL PROFISSIONAL)
# =====================================================

INDIRETOS = 0.15
IMPOSTOS = 0.08
LUCRO = 0.20

FATOR_PERDA_PADRAO = 1.10

PERDAS_POR_TIPO = {
    "Concreto": 1.05,
    "Revestimento": 1.15,
    "Alvenaria": 1.10
}

# =====================================================
# 📦 FUNÇÕES BÁSICAS
# =====================================================

def preco_material(nome, df_materiais):
    if df_materiais is None or df_materiais.empty or "Material" not in df_materiais.columns:
        return 0

    coluna_preco = None
    for candidato in ("Preço", "Preco"):
        if candidato in df_materiais.columns:
            coluna_preco = candidato
            break
    if coluna_preco is None:
        return 0

    linha = df_materiais[
        df_materiais["Material"].astype(str).str.strip()
        == str(nome or "").strip()
    ]

    if not linha.empty:
        valor = pd.to_numeric(linha.iloc[0][coluna_preco], errors="coerce")
        return 0 if pd.isna(valor) else float(valor)

    return 0


def get_param(nome, df_parametros):
    if df_parametros is None or df_parametros.empty or "Item" not in df_parametros.columns:
        return 0

    linha = df_parametros[
        df_parametros["Item"].astype(str).str.strip()
        == str(nome or "").strip()
    ]

    if not linha.empty:
        valor = pd.to_numeric(linha.iloc[0].get("Valor", 0), errors="coerce")
        return 0 if pd.isna(valor) else float(valor)

    return 0


# =====================================================
# 🏗️ TIPOS DE OBRA
# =====================================================

TIPOS_OBRA = {
    "Casa": {
        "permitidos": [
            "Alvenaria", "Chapisco", "Reboco Interno", "Reboco Externo",
            "Pintura", "Revestimento", "Piso Cerâmico", "Piso Porcelanato",
            "Contra Piso", "Concreto", "Laje com Escoramento",
            "Cobertura Cerâmica", "Instalação Elétrica", "Instalação Hidráulica"
        ]
    },
    "Prédio": {
        "permitidos": [
            "Concreto", "Laje com Escoramento", "Alvenaria",
            "Chapisco", "Reboco Interno", "Reboco Externo",
            "Pintura", "Revestimento",
            "Instalação Elétrica", "Instalação Hidráulica"
        ]
    },
    "Galpão": {
        "permitidos": [
            "Estrutura metálica", "Cobertura Metálica",
            "Cobertura Sanduíche", "Concreto",
            "Piso Cerâmico", "Instalação Elétrica"
        ]
    }
}


def filtrar_composicao_por_tipo(comp, tipo_obra):
    if tipo_obra not in TIPOS_OBRA:
        return comp

    permitidos = TIPOS_OBRA[tipo_obra]["permitidos"]

    return comp[comp["Serviço"].isin(permitidos)].copy()


# =====================================================
# 🚀 MOTOR DE CÁLCULO PROFISSIONAL
# =====================================================

def calcular_obra(area, tipo_obra="Casa", comp=None, mat=None, mo=None):

    # ===============================
    # 🔒 VALIDAÇÕES INICIAIS
    # ===============================
    if area <= 0:
        raise ValueError("Área inválida")

    if comp is None or mat is None or mo is None:
        raise ValueError("Dados obrigatórios não fornecidos")

    comp = comp.copy()
    mat = mat.copy()
    mo = mo.copy()

    # ===============================
    # 🔥 FILTRO POR TIPO DE OBRA
    # ===============================
    comp = filtrar_composicao_por_tipo(comp, tipo_obra)

    if comp.empty:
        raise ValueError("Nenhuma composição encontrada para este tipo de obra")

    # ===============================
    # 📐 QUANTIDADES
    # ===============================
    comp["Quantidade Total"] = comp["Consumo"] * area

    # ===============================
    # 📦 MATERIAIS
    # ===============================
    df_materiais = comp.merge(mat, on="Material", how="left")

    # 🔥 VALIDAÇÃO CRÍTICA
    faltantes = df_materiais[df_materiais["Preço"].isna()]["Material"].unique()
    if len(faltantes) > 0:
        raise ValueError(f"Materiais sem preço: {', '.join(faltantes)}")

    # 🔧 APLICA PERDAS INTELIGENTES
    def aplicar_perda(row):
        servico = row["Serviço"]
        fator = PERDAS_POR_TIPO.get(servico, FATOR_PERDA_PADRAO)
        return row["Quantidade Total"] * fator

    df_materiais["Quantidade Total"] = df_materiais.apply(aplicar_perda, axis=1)

    df_materiais["Custo"] = df_materiais["Quantidade Total"] * df_materiais["Preço"]

    resumo_materiais = (
        df_materiais.groupby(["Material", "Unidade"], as_index=False)
        .agg({
            "Quantidade Total": "sum",
            "Custo": "sum"
        })
        .sort_values("Custo", ascending=False)
    )

    custo_material_total = resumo_materiais["Custo"].sum()

    # ===============================
    # 👷 MÃO DE OBRA
    # ===============================
    lista_mo = []

    for s in comp["Serviço"].unique():

        qtd_servico = comp[comp["Serviço"] == s]["Quantidade Total"].sum()

        preco_row = mo[mo["Serviço"] == s]

        if preco_row.empty:
            raise ValueError(f"Serviço sem preço: {s}")

        preco = float(preco_row.iloc[0]["Preço"])

        valor = preco * qtd_servico

        lista_mo.append({
            "Serviço": s,
            "Quantidade": qtd_servico,
            "Custo": valor,
            "Custo/m²": valor / area
        })

    df_mo = pd.DataFrame(lista_mo).sort_values("Custo", ascending=False)

    custo_mo_total = df_mo["Custo"].sum()

    # ===============================
    # 💰 CUSTO BASE
    # ===============================
    custo_direto = custo_material_total + custo_mo_total

    # ===============================
    # 📊 BDI PROFISSIONAL
    # ===============================
    custo_total = custo_direto * (1 + INDIRETOS + IMPOSTOS + LUCRO)

    custo_m2 = custo_total / area

    # ===============================
    # 📊 PERCENTUAIS REAIS
    # ===============================
    percent_mat = custo_material_total / custo_direto if custo_direto > 0 else 0
    percent_mo = custo_mo_total / custo_direto if custo_direto > 0 else 0

    # ===============================
    # 📊 CURVA ABC (BÔNUS PROFISSIONAL)
    # ===============================
    resumo_materiais["%"] = resumo_materiais["Custo"] / custo_material_total
    resumo_materiais["% Acumulado"] = resumo_materiais["%"].cumsum()

    # ===============================
    # 🚀 RETORNO
    # ===============================
    return (
        resumo_materiais,
        df_mo,
        custo_total,
        custo_m2,
        percent_mat,
        percent_mo
    )
