import logging
import unicodedata

import pandas as pd

from services.composicoes import (
    COLUNA_CONSUMO,
    COLUNA_CUSTO,
    COLUNA_MATERIAL,
    COLUNA_PRECO,
    COLUNA_QUANTIDADE,
    COLUNA_SERVICO,
    COLUNA_UNIDADE,
    agrupar_materiais,
    aplicar_perdas,
    calcular_curva_abc,
    calcular_custos_materiais,
    calcular_materiais_por_quantitativos,
    validar_composicao,
)
from services.composicoes_detalhadas import (
    COLUNA_MATERIAL as COLUNA_MATERIAL_DETALHADA,
    COLUNA_QUANTIDADE as COLUNA_QUANTIDADE_DETALHADA,
    COLUNA_SERVICO as COLUNA_SERVICO_DETALHADA,
    COLUNA_UNIDADE as COLUNA_UNIDADE_DETALHADA,
    calcular_materiais_por_quantitativos as calcular_materiais_detalhados_por_quantitativos,
)
from services.quantitativos import (
    calcular_quantitativos_automaticos,
    normalizar_quantitativos,
)


MAPA_ETAPAS = {
    "Marcacao Terreno": "Servicos Preliminares",
    "Demolicao": "Servicos Preliminares",
    "Furo Fundacao": "Fundacao",
    "Forma Baldrame": "Fundacao",
    "Concreto": "Fundacao",
    "Forma Pilares e Vigas": "Estrutura",
    "Armacao": "Estrutura",
    "Laje com Escoramento": "Estrutura",
    "Estrutura metalica": "Estrutura",
    "Alvenaria": "Alvenaria",
    "Chapisco": "Alvenaria",
    "Reboco Interno": "Alvenaria",
    "Reboco Externo": "Alvenaria",
    "Revestimento": "Acabamento",
    "Piso Porcelanato": "Acabamento",
    "Piso Ceramico": "Acabamento",
    "Contra Piso": "Acabamento",
    "Pintura": "Pintura",
    "Instalacao Eletrica": "Instalacoes",
    "Instalacao Hidraulica": "Instalacoes",
    "Cobertura Ceramica": "Cobertura",
    "Cobertura Metalica": "Cobertura",
    "Cobertura Sanduiche": "Cobertura",
    "Portas Internas": "Esquadrias",
    "Portas Externas": "Esquadrias",
    "Janelas Aluminio": "Esquadrias",
    "Vidro": "Esquadrias",
    "Vaso Sanitario": "Loucas e Metais",
    "Cuba": "Loucas e Metais",
    "Torneira": "Loucas e Metais",
    "Chuveiro": "Loucas e Metais",
    "Tanque": "Loucas e Metais",
    "Sifao": "Loucas e Metais",
    "Engate Flexivel": "Loucas e Metais",
}

MAPA_ETAPAS.update({
    "Marcação Terreno": "Serviços Preliminares",
    "Demolição": "Serviços Preliminares",
    "Furo Fundação": "Fundação",
    "Forma Baldrame": "Fundação",
    "Concreto": "Fundação",
    "Armação": "Estrutura",
    "Estrutura metálica": "Estrutura",
    "Piso Cerâmico": "Acabamento",
    "Instalação Elétrica": "Instalações",
    "Instalação Hidráulica": "Instalações",
    "Cobertura Cerâmica": "Cobertura",
    "Cobertura Metálica": "Cobertura",
    "Cobertura Sanduíche": "Cobertura",
    "Vaso Sanitário": "Louças e Metais",
    "Engate Flexível": "Louças e Metais",
})

PARAMETROS_FINANCEIROS_PADRAO = {
    "indiretos": 0,
    "impostos": 0,
    "lucro": 0,
}

SERVICOS_AUTOMATICOS_CRITICOS = {
    "armacao",
    "concreto",
    "forma pilares e vigas",
    "furo fundacao",
}

COEFICIENTE_ARMACAO_COMPOSICAO = 8.0

SERVICOS_OFICIAIS = {
    "marcacao terreno": "Marcacao Terreno",
    "demolicao": "Demolicao",
    "furo fundacao": "Furo Fundacao",
    "forma baldrame": "Forma Baldrame",
    "concreto": "Concreto",
    "forma pilares e vigas": "Forma Pilares e Vigas",
    "armacao": "Armacao",
    "laje com escoramento": "Laje com Escoramento",
    "estrutura metalica": "Estrutura metalica",
    "alvenaria": "Alvenaria",
    "chapisco": "Chapisco",
    "reboco interno": "Reboco Interno",
    "reboco externo": "Reboco Externo",
    "revestimento": "Revestimento",
    "piso porcelanato": "Piso Porcelanato",
    "piso ceramico": "Piso Ceramico",
    "contra piso": "Contra Piso",
    "pintura": "Pintura",
    "instalacao eletrica": "Instalacao Eletrica",
    "instalacao hidraulica": "Instalacao Hidraulica",
    "cobertura ceramica": "Cobertura Ceramica",
    "cobertura metalica": "Cobertura Metalica",
    "cobertura sanduiche": "Cobertura Sanduiche",
    "portas internas": "Portas Internas",
    "portas externas": "Portas Externas",
    "janelas aluminio": "Janelas Aluminio",
    "vidro": "Vidro",
    "vaso sanitario": "Vaso Sanitario",
    "cuba": "Cuba",
    "torneira": "Torneira",
    "chuveiro": "Chuveiro",
    "tanque": "Tanque",
    "sifao": "Sifao",
    "engate flexivel": "Engate Flexivel",
}

