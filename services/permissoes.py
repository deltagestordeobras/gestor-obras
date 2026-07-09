import json

import streamlit as st


PERMISSOES_MODULOS = [
    "painel",
    "lancamentos",
    "materiais",
    "erp",
    "dashboard",
    "cronograma",
    "evolucao",
    "diario_obra",
    "relatorio_materiais",
    "produtos",
    "administracao",
    "consulta_pagamentos",
    "configuracoes",
    "orcamento",
    "fornecedores",
    "usuarios",
    "backup",
]

PERMISSOES_ADMIN = PERMISSOES_MODULOS.copy()


def normalizar_permissoes(permissoes):
    if permissoes is None:
        return []

    if isinstance(permissoes, list):
        return permissoes

    if isinstance(permissoes, dict):
        return permissoes

    if isinstance(permissoes, str):
        if not permissoes.strip():
            return []

        try:
            permissoes_carregadas = json.loads(permissoes)
        except json.JSONDecodeError:
            return []

        if isinstance(permissoes_carregadas, (list, dict)):
            return permissoes_carregadas

    return []


def permissoes_para_json(permissoes):
    return json.dumps(normalizar_permissoes(permissoes))


def permissoes_por_perfil(perfil, permissoes=None):
    if str(perfil).upper() == "ADMIN":
        return PERMISSOES_ADMIN.copy()

    return normalizar_permissoes(permissoes)


def tem_permissao(modulo, acao=None, permissoes=None):
    permissoes = normalizar_permissoes(
        st.session_state.get("permissoes", []) if permissoes is None else permissoes
    )

    if isinstance(permissoes, list):
        return modulo in permissoes

    if isinstance(permissoes, dict):
        if modulo not in permissoes:
            return False

        if acao is None:
            return True

        return acao in permissoes[modulo]

    return False
