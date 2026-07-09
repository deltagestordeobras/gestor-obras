import pandas as pd


COLUNA_SERVICO = "Serviço"
COLUNA_MATERIAL = "Material"
COLUNA_CONSUMO = "Consumo"
COLUNA_QUANTIDADE = "Quantidade"
COLUNA_UNIDADE = "Unidade"
COLUNA_PRECO = "Preço"
COLUNA_CUSTO = "Custo"
COLUNA_ETAPA = "Etapa"
COLUNA_FATOR_PERDA = "FatorPerda"

COLUNAS_COMPOSICAO_OBRIGATORIAS = [
    COLUNA_SERVICO,
    COLUNA_MATERIAL,
    COLUNA_CONSUMO,
]

FATOR_PERDA_PADRAO = 1.10

PERDAS_POR_SERVICO = {
    "Alvenaria": 1.10,
    "Chapisco": 1.10,
    "Concreto": 1.05,
    "Contra Piso": 1.08,
    "Pintura": 1.10,
    "Reboco Externo": 1.15,
    "Reboco Interno": 1.15,
    "Revestimento": 1.15,
}

COEFICIENTES_TECNICOS_PADRAO = {
    # Estrutura e fundação
    ("Concreto", "Cimento CP II"): 7.0,
    ("Concreto", "Areia média"): 0.55,
    ("Concreto", "Brita 1"): 0.80,
    ("Armação", "Aço CA50"): 8.0,
    ("Armação", "Arame recozido"): 0.25,
    ("Laje com Escoramento", "Concreto"): 0.10,
    ("Laje com Escoramento", "Aço CA50"): 4.5,

    # Alvenaria e argamassas
    ("Alvenaria", "Tijolo cerâmico"): 18.0,
    ("Alvenaria", "Bloco estrutural"): 12.5,
    ("Alvenaria", "Cimento CP II"): 0.10,
    ("Alvenaria", "Areia média"): 0.018,
    ("Alvenaria", "Cal hidratada"): 0.03,
    ("Chapisco", "Cimento CP II"): 0.08,
    ("Chapisco", "Areia média"): 0.015,
    ("Reboco Interno", "Cimento CP II"): 0.10,
    ("Reboco Interno", "Areia média"): 0.018,
    ("Reboco Interno", "Cal hidratada"): 0.03,
    ("Reboco Externo", "Cimento CP II"): 0.12,
    ("Reboco Externo", "Areia média"): 0.020,
    ("Reboco Externo", "Cal hidratada"): 0.03,
    ("Contra Piso", "Cimento CP II"): 0.16,
    ("Contra Piso", "Areia média"): 0.025,

    # Pisos, revestimentos e pintura
    ("Piso Cerâmico", "Argamassa AC1"): 0.22,
    ("Piso Cerâmico", "Rejunte"): 0.05,
    ("Piso Porcelanato", "Argamassa AC2"): 0.25,
    ("Piso Porcelanato", "Rejunte"): 0.05,
    ("Revestimento", "Argamassa AC1"): 0.22,
    ("Revestimento", "Argamassa AC2"): 0.25,
    ("Revestimento", "Rejunte"): 0.05,
    ("Pintura", "Tinta acrílica"): 0.18,
    ("Pintura", "Massa corrida"): 0.25,

    # Cobertura
    ("Cobertura Cerâmica", "Telha cerâmica"): 1.10,
    ("Cobertura Cerâmica", "Madeira"): 0.03,
    ("Cobertura Metálica", "Telha metálica"): 1.05,
    ("Cobertura Metálica", "Estrutura metálica"): 8.0,
    ("Cobertura Sanduíche", "Telha sanduíche"): 1.05,
    ("Cobertura Sanduíche", "Estrutura metálica"): 6.0,

    # Instalações
    ("Instalação Elétrica", "Fio 2.5mm"): 4.0,
    ("Instalação Elétrica", "Fio 4mm"): 1.2,
    ("Instalação Elétrica", "Disjuntor"): 0.03,
    ("Instalação Hidráulica", "Tubo PVC 50mm"): 0.45,
    ("Instalação Hidráulica", "Tubo PVC 100mm"): 0.25,
}


def _texto(valor):
    return str(valor or "").strip()


def _numero(valor, padrao=0.0):
    try:
        if valor is None:
            return padrao
        return float(valor)
    except (TypeError, ValueError):
        return padrao


def _normalizar_nome(valor):
    return _texto(valor).lower()


def _chave_tecnica(servico, material):
    servico_normalizado = _normalizar_nome(servico)
    material_normalizado = _normalizar_nome(material)

    for chave_servico, chave_material in COEFICIENTES_TECNICOS_PADRAO:
        if (
            _normalizar_nome(chave_servico) == servico_normalizado
            and _normalizar_nome(chave_material) == material_normalizado
        ):
            return chave_servico, chave_material

    return None