PRECOS_MATERIAIS_COMPLEMENTARES = {
    "porta interna semioca": 650.0,
    "porta externa macica": 1400.0,
    "batente madeira": 250.0,
    "guarnicao madeira": 180.0,
    "fechadura interna": 140.0,
    "fechadura externa": 260.0,
    "dobradica 3": 28.0,
    "dobradica reforcada": 55.0,
    "janela aluminio com vidro": 1100.0,
    "vidro temperado 8mm": 380.0,
    "parafuso e bucha 8mm": 1.2,
    "silicone vedacao": 28.0,
    "eletroduto corrugado 20mm": 3.2,
    "eletroduto corrugado 25mm": 4.4,
    "cabo flexivel 1.5mm2": 1.9,
    "cabo flexivel 2.5mm2": 2.8,
    "cabo flexivel 4mm2": 4.2,
    "cabo flexivel 6mm2": 6.8,
    "quadro de distribuicao qdc": 450.0,
    "disjuntor monopolar": 28.0,
    "disjuntor bipolar": 48.0,
    "dr residual": 180.0,
    "caixa 4x2": 4.5,
    "caixa 4x4": 7.5,
    "tomada 10a": 35.0,
    "interruptor simples": 30.0,
    "fita isolante": 8.0,
    "tubo pvc soldavel 25mm": 8.0,
    "tubo pvc soldavel 32mm": 14.0,
    "tubo pvc esgoto 40mm": 12.0,
    "tubo pvc esgoto 50mm": 18.0,
    "tubo pvc esgoto 100mm": 35.0,
    "conexoes pvc soldavel": 7.5,
    "conexoes pvc esgoto": 9.5,
    "registro gaveta": 75.0,
    "registro pressao": 65.0,
    "caixa gordura": 180.0,
    "caixa inspecao": 160.0,
    "cola pvc": 22.0,
    "fita veda rosca": 5.0,
    "ralo sifonado": 32.0,
    "vaso sanitario com caixa acoplada": 350.0,
    "cuba lavatorio": 220.0,
    "cuba inox cozinha": 280.0,
    "torneira lavatorio": 85.0,
    "torneira cozinha": 150.0,
    "torneira tanque": 70.0,
    "chuveiro eletrico": 120.0,
    "tanque louca/sintetico": 260.0,
    "tanque louca sintetico": 260.0,
    "sifao lavatorio": 25.0,
    "sifao cozinha": 35.0,
    "engate flexivel": 18.0,
    "porcelanato": 150.0,
    "ceramica piso": 55.0,
    "ceramica parede": 60.0,
    "argamassa ac1": 18.0,
    "argamassa ac2": 28.0,
    "rejunte": 9.0,
    "rejunte porcelanato": 12.0,
    "selador acrilico": 18.0,
    "selador acrilico externo": 22.0,
    "massa corrida pva": 6.0,
    "tinta acrilica premium": 32.0,
    "tinta acrilica externa": 35.0,
    "textura acrilica": 9.0,
    "lixa parede": 2.0,
    "concreto": 550.0,
}


