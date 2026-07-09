import math


ESPESSURA_LAJE_PADRAO_CM = 10.0
LARGURA_BALDRAME_PADRAO_CM = 14.0
ALTURA_BALDRAME_PADRAO_CM = 30.0

ACO_FUNDACAO_KG_M3 = 58.0
ACO_ESTRUTURA_KG_M3 = 90.0
ACO_LAJE_KG_M2 = 5.5
ACO_FALLBACK_TERREO_KG_M2 = 10.0
ACO_FALLBACK_SOBRADO_KG_M2 = 18.0
ACO_FALLBACK_TERREO_MIN_KG_M2 = 7.0
ACO_FALLBACK_TERREO_MAX_KG_M2 = 12.0


def _numero(valor, padrao=0.0):
    try:
        if valor is None:
            return padrao
        return float(valor)
    except (TypeError, ValueError):
        return padrao


def _normalizar_texto(valor):
    texto = str(valor or "").strip().lower()
    substituicoes = {
        "?": "a",
        "?": "a",
        "?": "a",
        "?": "a",
        "?": "e",
        "?": "e",
        "?": "i",
        "?": "o",
        "?": "o",
        "?": "o",
        "?": "u",
        "?": "c",
    }

    for original, novo in substituicoes.items():
        texto = texto.replace(original, novo)

    return texto


def calcular_vigas(comprimento=0, largura_cm=0, altura_cm=0):
    comprimento = _numero(comprimento)
    largura_m = _numero(largura_cm) / 100
    altura_m = _numero(altura_cm) / 100

    volume = comprimento * largura_m * altura_m

    return {
        "comprimento": comprimento,
        "volume": volume,
        "area_forma": comprimento,
    }


def calcular_pilares(comprimento=0, largura_cm=0, altura_cm=0):
    comprimento = _numero(comprimento)
    largura_m = _numero(largura_cm) / 100
    altura_m = _numero(altura_cm) / 100

    volume = comprimento * largura_m * altura_m

    return {
        "comprimento": comprimento,
        "volume": volume,
        "area_forma": comprimento,
    }


def calcular_baldrame(comprimento=0, largura_cm=0, altura_cm=0):
    comprimento = _numero(comprimento)

    if comprimento <= 0:
        return {
            "comprimento": 0.0,
            "volume": 0.0,
            "largura_cm": 0.0,
            "altura_cm": 0.0,
        }

    largura = _numero(largura_cm, LARGURA_BALDRAME_PADRAO_CM) or LARGURA_BALDRAME_PADRAO_CM
    altura = _numero(altura_cm, ALTURA_BALDRAME_PADRAO_CM) or ALTURA_BALDRAME_PADRAO_CM
    volume = comprimento * (largura / 100) * (altura / 100)

    return {
        "comprimento": comprimento,
        "volume": volume,
        "largura_cm": largura,
        "altura_cm": altura,
    }


def calcular_tubuloes(quantidade=0, diametro_cm=0, profundidade_m=0):
    quantidade = _numero(quantidade)
    raio_m = (_numero(diametro_cm) / 100) / 2
    profundidade_m = _numero(profundidade_m)

    volume_unitario = math.pi * (raio_m ** 2) * profundidade_m
    volume_total = quantidade * volume_unitario

    return {
        "quantidade": quantidade,
        "volume_unitario": volume_unitario,
        "volume": volume_total,
    }


def calcular_volume_piso(area_m2=0, espessura_cm=0):
    area_m2 = _numero(area_m2)
    espessura_m = _numero(espessura_cm) / 100

    return area_m2 * espessura_m


def calcular_volume_laje(area_laje=0, espessura_laje_cm=0, area_fallback=0, espessura_fallback_cm=0):
    area = _numero(area_laje) or _numero(area_fallback)

    if area <= 0:
        return 0.0

    espessura_cm = (
        _numero(espessura_laje_cm)
        or _numero(espessura_fallback_cm)
        or ESPESSURA_LAJE_PADRAO_CM
    )

    return area * (espessura_cm / 100)