def calibrar_consumo_tecnico(servico, material, consumo):
    chave = _chave_tecnica(servico, material)

    if chave is None:
        return _numero(consumo)

    return COEFICIENTES_TECNICOS_PADRAO[chave]


def calibrar_composicao_tecnica(df_composicao):
    if df_composicao is None or df_composicao.empty:
        return pd.DataFrame()

    composicao = df_composicao.copy()

    if COLUNA_CONSUMO not in composicao.columns:
        composicao[COLUNA_CONSUMO] = 0

    composicao[COLUNA_CONSUMO] = composicao.apply(
        lambda row: calibrar_consumo_tecnico(
            row.get(COLUNA_SERVICO, ""),
            row.get(COLUNA_MATERIAL, ""),
            row.get(COLUNA_CONSUMO, 0),
        ),
        axis=1,
    )

    return composicao


def validar_composicao(df_composicao):
    if df_composicao is None:
        return False, "Composição não informada"

    if df_composicao.empty:
        return False, "Composição vazia"

    colunas_faltantes = [
        coluna for coluna in COLUNAS_COMPOSICAO_OBRIGATORIAS
        if coluna not in df_composicao.columns
    ]

    if colunas_faltantes:
        return False, f"Colunas obrigatórias ausentes: {', '.join(colunas_faltantes)}"

    composicao = calibrar_composicao_tecnica(df_composicao)
    composicao[COLUNA_CONSUMO] = pd.to_numeric(
        composicao[COLUNA_CONSUMO],
        errors="coerce",
    )

    linhas_invalidas = composicao[
        composicao[COLUNA_SERVICO].isna()
        | composicao[COLUNA_MATERIAL].isna()
        | composicao[COLUNA_CONSUMO].isna()
    ]

    if not linhas_invalidas.empty:
        return False, "Existem serviços, materiais ou consumos inválidos na composição"

    return True, None


def obter_composicao_servico(df_composicao, servico):
    ok, _ = validar_composicao(df_composicao)

    if not ok:
        return pd.DataFrame(columns=df_composicao.columns if df_composicao is not None else [])

    servico_normalizado = _normalizar_nome(servico)
    composicao = calibrar_composicao_tecnica(df_composicao)

    return composicao[
        composicao[COLUNA_SERVICO].astype(str).str.strip().str.lower()
        == servico_normalizado
    ].copy()


def calcular_consumo_materiais(servico, quantidade, df_composicao):
    quantidade = _numero(quantidade)

    if quantidade <= 0:
        return pd.DataFrame(columns=[
            COLUNA_SERVICO,
            COLUNA_MATERIAL,
            COLUNA_CONSUMO,
            COLUNA_QUANTIDADE,
        ])

    composicao_servico = obter_composicao_servico(df_composicao, servico)

    if composicao_servico.empty:
        return pd.DataFrame(columns=[
            COLUNA_SERVICO,
            COLUNA_MATERIAL,
            COLUNA_CONSUMO,
            COLUNA_QUANTIDADE,
        ])

    materiais = composicao_servico.copy()
    materiais[COLUNA_CONSUMO] = pd.to_numeric(
        materiais[COLUNA_CONSUMO],
        errors="coerce",
    ).fillna(0)

    materiais[COLUNA_QUANTIDADE] = quantidade * materiais[COLUNA_CONSUMO]

    return materiais


def calcular_materiais_por_quantitativos(quantitativos, df_composicao):
    if not quantitativos:
        return pd.DataFrame(columns=[
            COLUNA_SERVICO,
            COLUNA_MATERIAL,
            COLUNA_CONSUMO,
            COLUNA_QUANTIDADE,
        ])

    lista_materiais = []

    for servico, quantidade in quantitativos.items():
        materiais_servico = calcular_consumo_materiais(
            servico,
            quantidade,
            df_composicao,
        )

        if not materiais_servico.empty:
            lista_materiais.append(materiais_servico)

    if not lista_materiais:
        return pd.DataFrame(columns=[
            COLUNA_SERVICO,
            COLUNA_MATERIAL,
            COLUNA_CONSUMO,
            COLUNA_QUANTIDADE,
        ])

    return pd.concat(lista_materiais, ignore_index=True)


def aplicar_perdas(df_materiais):
    if df_materiais is None or df_materiais.empty:
        return pd.DataFrame()

    materiais = df_materiais.copy()

    if COLUNA_QUANTIDADE not in materiais.columns:
        materiais[COLUNA_QUANTIDADE] = 0

    materiais[COLUNA_QUANTIDADE] = pd.to_numeric(
        materiais[COLUNA_QUANTIDADE],
        errors="coerce",
    ).fillna(0)

    if COLUNA_FATOR_PERDA in materiais.columns:
        fator_perda = pd.to_numeric(
            materiais[COLUNA_FATOR_PERDA],
            errors="coerce",
        )
    else:
        fator_perda = materiais[COLUNA_SERVICO].map(PERDAS_POR_SERVICO)

    materiais[COLUNA_FATOR_PERDA] = fator_perda.fillna(FATOR_PERDA_PADRAO)
    materiais["QuantidadeSemPerda"] = materiais[COLUNA_QUANTIDADE]
    materiais[COLUNA_QUANTIDADE] = (
        materiais["QuantidadeSemPerda"] * materiais[COLUNA_FATOR_PERDA]
    )

    return materiais