def corrigir_mojibake(texto):
    texto = str(texto or "")

    substituicoes = {
        # acentuação corrompida com ?
        "Servi?o": "Serviço",
        "servi?o": "serviço",
        "Observa??o": "Observação",
        "observa??o": "observação",
        "Pre?o": "Preço",
        "pre?o": "preço",

        "Funda??o": "Fundação",
        "funda??o": "fundação",
        "Arma??o": "Armação",
        "arma??o": "armação",
        "Instala??o": "Instalação",
        "instala??o": "instalação",
        "Instala??es": "Instalações",
        "instala??es": "instalações",
        "Impermeabiliza??o": "Impermeabilização",
        "impermeabiliza??o": "impermeabilização",
        "Distribui??o": "Distribuição",
        "distribui??o": "distribuição",
        "Veda??o": "Vedação",
        "veda??o": "vedação",
        "Conex?es": "Conexões",
        "conex?es": "conexões",
        "Inspe??o": "Inspeção",
        "inspe??o": "inspeção",

        "A?o": "Aço",
        "a?o": "aço",
        "A?o CA50": "Aço CA50",
        "A?o CA60": "Aço CA60",

        "?rea": "Área",
        "?rea Servi?o": "Área Serviço",
        "m?": "m²",
        "mm?": "mm²",

        "m?dio": "médio",
        "M?dio": "Médio",
        "m?dia": "média",
        "M?dia": "Média",
        "m?": "m³",

        "consum?vel": "consumível",
        "Consum?vel": "Consumível",

        "lou?a": "louça",
        "Lou?a": "Louça",
        "lou?as": "louças",
        "Lou?as": "Louças",

        "el?trico": "elétrico",
        "El?trico": "Elétrico",
        "el?trica": "elétrica",
        "El?trica": "Elétrica",

        "hidr?ulico": "hidráulico",
        "Hidr?ulico": "Hidráulico",
        "hidr?ulica": "hidráulica",
        "Hidr?ulica": "Hidráulica",

        "acr?lico": "acrílico",
        "Acr?lico": "Acrílico",
        "acr?lica": "acrílica",
        "Acr?lica": "Acrílica",

        "Cer?mica": "Cerâmica",
        "cer?mica": "cerâmica",
        "cer?mico": "cerâmico",
        "Cer?mico": "Cerâmico",

        "Met?lica": "Metálica",
        "met?lica": "metálica",
        "met?lico": "metálico",
        "Met?lico": "Metálico",

        "t?rmica": "térmica",
        "T?rmica": "Térmica",
        "Sandu?che": "Sanduíche",
        "sandu?che": "sanduíche",
        "termoac?stica": "termoacústica",

        "polim?rica": "polimérica",
        "asf?ltico": "asfáltico",
        "sint?tico": "sintético",
        "Sint?tico": "Sintético",
        "sint?tico": "sintético",
        "sint?tica": "sintética",

        "flex?vel": "flexível",
        "Flex?vel": "Flexível",
        "sold?vel": "soldável",
        "press?o": "pressão",
        "gaveta": "gaveta",

        "lavat?rio": "lavatório",
        "Lavat?rio": "Lavatório",
        "sanit?rio": "sanitário",
        "Sanit?rio": "Sanitário",
        "Sif?o": "Sifão",
        "sif?o": "sifão",

        "Guarni??o": "Guarnição",
        "guarni??o": "guarnição",
        "Dobradi?a": "Dobradiça",
        "dobradi?a": "dobradiça",
        "Dobradiça refor?ada": "Dobradiça reforçada",
        "dobradiça refor?ada": "dobradiça reforçada",
        "Dobradi?a refor?ada": "Dobradiça reforçada",
        "dobradi?a refor?ada": "dobradiça reforçada",

        "Alum?nio": "Alumínio",
        "alum?nio": "alumínio",
        "maci?a": "maciça",
        "Maci?a": "Maciça",
        "vedacao": "vedação",
        "veda??o": "vedação",
    }

    for original, corrigido in substituicoes.items():
        texto = texto.replace(original, corrigido)

    # tenta corrigir mojibake clássico, sem forçar troca global de '?'
    for _ in range(3):
        try:
            corrigido = texto.encode("latin1").decode("utf-8")
        except UnicodeError:
            break

        if corrigido == texto:
            break

        texto = corrigido

        for original, corrigido_mapeado in substituicoes.items():
            texto = texto.replace(original, corrigido_mapeado)

    return texto


def _corrigir_mojibake(valor):
    return corrigir_mojibake(valor)


def _normalizar_nome(valor):
    texto = _corrigir_mojibake(valor)

    # Corrige unidades comuns sem substituir '?' globalmente.
    texto = texto.replace("m?", "m2")
    texto = texto.replace("mm?", "mm2")

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = "".join(ch.lower() if ch.isalnum() else " " for ch in texto)

    return " ".join(texto.split())

def _normalizar_material_exibicao(valor):
    return " ".join(corrigir_mojibake(valor).strip().split())


def _numero(valor, padrao=0.0):
    try:
        if valor is None:
            return padrao
        return float(valor)
    except (TypeError, ValueError):
        return padrao


def _dataframe_vazio(colunas):
    return pd.DataFrame(columns=colunas)


def _obter_coluna(df, nomes):
    if df is None or df.empty:
        return None

    nomes_normalizados = {_normalizar_nome(nome) for nome in nomes}

    for coluna in df.columns:
        if _normalizar_nome(coluna) in nomes_normalizados:
            return coluna

    return None


def _renomear_colunas(df, mapa_colunas):
    if df is None:
        return pd.DataFrame()

    tabela = df.copy()
    renomear = {}

    for destino, aliases in mapa_colunas.items():
        coluna = _obter_coluna(tabela, [destino] + list(aliases))

        if coluna and coluna != destino:
            renomear[coluna] = destino

    if renomear:
        tabela = tabela.rename(columns=renomear)

    return tabela


def _preparar_tabela_composicao(tabela_composicao):
    tabela = _renomear_colunas(
        tabela_composicao,
        {
            COLUNA_SERVICO: ["Servico", "Servico"],
            COLUNA_MATERIAL: ["Material"],
            COLUNA_CONSUMO: ["Consumo"],
        },
    )

    if tabela.empty or COLUNA_SERVICO not in tabela.columns:
        return tabela

    tabela[COLUNA_SERVICO] = tabela[COLUNA_SERVICO].apply(_servico_oficial)

    return tabela