def calcular_volume_fundacao(
    tipo_fundacao=None,
    area_total=0,
    area_piso=0,
    quantidade_tubuloes=0,
    diametro_tubulao_cm=0,
    profundidade_tubulao_m=0,
):
    tipo = _normalizar_texto(tipo_fundacao) or "sapata"
    area_referencia = _numero(area_piso) or _numero(area_total)

    if tipo == "tubulao":
        tubuloes = calcular_tubuloes(
            quantidade=quantidade_tubuloes,
            diametro_cm=diametro_tubulao_cm,
            profundidade_m=profundidade_tubulao_m,
        )

        if tubuloes["volume"] > 0:
            return tubuloes["volume"]

        return area_referencia * 0.035

    if area_referencia <= 0:
        return 0.0

    if tipo == "radier":
        return area_referencia * 0.12

    if tipo == "bloco":
        return area_referencia * 0.035

    return area_referencia * 0.04


def _aplicar_override_volume(volumes, volume_estimado_concreto=0):
    volume_estimado = _numero(volume_estimado_concreto)

    if volume_estimado <= 0:
        return volumes

    total_calculado = sum(volumes.values())

    if total_calculado <= 0:
        return {
            "fundacao": volume_estimado * 0.30,
            "baldrame": volume_estimado * 0.15,
            "vigas": volume_estimado * 0.20,
            "pilares": volume_estimado * 0.10,
            "laje": volume_estimado * 0.25,
        }

    fator = volume_estimado / total_calculado

    return {
        chave: volume * fator
        for chave, volume in volumes.items()
    }


def calcular_armacao_automatica(volumes_concreto, area_laje=0):
    volume_fundacao = _numero(volumes_concreto.get("fundacao", 0))
    volume_baldrame = _numero(volumes_concreto.get("baldrame", 0))
    volume_vigas = _numero(volumes_concreto.get("vigas", 0))
    volume_pilares = _numero(volumes_concreto.get("pilares", 0))
    area_laje = _numero(area_laje)

    aco_fundacao = (volume_fundacao + volume_baldrame) * ACO_FUNDACAO_KG_M3
    aco_estrutura = (volume_vigas + volume_pilares) * ACO_ESTRUTURA_KG_M3
    aco_laje = area_laje * ACO_LAJE_KG_M2

    return aco_fundacao + aco_estrutura + aco_laje

def calcular_armacao_fallback_area(area_construida=0, pavimentos=1):
    area = _numero(area_construida)

    if area <= 0:
        return 0.0

    pavimentos = _numero(pavimentos, 1) or 1

    if pavimentos > 1:
        return area * ACO_FALLBACK_SOBRADO_KG_M2

    coeficiente = min(
        max(ACO_FALLBACK_TERREO_KG_M2, ACO_FALLBACK_TERREO_MIN_KG_M2),
        ACO_FALLBACK_TERREO_MAX_KG_M2,
    )

    return area * coeficiente


def possui_dados_estruturais_completos(
    area_laje=0,
    espessura_laje_cm=0,
    comprimento_viga=0,
    largura_viga_cm=0,
    altura_viga_cm=0,
    comprimento_pilar=0,
    largura_pilar_cm=0,
    altura_pilar_cm=0,
    volume_estimado_concreto=0,
    comprimento_baldrame=0,
    largura_baldrame_cm=0,
    altura_baldrame_cm=0,
    quantidade_tubuloes=0,
    diametro_tubulao_cm=0,
    profundidade_tubulao_m=0,
):
    if _numero(volume_estimado_concreto) > 0:
        return True

    tem_vigas = (
        _numero(comprimento_viga) > 0
        and _numero(largura_viga_cm) > 0
        and _numero(altura_viga_cm) > 0
    )
    tem_pilares = (
        _numero(comprimento_pilar) > 0
        and _numero(largura_pilar_cm) > 0
        and _numero(altura_pilar_cm) > 0
    )
    tem_laje = _numero(area_laje) > 0 and _numero(espessura_laje_cm) > 0
    tem_baldrame_detalhado = (
        _numero(comprimento_baldrame) > 0
        and _numero(largura_baldrame_cm) > 0
        and _numero(altura_baldrame_cm) > 0
    )
    tem_tubuloes = (
        _numero(quantidade_tubuloes) > 0
        and _numero(diametro_tubulao_cm) > 0
        and _numero(profundidade_tubulao_m) > 0
    )

    return tem_vigas or tem_pilares or tem_laje or tem_baldrame_detalhado or tem_tubuloes


