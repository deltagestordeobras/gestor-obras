import pandas as pd


SERVICO_PINTURA = "Pintura"
SERVICO_REVESTIMENTO = "Revestimento"

PISOS_SERVICOS = {
    "porcelanato": "Piso Porcelanato",
    "piso porcelanato": "Piso Porcelanato",
    "ceramico": "Piso Cerâmico",
    "cerâmico": "Piso Cerâmico",
    "piso ceramico": "Piso Cerâmico",
    "piso cerâmico": "Piso Cerâmico",
}

TIPOS_AMBIENTE_SEM_PINTURA_PADRAO = {
    "garagem",
    "area externa",
    "área externa",
}


def _numero(valor, padrao=0.0):
    try:
        if valor is None:
            return padrao
        return float(valor)
    except (TypeError, ValueError):
        return padrao


def _texto(valor, padrao=""):
    if valor is None:
        return padrao
    return str(valor).strip()


def _booleano(valor, padrao=True):
    if valor is None:
        return padrao

    if isinstance(valor, bool):
        return valor

    texto = str(valor).strip().lower()

    if texto in ["sim", "s", "true", "1", "yes"]:
        return True

    if texto in ["nao", "não", "n", "false", "0", "no"]:
        return False

    return padrao


def _normalizar_chave(valor):
    return _texto(valor).lower()


def _obter_valor(dados, chaves, padrao=None):
    for chave in chaves:
        if chave in dados:
            return dados.get(chave)
    return padrao


def _normalizar_tipo_piso(tipo_piso):
    tipo = _normalizar_chave(tipo_piso)
    return PISOS_SERVICOS.get(tipo, _texto(tipo_piso))


def _normalizar_ambiente(ambiente):
    ambiente = ambiente or {}

    nome = _texto(_obter_valor(ambiente, ["nome", "Nome"], "Ambiente"))
    tipo = _texto(_obter_valor(ambiente, ["tipo", "Tipo"], ""))
    tipo_piso = _texto(_obter_valor(
        ambiente,
        ["tipo_piso", "tipo piso", "piso", "Piso", "Tipo Piso"],
        "Piso Porcelanato",
    ))

    possui_pintura_padrao = _normalizar_chave(tipo) not in TIPOS_AMBIENTE_SEM_PINTURA_PADRAO

    return {
        "nome": nome,
        "tipo": tipo,
        "area_piso": _numero(_obter_valor(
            ambiente,
            ["area_piso", "área piso", "area", "Área", "Area", "area_total"],
            0,
        )),
        "perimetro": _numero(_obter_valor(
            ambiente,
            ["perimetro", "perímetro", "Perímetro", "Perimetro"],
            0,
        )),
        "pe_direito": _numero(_obter_valor(
            ambiente,
            ["pe_direito", "pé direito", "pe direito", "Pé Direito"],
            2.8,
        ), 2.8),
        "tipo_piso": tipo_piso,
        "altura_revestimento": _numero(_obter_valor(
            ambiente,
            ["altura_revestimento", "altura revestimento", "Altura Revestimento"],
            0,
        )),
        "possui_pintura": _booleano(_obter_valor(
            ambiente,
            ["possui_pintura", "possui pintura", "Pintura"],
            possui_pintura_padrao,
        ), possui_pintura_padrao),
        "percentual_perdas": _numero(_obter_valor(
            ambiente,
            ["percentual_perdas", "perdas", "perda", "% perdas"],
            0,
        )),
    }


def normalizar_projeto(projeto):
    projeto = projeto or {}
    obra = projeto.get("obra", {}) or {}
    ambientes = projeto.get("ambientes", []) or []

    if isinstance(ambientes, dict):
        ambientes = [ambientes]

    return {
        "obra": {
            "nome": _texto(obra.get("nome", "")),
            "tipo": _texto(obra.get("tipo", "")),
            "area_total": _numero(obra.get("area_total", obra.get("area", 0))),
        },
        "ambientes": [
            _normalizar_ambiente(ambiente)
            for ambiente in ambientes
        ],
    }


def calcular_area_paredes(ambiente):
    perimetro = _numero(ambiente.get("perimetro", 0))
    pe_direito = _numero(ambiente.get("pe_direito", 0))

    return perimetro * pe_direito


def calcular_area_pintura_ambiente(ambiente):
    if not _booleano(ambiente.get("possui_pintura"), True):
        return 0

    area_paredes = calcular_area_paredes(ambiente)
    altura_revestimento = _numero(ambiente.get("altura_revestimento", 0))
    perimetro = _numero(ambiente.get("perimetro", 0))
    area_revestida = perimetro * altura_revestimento
    area_pintura = area_paredes - area_revestida

    return max(area_pintura, 0)


def calcular_pisos_ambiente(ambiente):
    area_piso = _numero(ambiente.get("area_piso", 0))
    percentual_perdas = _numero(ambiente.get("percentual_perdas", 0))
    tipo_piso = _normalizar_tipo_piso(ambiente.get("tipo_piso", "Piso Porcelanato"))

    if area_piso <= 0 or not tipo_piso:
        return {}

    quantidade = area_piso * (1 + percentual_perdas / 100)

    return {
        tipo_piso: quantidade,
    }


def calcular_revestimentos_ambiente(ambiente):
    perimetro = _numero(ambiente.get("perimetro", 0))
    altura_revestimento = _numero(ambiente.get("altura_revestimento", 0))
    percentual_perdas = _numero(ambiente.get("percentual_perdas", 0))

    if perimetro <= 0 or altura_revestimento <= 0:
        return {}

    area_revestimento = perimetro * altura_revestimento
    quantidade = area_revestimento * (1 + percentual_perdas / 100)

    return {
        SERVICO_REVESTIMENTO: quantidade,
    }


def _somar_quantitativos(destino, origem):
    for servico, quantidade in origem.items():
        destino[servico] = destino.get(servico, 0) + _numero(quantidade)

    return destino


def gerar_quantitativos_arquitetonicos(projeto):
    projeto_normalizado = normalizar_projeto(projeto)
    quantitativos = {}
    detalhamento = []

    for ambiente in projeto_normalizado["ambientes"]:
        pisos = calcular_pisos_ambiente(ambiente)
        revestimentos = calcular_revestimentos_ambiente(ambiente)
        pintura = calcular_area_pintura_ambiente(ambiente)

        _somar_quantitativos(quantitativos, pisos)
        _somar_quantitativos(quantitativos, revestimentos)

        if pintura > 0:
            quantitativos[SERVICO_PINTURA] = quantitativos.get(SERVICO_PINTURA, 0) + pintura

        detalhamento.append({
            "Ambiente": ambiente["nome"],
            "Tipo": ambiente["tipo"],
            "Área Piso": ambiente["area_piso"],
            "Perímetro": ambiente["perimetro"],
            "Pé Direito": ambiente["pe_direito"],
            "Tipo Piso": ambiente["tipo_piso"],
            "Altura Revestimento": ambiente["altura_revestimento"],
            "Percentual Perdas": ambiente["percentual_perdas"],
            "Área Paredes": calcular_area_paredes(ambiente),
            "Área Pintura": pintura,
            "Pisos": pisos,
            "Revestimentos": revestimentos,
        })

    return {
        "quantitativos": quantitativos,
        "detalhamento": pd.DataFrame(detalhamento),
        "projeto": projeto_normalizado,
    }