def _preparar_tabela_materiais(tabela_materiais):
    tabela = _renomear_colunas(
        tabela_materiais,
        {
            COLUNA_MATERIAL: ["Material"],
            COLUNA_UNIDADE: ["Unidade"],
            COLUNA_PRECO: ["Preco", "Preco"],
        },
    )

    if not tabela.empty and COLUNA_MATERIAL in tabela.columns:
        tabela[COLUNA_MATERIAL] = tabela[COLUNA_MATERIAL].apply(_normalizar_material_exibicao)

    return tabela


def _obter_parametros_financeiros(parametros=None):
    parametros_finais = PARAMETROS_FINANCEIROS_PADRAO.copy()

    if parametros:
        for chave in parametros_finais:
            parametros_finais[chave] = _numero(parametros.get(chave), parametros_finais[chave])

    return parametros_finais


def _servico_oficial(servico):
    return SERVICOS_OFICIAIS.get(_normalizar_nome(servico), _corrigir_mojibake(servico).strip())


def _adicionar_quantitativo(quantitativos, servico, quantidade, substituir=False):
    quantidade = _numero(quantidade)

    if quantidade <= 0:
        return

    servico = _servico_oficial(servico)

    if substituir:
        quantitativos[servico] = quantidade
    else:
        quantitativos[servico] = _numero(quantitativos.get(servico, 0)) + quantidade


def _normalizar_quantitativos_manuais(quantidades_manuais):
    quantitativos = {}

    for servico, quantidade in (quantidades_manuais or {}).items():
        _adicionar_quantitativo(quantitativos, servico, quantidade)

    return quantitativos


def _obter_quantitativo(quantitativos, servico):
    alvo = _normalizar_nome(servico)

    for nome_servico, quantidade in (quantitativos or {}).items():
        if _normalizar_nome(nome_servico) == alvo:
            return _numero(quantidade)

    return 0.0


def _obter_etapa(servico, mapa_etapas=None):
    mapa = mapa_etapas or MAPA_ETAPAS
    servico_normalizado = _normalizar_nome(servico)

    for nome_servico, etapa in mapa.items():
        if _normalizar_nome(nome_servico) == servico_normalizado:
            return etapa

    logging.warning("Serviço sem etapa mapeada no orçamento técnico: %s", servico)
    return "Outros"


def _valor_estrutura(dados_obra, estrutura, chave, padrao=0.0):
    return _numero(dados_obra.get(chave, estrutura.get(chave, padrao)), padrao)


def _usar_quantitativos_projeto_estrutural(dados_obra, estrutura):
    return bool(
        dados_obra.get(
            "usar_quantitativos_projeto_estrutural",
            estrutura.get("usar_quantitativos_projeto", False),
        )
    )


def _aplicar_quantitativos_projeto_estrutural(quantitativos, dados_obra, estrutura):
    for servico in list(quantitativos):
        nome_servico = _normalizar_nome(servico)

        if (
            nome_servico in {"concreto", "armacao", "forma pilares e vigas"}
            or ("furo" in nome_servico and "funda" in nome_servico)
        ):
            quantitativos.pop(servico, None)

    volume_concreto = _valor_estrutura(
        dados_obra,
        estrutura,
        "projeto_volume_concreto_m3",
    )
    aco_ca50 = _valor_estrutura(dados_obra, estrutura, "projeto_aco_ca50_kg")
    aco_ca60 = _valor_estrutura(dados_obra, estrutura, "projeto_aco_ca60_kg")
    area_forma = _valor_estrutura(dados_obra, estrutura, "projeto_area_forma_m2")

    if volume_concreto > 0:
        quantitativos["Concreto"] = volume_concreto

    aco_total = aco_ca50 + aco_ca60

    if aco_total > 0:
        quantitativos["Armacao"] = aco_total

    if area_forma > 0:
        quantitativos["Forma Pilares e Vigas"] = area_forma

    return quantitativos


