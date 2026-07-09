from datetime import datetime
import uuid

import pandas as pd
import streamlit as st

from database.connection import get_connection
from services.cronograma import atualizar_progresso_etapa
from services.evolucao import (
    contar_fotos_diario,
    excluir_evolucao_por_diario,
    salvar_evolucao,
)


COLUNAS_DIARIO = [
    "ID", "ObraID", "Obra", "Data", "Etapa", "Clima", "Responsavel",
    "Equipe", "ServicosExecutados", "Ocorrencias", "Observacoes",
    "ProgressoEtapa", "AtualizarCronograma", "CriarEvolucao",
    "CriadoEm", "AtualizadoEm",
]


def carregar_diarios(obra_id, data_inicio=None, data_fim=None):
    conn = get_connection()
    condicoes = ["ObraID = ?"]
    parametros = [str(obra_id)]
    if data_inicio:
        condicoes.append("date(Data) >= date(?)")
        parametros.append(pd.Timestamp(data_inicio).date().isoformat())
    if data_fim:
        condicoes.append("date(Data) <= date(?)")
        parametros.append(pd.Timestamp(data_fim).date().isoformat())
    df = pd.read_sql_query(
        f"""
        SELECT *
        FROM diario_obra
        WHERE {" AND ".join(condicoes)}
        ORDER BY date(Data) DESC, AtualizadoEm DESC
        """,
        conn,
        params=parametros,
    )
    conn.close()
    if not df.empty:
        df["QuantidadeFotos"] = df["ID"].apply(contar_fotos_diario)
    return df


def obter_diario(diario_id, obra_id):
    conn = get_connection()
    linha = conn.execute(
        "SELECT * FROM diario_obra WHERE ID = ? AND ObraID = ?",
        (str(diario_id), str(obra_id)),
    ).fetchone()
    conn.close()
    return dict(linha) if linha else None


def salvar_diario(dados, fotos=None):
    agora = datetime.now().isoformat(timespec="microseconds")
    diario_id = dados.get("ID") or str(uuid.uuid4())
    registro = {
        **dados,
        "ID": diario_id,
        "ObraID": str(dados.get("ObraID") or ""),
        "Data": pd.Timestamp(dados.get("Data")).date().isoformat(),
        "ProgressoEtapa": min(100.0, max(0.0, float(dados.get("ProgressoEtapa") or 0))),
        "AtualizarCronograma": 1 if dados.get("AtualizarCronograma") else 0,
        "CriarEvolucao": 1 if dados.get("CriarEvolucao") else 0,
        "AtualizadoEm": agora,
    }

    conn = get_connection()
    existente = conn.execute("SELECT CriadoEm FROM diario_obra WHERE ID = ?", (diario_id,)).fetchone()
    registro["CriadoEm"] = existente["CriadoEm"] if existente else agora
    if existente:
        conn.execute("""
            UPDATE diario_obra SET
                ObraID=?, Obra=?, Data=?, Etapa=?, Clima=?, Responsavel=?, Equipe=?,
                ServicosExecutados=?, Ocorrencias=?, Observacoes=?, ProgressoEtapa=?,
                AtualizarCronograma=?, CriarEvolucao=?, AtualizadoEm=?
            WHERE ID=?
        """, tuple(registro.get(c) for c in COLUNAS_DIARIO[1:14]) + (registro["AtualizadoEm"], diario_id))
    else:
        conn.execute(
            f"INSERT INTO diario_obra ({', '.join(COLUNAS_DIARIO)}) VALUES ({', '.join(['?'] * len(COLUNAS_DIARIO))})",
            tuple(registro.get(c) for c in COLUNAS_DIARIO),
        )
    conn.commit()
    st.cache_data.clear()
    conn.close()

    avisos = []
    if registro["AtualizarCronograma"]:
        atualizado = atualizar_progresso_etapa(
            registro["ObraID"], registro.get("Obra"), registro.get("Etapa"),
            registro["ProgressoEtapa"],
        )
        if not atualizado:
            avisos.append("Esta etapa ainda não existe no cronograma. O diário foi salvo sem atualizar o cronograma.")

    if registro["CriarEvolucao"] and fotos:
        descricao = "\n\n".join(
            texto for texto in [
                str(registro.get("ServicosExecutados") or "").strip(),
                str(registro.get("Observacoes") or "").strip(),
            ] if texto
        )
        ok, erro = salvar_evolucao(
            registro["ObraID"], registro.get("Obra"), registro.get("Etapa"),
            registro["Data"], f"Diário de Obra - {pd.Timestamp(registro['Data']).strftime('%d/%m/%Y')}",
            descricao, registro.get("Responsavel"), fotos,
            origem="Diário de Obra", diario_id=diario_id,
        )
        if not ok:
            avisos.append(f"Diário salvo, mas as fotos não foram publicadas: {erro}")
    return True, avisos, diario_id


def excluir_diario(diario_id, obra_id, remover_fotos=False):
    if remover_fotos:
        excluir_evolucao_por_diario(obra_id, diario_id)
    conn = get_connection()
    conn.execute(
        "DELETE FROM diario_obra WHERE ID = ? AND ObraID = ?",
        (str(diario_id), str(obra_id)),
    )
    conn.commit()
    st.cache_data.clear()
    conn.close()


def ultimo_diario(obra_id):
    conn = get_connection()
    linha = conn.execute("""
        SELECT *
        FROM diario_obra
        WHERE ObraID = ?
        ORDER BY date(Data) DESC, AtualizadoEm DESC
        LIMIT 1
    """, (str(obra_id),)).fetchone()
    conn.close()
    return dict(linha) if linha else None
