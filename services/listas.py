from datetime import datetime
import uuid

import pandas as pd
import streamlit as st

from database.connection import get_connection


TIPO_ETAPA_OBRA = "etapa_obra"

ETAPAS_OBRA_INICIAIS = [
    "Fundação",
    "Estrutura",
    "Alvenaria",
    "Cobertura",
    "Instalações",
    "Acabamento",
    "Outros",
]


def garantir_listas_iniciais():
    conn = get_connection()
    agora = datetime.now().isoformat(timespec="seconds")
    for ordem, nome in enumerate(ETAPAS_OBRA_INICIAIS, start=1):
        conn.execute("""
            INSERT OR IGNORE INTO listas_sistema
                (ID, Tipo, Nome, Ativo, Ordem, CriadoEm)
            VALUES (?, ?, ?, 1, ?, ?)
        """, (str(uuid.uuid4()), TIPO_ETAPA_OBRA, nome, ordem, agora))
    conn.commit()
    st.cache_data.clear()
    conn.close()


def carregar_lista(tipo, somente_ativos=True):
    conn = get_connection()
    if somente_ativos:
        query = """
        SELECT ID, Tipo, Nome, Ativo, Ordem, CriadoEm
        FROM listas_sistema
        WHERE Tipo = ? AND Ativo = 1
        ORDER BY COALESCE(Ordem, 999999), Nome
        """
    else:
        query = """
        SELECT ID, Tipo, Nome, Ativo, Ordem, CriadoEm
        FROM listas_sistema
        WHERE Tipo = ?
        ORDER BY COALESCE(Ordem, 999999), Nome
        """
    df = pd.read_sql_query(
        query,
        conn,
        params=(tipo,),
    )
    conn.close()
    return df


def listar_nomes(tipo, somente_ativos=True, incluir=None):
    df = carregar_lista(tipo, somente_ativos)
    nomes = df["Nome"].dropna().astype(str).tolist() if not df.empty else []
    for nome in incluir or []:
        nome = str(nome or "").strip()
        if nome and nome not in nomes:
            nomes.append(nome)
    return nomes


def listar_etapas_ativas(incluir=None):
    return listar_nomes(TIPO_ETAPA_OBRA, True, incluir)


def adicionar_item(tipo, nome, ordem=None):
    nome = str(nome or "").strip()
    if not nome:
        return False, "Informe o nome."

    conn = get_connection()
    existente = conn.execute(
        "SELECT ID, Ativo FROM listas_sistema WHERE Tipo = ? AND lower(Nome) = lower(?)",
        (tipo, nome),
    ).fetchone()
    if existente:
        if int(existente["Ativo"] or 0) == 1:
            conn.close()
            return False, "Este item já existe."
        conn.execute(
            "UPDATE listas_sistema SET Ativo = 1, Nome = ? WHERE ID = ?",
            (nome, existente["ID"]),
        )
    else:
        if ordem is None:
            ordem = conn.execute(
                "SELECT COALESCE(MAX(Ordem), 0) + 1 FROM listas_sistema WHERE Tipo = ?",
                (tipo,),
            ).fetchone()[0]
        conn.execute("""
            INSERT INTO listas_sistema (ID, Tipo, Nome, Ativo, Ordem, CriadoEm)
            VALUES (?, ?, ?, 1, ?, ?)
        """, (
            str(uuid.uuid4()), tipo, nome, int(ordem),
            datetime.now().isoformat(timespec="seconds"),
        ))
    conn.commit()
    st.cache_data.clear()
    conn.close()
    return True, None


def renomear_item(item_id, novo_nome):
    novo_nome = str(novo_nome or "").strip()
    if not novo_nome:
        return False, "Informe o novo nome."

    conn = get_connection()
    item = conn.execute(
        "SELECT Tipo FROM listas_sistema WHERE ID = ?",
        (item_id,),
    ).fetchone()
    if not item:
        conn.close()
        return False, "Item não encontrado."

    duplicado = conn.execute(
        "SELECT 1 FROM listas_sistema WHERE Tipo = ? AND lower(Nome) = lower(?) AND ID <> ?",
        (item["Tipo"], novo_nome, item_id),
    ).fetchone()
    if duplicado:
        conn.close()
        return False, "Já existe um item com esse nome."

    conn.execute("UPDATE listas_sistema SET Nome = ? WHERE ID = ?", (novo_nome, item_id))
    conn.commit()
    st.cache_data.clear()
    conn.close()
    return True, None


def definir_item_ativo(item_id, ativo):
    conn = get_connection()
    conn.execute(
        "UPDATE listas_sistema SET Ativo = ? WHERE ID = ?",
        (1 if ativo else 0, item_id),
    )
    conn.commit()
    st.cache_data.clear()
    conn.close()