def preparar_quantitativos(dados_obra):
    quantidades_manuais = dados_obra.get("quantidades_servicos", {}) or {}
    estrutura = dados_obra.get("estrutura", {}) or {}
    implantacao = dados_obra.get("implantacao", {}) or {}

    area_laje = dados_obra.get("area_laje", estrutura.get("area_laje", 0))
    espessura_laje_cm = dados_obra.get(
        "espessura_laje_cm",
        estrutura.get("espessura_laje_cm", dados_obra.get("espessura_piso_cm", 0)),
    )
    tipo_fundacao = dados_obra.get("tipo_fundacao", estrutura.get("tipo_fundacao"))
    volume_estimado_concreto = dados_obra.get(
        "volume_estimado_concreto",
        estrutura.get("volume_estimado_concreto", 0),
    )
    comprimento_baldrame = dados_obra.get(
        "comprimento_baldrame",
        estrutura.get("comprimento_baldrame", implantacao.get("perimetro_externo", 0)),
    )
    largura_baldrame_cm = dados_obra.get(
        "largura_baldrame_cm",
        estrutura.get("largura_baldrame_cm", 0),
    )
    altura_baldrame_cm = dados_obra.get(
        "altura_baldrame_cm",
        estrutura.get("altura_baldrame_cm", 0),
    )

    quantitativos_automaticos = calcular_quantitativos_automaticos(
        area_total=dados_obra.get("area_total", 0),
        area_piso=dados_obra.get("area_piso", 0),
        espessura_piso_cm=dados_obra.get("espessura_piso_cm", 0),
        area_laje=area_laje,
        espessura_laje_cm=espessura_laje_cm,
        comprimento_viga=dados_obra.get("comprimento_viga", 0),
        largura_viga_cm=dados_obra.get("largura_viga_cm", 0),
        altura_viga_cm=dados_obra.get("altura_viga_cm", 0),
        comprimento_pilar=dados_obra.get("comprimento_pilar", 0),
        largura_pilar_cm=dados_obra.get("largura_pilar_cm", 0),
        altura_pilar_cm=dados_obra.get("altura_pilar_cm", 0),
        tipo_fundacao=tipo_fundacao,
        volume_estimado_concreto=volume_estimado_concreto,
        comprimento_baldrame=comprimento_baldrame,
        largura_baldrame_cm=largura_baldrame_cm,
        altura_baldrame_cm=altura_baldrame_cm,
        quantidade_tubuloes=dados_obra.get("quantidade_tubuloes", 0),
        diametro_tubulao_cm=dados_obra.get("diametro_tubulao_cm", 0),
        profundidade_tubulao_m=dados_obra.get("profundidade_tubulao_m", 0),
        area_cobertura=dados_obra.get("area_cobertura", 0),
        tipo_cobertura=dados_obra.get("tipo_cobertura"),
        incluir_piso_porcelanato=dados_obra.get("incluir_piso_porcelanato", True),
        pavimentos=dados_obra.get("pavimentos", estrutura.get("pavimentos", 1)),
    )

    if _usar_quantitativos_projeto_estrutural(dados_obra, estrutura):
        quantitativos_automaticos = _aplicar_quantitativos_projeto_estrutural(
            quantitativos_automaticos,
            dados_obra,
            estrutura,
        )

    quantitativos = _normalizar_quantitativos_manuais(quantidades_manuais)

    for servico, quantidade in quantitativos_automaticos.items():
        servico_oficial = _servico_oficial(servico)
        quantidade = _numero(quantidade)

        if quantidade <= 0:
            continue

        if _normalizar_nome(servico_oficial) in SERVICOS_AUTOMATICOS_CRITICOS:
            quantitativos[servico_oficial] = quantidade
            continue

        if _obter_quantitativo(quantitativos, servico_oficial) <= 0:
            quantitativos[servico_oficial] = quantidade

    return quantitativos


def preparar_quantitativos_complementares(dados_obra, quantitativos_base=None):
    area_total = _numero(dados_obra.get("area_total", 0))
    esquadrias = dados_obra.get("esquadrias", {}) or {}
    instalacoes = dados_obra.get("instalacoes", {}) or {}
    hidraulica = instalacoes.get("hidraulica", {}) or {}
    acabamento = dados_obra.get("acabamento", {}) or {}
    loucas_metais = dados_obra.get("loucas_metais", {}) or {}
    complementares = {}

    _adicionar_quantitativo(complementares, "Portas Internas", esquadrias.get("portas_internas", 0))
    _adicionar_quantitativo(complementares, "Portas Externas", esquadrias.get("portas_externas", 0))
    _adicionar_quantitativo(complementares, "Janelas Aluminio", esquadrias.get("area_total_janelas", 0))
    _adicionar_quantitativo(complementares, "Vidro", esquadrias.get("area_total_vidro", 0))

    if area_total > 0:
        _adicionar_quantitativo(complementares, "Instalacao Eletrica", area_total)
        _adicionar_quantitativo(complementares, "Instalacao Hidraulica", area_total)

    banheiros = _numero(hidraulica.get("banheiros", 0))
    cozinha = _numero(hidraulica.get("cozinha", 0))
    area_servico = _numero(hidraulica.get("area_servico", 0))
    cubas = _numero(loucas_metais.get("cubas", 0))

    _adicionar_quantitativo(complementares, "Vaso Sanitario", loucas_metais.get("vasos_sanitarios", 0))
    _adicionar_quantitativo(complementares, "Cuba", cubas)
    _adicionar_quantitativo(complementares, "Torneira", loucas_metais.get("torneiras", 0))
    _adicionar_quantitativo(complementares, "Chuveiro", loucas_metais.get("chuveiros", 0))
    _adicionar_quantitativo(complementares, "Tanque", loucas_metais.get("tanques", 0))
    _adicionar_quantitativo(complementares, "Sifao", max(cubas, banheiros + cozinha + area_servico))
    _adicionar_quantitativo(complementares, "Engate Flexivel", max(cubas * 2, loucas_metais.get("torneiras", 0)))

    piso_porcelanato = _obter_quantitativo(quantitativos_base, "Piso Porcelanato")
    piso_ceramico = _obter_quantitativo(quantitativos_base, "Piso Ceramico")

    if piso_porcelanato > 0:
        _adicionar_quantitativo(complementares, "Piso Porcelanato", piso_porcelanato)
    elif piso_ceramico > 0:
        _adicionar_quantitativo(complementares, "Piso Ceramico", piso_ceramico)
    else:
        _adicionar_quantitativo(complementares, "Piso Porcelanato", dados_obra.get("area_piso", 0))

    _adicionar_quantitativo(
        complementares,
        "Revestimento Parede",
        acabamento.get("area_revestimento_parede", 0),
    )
    _adicionar_quantitativo(
        complementares,
        "Pintura Interna",
        acabamento.get("area_pintura_interna", 0),
    )
    _adicionar_quantitativo(
        complementares,
        "Pintura Externa",
        acabamento.get("area_pintura_externa", 0),
    )

    return complementares