def agrupar_materiais(lista_materiais):
    if lista_materiais is None:
        return pd.DataFrame(columns=[COLUNA_MATERIAL, COLUNA_QUANTIDADE])

    if isinstance(lista_materiais, pd.DataFrame):
        materiais = lista_materiais.copy()
    else:
        materiais = pd.DataFrame(lista_materiais)

    if materiais.empty:
        return pd.DataFrame(columns=[COLUNA_MATERIAL, COLUNA_QUANTIDADE])

    if COLUNA_MATERIAL not in materiais.columns:
        materiais[COLUNA_MATERIAL] = ""

    if COLUNA_QUANTIDADE not in materiais.columns:
        materiais[COLUNA_QUANTIDADE] = 0

    materiais[COLUNA_QUANTIDADE] = pd.to_numeric(
        materiais[COLUNA_QUANTIDADE],
        errors="coerce",
    ).fillna(0)

    agrupadores = [COLUNA_MATERIAL]

    if COLUNA_UNIDADE in materiais.columns:
        agrupadores.append(COLUNA_UNIDADE)

    materiais_agrupados = (
        materiais
        .groupby(agrupadores, as_index=False)
        .agg({COLUNA_QUANTIDADE: "sum"})
        .sort_values(COLUNA_QUANTIDADE, ascending=False)
    )

    return materiais_agrupados


def calcular_custos_materiais(df_materiais, tabela_materiais):
    if df_materiais is None or df_materiais.empty:
        return pd.DataFrame(columns=[
            COLUNA_MATERIAL,
            COLUNA_QUANTIDADE,
            COLUNA_UNIDADE,
            COLUNA_PRECO,
            COLUNA_CUSTO,
        ])

    materiais = df_materiais.copy()
    materiais[COLUNA_MATERIAL] = materiais[COLUNA_MATERIAL].astype(str).str.strip()

    if tabela_materiais is None or tabela_materiais.empty:
        materiais[COLUNA_UNIDADE] = ""
        materiais[COLUNA_PRECO] = 0
    else:
        precos = tabela_materiais.copy()
        if COLUNA_MATERIAL in precos.columns:
            precos[COLUNA_MATERIAL] = precos[COLUNA_MATERIAL].astype(str).str.strip()
            precos = precos.drop_duplicates(subset=[COLUNA_MATERIAL], keep="last")
            materiais = materiais.merge(
                precos[[coluna for coluna in [COLUNA_MATERIAL, COLUNA_UNIDADE, COLUNA_PRECO] if coluna in precos.columns]],
                on=COLUNA_MATERIAL,
                how="left",
            )
        else:
            materiais[COLUNA_UNIDADE] = ""
            materiais[COLUNA_PRECO] = 0

    if COLUNA_UNIDADE not in materiais.columns:
        materiais[COLUNA_UNIDADE] = ""

    if COLUNA_PRECO not in materiais.columns:
        materiais[COLUNA_PRECO] = 0

    materiais[COLUNA_QUANTIDADE] = pd.to_numeric(
        materiais[COLUNA_QUANTIDADE],
        errors="coerce",
    ).fillna(0)
    materiais[COLUNA_PRECO] = pd.to_numeric(
        materiais[COLUNA_PRECO],
        errors="coerce",
    ).fillna(0)

    materiais[COLUNA_CUSTO] = materiais[COLUNA_QUANTIDADE] * materiais[COLUNA_PRECO]

    return materiais.sort_values(COLUNA_CUSTO, ascending=False)


def calcular_curva_abc(df_custos):
    if df_custos is None or df_custos.empty or COLUNA_CUSTO not in df_custos.columns:
        return pd.DataFrame()

    curva = df_custos.copy().sort_values(COLUNA_CUSTO, ascending=False)
    total = curva[COLUNA_CUSTO].sum()

    if total <= 0:
        curva["%"] = 0
        curva["% Acumulado"] = 0
        curva["Classe ABC"] = "C"
        return curva

    curva["%"] = curva[COLUNA_CUSTO] / total
    curva["% Acumulado"] = curva["%"].cumsum()

    def classe_abc(percentual_acumulado):
        if percentual_acumulado <= 0.80:
            return "A"
        if percentual_acumulado <= 0.95:
            return "B"
        return "C"

    curva["Classe ABC"] = curva["% Acumulado"].apply(classe_abc)

    return curva