def calcular_volume_concreto(
    area_total=0,
    area_piso=0,
    espessura_piso_cm=0,
    area_laje=0,
    espessura_laje_cm=0,
    comprimento_viga=0,
    largura_viga_cm=0,
    altura_viga_cm=0,
    comprimento_pilar=0,
    largura_pilar_cm=0,
    altura_pilar_cm=0,
    tipo_fundacao=None,
    volume_estimado_concreto=0,
    comprimento_baldrame=0,
    largura_baldrame_cm=0,
    altura_baldrame_cm=0,
    quantidade_tubuloes=0,
    diametro_tubulao_cm=0,
    profundidade_tubulao_m=0,
):
    volume_piso = calcular_volume_piso(area_piso, espessura_piso_cm)
    volume_fundacao = calcular_volume_fundacao(
        tipo_fundacao=tipo_fundacao,
        area_total=area_total,
        area_piso=area_piso,
        quantidade_tubuloes=quantidade_tubuloes,
        diametro_tubulao_cm=diametro_tubulao_cm,
        profundidade_tubulao_m=profundidade_tubulao_m,
    )

    vigas = calcular_vigas(
        comprimento=comprimento_viga,
        largura_cm=largura_viga_cm,
        altura_cm=altura_viga_cm,
    )

    pilares = calcular_pilares(
        comprimento=comprimento_pilar,
        largura_cm=largura_pilar_cm,
        altura_cm=altura_pilar_cm,
    )

    baldrame = calcular_baldrame(
        comprimento=comprimento_baldrame,
        largura_cm=largura_baldrame_cm,
        altura_cm=altura_baldrame_cm,
    )

    volume_laje = calcular_volume_laje(
        area_laje=area_laje,
        espessura_laje_cm=espessura_laje_cm,
        area_fallback=area_piso,
        espessura_fallback_cm=espessura_piso_cm,
    )

    volumes = _aplicar_override_volume(
        {
            "fundacao": volume_fundacao,
            "baldrame": baldrame["volume"],
            "vigas": vigas["volume"],
            "pilares": pilares["volume"],
            "laje": volume_laje,
        },
        volume_estimado_concreto=volume_estimado_concreto,
    )

    return {
        "piso": volume_piso,
        "fundacao": volumes["fundacao"],
        "baldrame": volumes["baldrame"],
        "vigas": volumes["vigas"],
        "pilares": volumes["pilares"],
        "laje": volumes["laje"],
        "total": sum(volumes.values()),
    }


def calcular_formas(comprimento_viga=0, comprimento_pilar=0):
    return _numero(comprimento_viga) + _numero(comprimento_pilar)


def calcular_pintura(area_total=0, fator=2):
    return _numero(area_total) * _numero(fator, 2)


def calcular_revestimento(area_total=0, fator=2):
    return _numero(area_total) * _numero(fator, 2)


def calcular_eletrica(area_total=0):
    return _numero(area_total)


def calcular_hidraulica(area_total=0):
    return _numero(area_total)


def calcular_piso(area_piso=0):
    return _numero(area_piso)


def calcular_cobertura(area_cobertura=0, tipo_cobertura=None):
    mapa = {
        "Cer?mica": "Cobertura Cer?mica",
        "Met?lica Simples": "Cobertura Met?lica",
        "Telha Sandu?che": "Cobertura Sandu?che",
    }

    servico = mapa.get(tipo_cobertura)

    if not servico:
        return {}

    area = _numero(area_cobertura)

    if area <= 0:
        return {}

    return {servico: area}


def normalizar_quantitativos(*quantitativos):
    normalizado = {}

    for grupo in quantitativos:
        if not grupo:
            continue

        for servico, quantidade in grupo.items():
            quantidade = _numero(quantidade)

            if quantidade <= 0:
                continue

            normalizado[servico] = normalizado.get(servico, 0) + quantidade

    return normalizado