def ajustar_quantitativos_para_composicao(quantitativos):
    quantitativos_composicao = dict(quantitativos or {})
    armacao_kg = _obter_quantitativo(quantitativos_composicao, "Armacao")

    if armacao_kg > 0:
        for servico in list(quantitativos_composicao):
            if _normalizar_nome(servico) == "armacao":
                quantitativos_composicao[servico] = armacao_kg / COEFICIENTE_ARMACAO_COMPOSICAO

    return quantitativos_composicao


def calcular_mao_de_obra(quantitativos, tabela_mao_obra, mapa_etapas=None):
    colunas = ["Servico", "Etapa", "Quantidade", "Preco", "Custo"]

    if not quantitativos or tabela_mao_obra is None or tabela_mao_obra.empty:
        return _dataframe_vazio(colunas)

    servico_col = _obter_coluna(tabela_mao_obra, ["Servico", "Servico"])
    preco_col = _obter_coluna(tabela_mao_obra, ["Preco", "Preco"])

    if not servico_col or not preco_col:
        return _dataframe_vazio(colunas)

    registros = []

    for _, row in tabela_mao_obra.iterrows():
        servico = _servico_oficial(row.get(servico_col, ""))
        quantidade = _obter_quantitativo(quantitativos, servico)

        if not servico or quantidade <= 0:
            continue

        preco = _numero(row.get(preco_col, 0))
        custo = quantidade * preco

        registros.append({
            "Servico": servico,
            "Etapa": _obter_etapa(servico, mapa_etapas),
            "Quantidade": quantidade,
            "Preco": preco,
            "Custo": custo,
        })

    if not registros:
        return _dataframe_vazio(colunas)

    return pd.DataFrame(registros).sort_values("Custo", ascending=False)


def _converter_materiais_detalhados(df_materiais):
    if df_materiais is None or df_materiais.empty:
        return pd.DataFrame(columns=[COLUNA_SERVICO, COLUNA_MATERIAL, COLUNA_QUANTIDADE, COLUNA_UNIDADE])

    materiais = df_materiais.copy()
    registros = pd.DataFrame({
        COLUNA_SERVICO: materiais.get(COLUNA_SERVICO_DETALHADA, ""),
        COLUNA_MATERIAL: materiais.get(COLUNA_MATERIAL_DETALHADA, ""),
        COLUNA_QUANTIDADE: pd.to_numeric(
            materiais.get(COLUNA_QUANTIDADE_DETALHADA, 0),
            errors="coerce",
        ).fillna(0),
    })

    if COLUNA_UNIDADE_DETALHADA in materiais.columns:
        registros[COLUNA_UNIDADE] = materiais[COLUNA_UNIDADE_DETALHADA]

    registros[COLUNA_MATERIAL] = registros[COLUNA_MATERIAL].apply(_normalizar_material_exibicao)

    return registros


def _adicionar_precos_complementares(tabela_materiais, materiais_agrupados):
    tabela = _preparar_tabela_materiais(tabela_materiais)

    if tabela.empty:
        tabela = pd.DataFrame(columns=[COLUNA_MATERIAL, COLUNA_UNIDADE, COLUNA_PRECO])

    materiais_com_preco = set()

    if COLUNA_MATERIAL in tabela.columns:
        materiais_com_preco = {
            _normalizar_nome(material)
            for material in tabela[COLUNA_MATERIAL].dropna().tolist()
        }

    novos = []

    if materiais_agrupados is not None and not materiais_agrupados.empty:
        for _, row in materiais_agrupados.iterrows():
            material = _normalizar_material_exibicao(row.get(COLUNA_MATERIAL, ""))
            chave_material = _normalizar_nome(material)

            if not material or chave_material in materiais_com_preco:
                continue

            preco = PRECOS_MATERIAIS_COMPLEMENTARES.get(chave_material)

            if preco is None:
                continue

            novos.append({
                COLUNA_MATERIAL: material,
                COLUNA_UNIDADE: row.get(COLUNA_UNIDADE, ""),
                COLUNA_PRECO: preco,
            })
            materiais_com_preco.add(chave_material)

    if novos:
        tabela = pd.concat([tabela, pd.DataFrame(novos)], ignore_index=True)

    return tabela


def gerar_lista_materiais(
    quantitativos,
    tabela_composicao,
    tabela_materiais,
    aplicar_fator_perda=True,
    quantitativos_complementares=None,
    area_total=0,
):
    tabela_composicao = _preparar_tabela_composicao(tabela_composicao)
    ok, erro = validar_composicao(tabela_composicao)

    if not ok:
        return {
            "ok": False,
            "erro": erro,
            "materiais_servicos": _dataframe_vazio([
                COLUNA_SERVICO,
                COLUNA_MATERIAL,
                COLUNA_QUANTIDADE,
            ]),
            "materiais_agrupados": _dataframe_vazio([
                COLUNA_MATERIAL,
                COLUNA_QUANTIDADE,
            ]),
            "materiais_custos": _dataframe_vazio([
                COLUNA_MATERIAL,
                COLUNA_QUANTIDADE,
                COLUNA_PRECO,
                COLUNA_CUSTO,
            ]),
        }

    quantitativos_composicao = ajustar_quantitativos_para_composicao(quantitativos)
    materiais_base = calcular_materiais_por_quantitativos(
        quantitativos_composicao,
        tabela_composicao,
    )

    if aplicar_fator_perda:
        materiais_base = aplicar_perdas(materiais_base)

    materiais_complementares = calcular_materiais_detalhados_por_quantitativos(
        quantitativos=quantitativos_complementares or {},
        area_total=area_total,
        aplicar_perdas=aplicar_fator_perda,
    )
    materiais_complementares = _converter_materiais_detalhados(materiais_complementares)

    grupos_materiais = [
        grupo
        for grupo in [materiais_base, materiais_complementares]
        if grupo is not None and not grupo.empty
    ]

    if grupos_materiais:
        materiais_servicos = pd.concat(grupos_materiais, ignore_index=True)
    else:
        materiais_servicos = _dataframe_vazio([
            COLUNA_SERVICO,
            COLUNA_MATERIAL,
            COLUNA_QUANTIDADE,
        ])

    materiais_servicos[COLUNA_MATERIAL] = materiais_servicos[COLUNA_MATERIAL].apply(_normalizar_material_exibicao)

    if COLUNA_UNIDADE not in materiais_servicos.columns:
        materiais_servicos[COLUNA_UNIDADE] = ""
    else:
        materiais_servicos[COLUNA_UNIDADE] = materiais_servicos[COLUNA_UNIDADE].fillna("")

    materiais_agrupados = agrupar_materiais(materiais_servicos)
    tabela_materiais = _adicionar_precos_complementares(tabela_materiais, materiais_agrupados)
    materiais_custos = calcular_custos_materiais(
        materiais_agrupados,
        tabela_materiais,
    )

    return {
        "ok": True,
        "erro": None,
        "materiais_servicos": materiais_servicos,
        "materiais_agrupados": materiais_agrupados,
        "materiais_custos": materiais_custos,
    }


def calcular_custos_etapas(
    df_mao_obra,
    df_materiais_servicos=None,
    df_materiais_custos=None,
    mapa_etapas=None,
):
    custos = {}

    if df_mao_obra is not None and not df_mao_obra.empty:
        for _, row in df_mao_obra.iterrows():
            etapa = row.get("Etapa") or _obter_etapa(row.get("Servico"), mapa_etapas)
            custos.setdefault(etapa, {"Mao de Obra": 0, "Material": 0, "Total": 0})
            custos[etapa]["Mao de Obra"] += _numero(row.get("Custo", 0))

    if (
        df_materiais_servicos is not None
        and not df_materiais_servicos.empty
        and df_materiais_custos is not None
        and not df_materiais_custos.empty
    ):
        custo_unitario = {}

        for _, row in df_materiais_custos.iterrows():
            quantidade = _numero(row.get(COLUNA_QUANTIDADE, 0))
            custo = _numero(row.get(COLUNA_CUSTO, 0))

            if quantidade > 0:
                custo_unitario[row.get(COLUNA_MATERIAL)] = custo / quantidade

        for _, row in df_materiais_servicos.iterrows():
            servico = row.get(COLUNA_SERVICO)
            material = row.get(COLUNA_MATERIAL)
            etapa = row.get("Etapa") or _obter_etapa(servico, mapa_etapas)
            quantidade = _numero(row.get(COLUNA_QUANTIDADE, 0))
            custo = quantidade * _numero(custo_unitario.get(material, 0))

            custos.setdefault(etapa, {"Mao de Obra": 0, "Material": 0, "Total": 0})
            custos[etapa]["Material"] += custo

    registros = []

    for etapa, valores in custos.items():
        total = valores["Mao de Obra"] + valores["Material"]
        registros.append({
            "Etapa": etapa,
            "Mao de Obra": valores["Mao de Obra"],
            "Material": valores["Material"],
            "Total": total,
        })

    if not registros:
        return _dataframe_vazio(["Etapa", "Mao de Obra", "Material", "Total"])

    return pd.DataFrame(registros).sort_values("Total", ascending=False)