def calcular_quantitativos_automaticos(
    area_total=0,
    area_piso=0,
    espessura_piso_cm=0,
    area_laje=0,
    espessura_laje_cm=0,
    comprimento_viga=0,
    largura_viga_cm=0,
    altura_viga_cm=0,
    comprimento_pilar=0,
    largura_pilar_cm=0,
    altura_pilar_cm=0,
    tipo_fundacao=None,
    volume_estimado_concreto=0,
    comprimento_baldrame=0,
    largura_baldrame_cm=0,
    altura_baldrame_cm=0,
    quantidade_tubuloes=0,
    diametro_tubulao_cm=0,
    profundidade_tubulao_m=0,
    area_cobertura=0,
    tipo_cobertura=None,
    incluir_piso_porcelanato=True,
    pavimentos=1,
):
    volume_concreto = calcular_volume_concreto(
        area_total=area_total,
        area_piso=area_piso,
        espessura_piso_cm=espessura_piso_cm,
        area_laje=area_laje,
        espessura_laje_cm=espessura_laje_cm,
        comprimento_viga=comprimento_viga,
        largura_viga_cm=largura_viga_cm,
        altura_viga_cm=altura_viga_cm,
        comprimento_pilar=comprimento_pilar,
        largura_pilar_cm=largura_pilar_cm,
        altura_pilar_cm=altura_pilar_cm,
        tipo_fundacao=tipo_fundacao,
        volume_estimado_concreto=volume_estimado_concreto,
        comprimento_baldrame=comprimento_baldrame,
        largura_baldrame_cm=largura_baldrame_cm,
        altura_baldrame_cm=altura_baldrame_cm,
        quantidade_tubuloes=quantidade_tubuloes,
        diametro_tubulao_cm=diametro_tubulao_cm,
        profundidade_tubulao_m=profundidade_tubulao_m,
    )
    estrutura_detalhada = possui_dados_estruturais_completos(
        area_laje=area_laje,
        espessura_laje_cm=espessura_laje_cm,
        comprimento_viga=comprimento_viga,
        largura_viga_cm=largura_viga_cm,
        altura_viga_cm=altura_viga_cm,
        comprimento_pilar=comprimento_pilar,
        largura_pilar_cm=largura_pilar_cm,
        altura_pilar_cm=altura_pilar_cm,
        volume_estimado_concreto=volume_estimado_concreto,
        comprimento_baldrame=comprimento_baldrame,
        largura_baldrame_cm=largura_baldrame_cm,
        altura_baldrame_cm=altura_baldrame_cm,
        quantidade_tubuloes=quantidade_tubuloes,
        diametro_tubulao_cm=diametro_tubulao_cm,
        profundidade_tubulao_m=profundidade_tubulao_m,
    )

    area_base = _numero(area_total) or _numero(area_piso)

    if estrutura_detalhada:
        armacao_calculada = calcular_armacao_automatica(
            volume_concreto,
            _numero(area_laje)
        )

        # trava técnica residencial
        # casa térrea completa: 13 a 16 kg/m²
        if _numero(pavimentos, 1) <= 1 and area_base > 0:
            armacao_minima = area_base * 13.0
            armacao_maxima = area_base * 16.0
            armacao = max(armacao_calculada, armacao_minima)
            armacao = min(armacao, armacao_maxima)
        else:
            armacao = armacao_calculada
    else:
        armacao = calcular_armacao_fallback_area(
            area_construida=area_base,
            pavimentos=pavimentos,
        )

    quantitativos = {
        "Concreto": volume_concreto["total"],
        "Armação": armacao,
        "Forma Pilares e Vigas": calcular_formas(comprimento_viga, comprimento_pilar),
        "Furo Funda??o": _numero(quantidade_tubuloes),
        "Pintura": calcular_pintura(area_total),
        "Instala??o El?trica": calcular_eletrica(area_total),
        "Instala??o Hidr?ulica": calcular_hidraulica(area_total),
        "Revestimento": calcular_revestimento(area_total),
    }

    if incluir_piso_porcelanato:
        quantitativos["Piso Porcelanato"] = calcular_piso(area_piso)

    quantitativos = normalizar_quantitativos(
        quantitativos,
        calcular_cobertura(area_cobertura, tipo_cobertura),
    )

    return quantitativos