def calcular_resumo_financeiro(
    df_mao_obra,
    df_materiais_custos,
    area_total=0,
    parametros_financeiros=None,
):
    parametros = _obter_parametros_financeiros(parametros_financeiros)

    custo_mao_obra = 0
    if df_mao_obra is not None and not df_mao_obra.empty:
        custo_mao_obra = df_mao_obra["Custo"].sum()

    custo_material = 0
    if df_materiais_custos is not None and not df_materiais_custos.empty:
        custo_material = df_materiais_custos[COLUNA_CUSTO].sum()

    custo_direto = custo_mao_obra + custo_material
    fator_bdi = 1 + parametros["indiretos"] + parametros["impostos"] + parametros["lucro"]
    custo_total = custo_direto * fator_bdi
    area_total = _numero(area_total)
    custo_m2 = custo_total / area_total if area_total > 0 else 0

    return {
        "custo_mao_obra": custo_mao_obra,
        "custo_material": custo_material,
        "custo_direto": custo_direto,
        "indiretos": custo_direto * parametros["indiretos"],
        "impostos": custo_direto * parametros["impostos"],
        "lucro": custo_direto * parametros["lucro"],
        "custo_total": custo_total,
        "custo_m2": custo_m2,
        "percentual_material": custo_material / custo_direto if custo_direto > 0 else 0,
        "percentual_mao_obra": custo_mao_obra / custo_direto if custo_direto > 0 else 0,
        "parametros": parametros,
    }


def gerar_curva_abc(df_materiais_custos):
    return calcular_curva_abc(df_materiais_custos)


def consolidar_orcamento(
    quantitativos,
    df_mao_obra,
    lista_materiais,
    df_custos_etapas,
    resumo_financeiro,
):
    return {
        "quantitativos": quantitativos,
        "mao_obra": df_mao_obra,
        "materiais_servicos": lista_materiais.get("materiais_servicos"),
        "materiais_agrupados": lista_materiais.get("materiais_agrupados"),
        "materiais_custos": lista_materiais.get("materiais_custos"),
        "custos_etapas": df_custos_etapas,
        "curva_abc": gerar_curva_abc(lista_materiais.get("materiais_custos")),
        "resumo": resumo_financeiro,
        "alertas": [],
    }


def gerar_orcamento_completo(dados_obra):
    tabela_composicao = dados_obra.get("tabela_composicao")
    tabela_materiais = dados_obra.get("tabela_materiais")
    tabela_mao_obra = dados_obra.get("tabela_mao_obra")
    mapa_etapas = dados_obra.get("mapa_etapas") or MAPA_ETAPAS
    estrutura = dados_obra.get("estrutura", {}) or {}

    if _usar_quantitativos_projeto_estrutural(dados_obra, estrutura):
        quantitativos_estruturais = [
            _valor_estrutura(dados_obra, estrutura, "projeto_volume_concreto_m3"),
            _valor_estrutura(dados_obra, estrutura, "projeto_aco_ca50_kg"),
            _valor_estrutura(dados_obra, estrutura, "projeto_aco_ca60_kg"),
            _valor_estrutura(dados_obra, estrutura, "projeto_area_forma_m2"),
        ]
        if all(valor <= 0 for valor in quantitativos_estruturais):
            raise ValueError("Quantitativos estruturais não carregados.")

    quantitativos = preparar_quantitativos(dados_obra)
    quantitativos_complementares = preparar_quantitativos_complementares(
        dados_obra,
        quantitativos,
    )

    df_mao_obra = calcular_mao_de_obra(
        quantitativos,
        tabela_mao_obra,
        mapa_etapas=mapa_etapas,
    )

    lista_materiais = gerar_lista_materiais(
        quantitativos,
        tabela_composicao,
        tabela_materiais,
        aplicar_fator_perda=dados_obra.get("aplicar_perdas", True),
        quantitativos_complementares=quantitativos_complementares,
        area_total=dados_obra.get("area_total", 0),
    )

    df_custos_etapas = calcular_custos_etapas(
        df_mao_obra,
        lista_materiais.get("materiais_servicos"),
        lista_materiais.get("materiais_custos"),
        mapa_etapas=mapa_etapas,
    )

    resumo_financeiro = calcular_resumo_financeiro(
        df_mao_obra,
        lista_materiais.get("materiais_custos"),
        area_total=dados_obra.get("area_total", 0),
        parametros_financeiros=dados_obra.get("parametros_financeiros"),
    )

    orcamento = consolidar_orcamento(
        quantitativos,
        df_mao_obra,
        lista_materiais,
        df_custos_etapas,
        resumo_financeiro,
    )
    orcamento["quantitativos_complementares"] = quantitativos_complementares

    if not lista_materiais.get("ok", True):
        orcamento["alertas"].append(lista_materiais.get("erro"))

    return orcamento











