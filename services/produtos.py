from datetime import datetime
import re
import uuid

import pandas as pd
import streamlit as st

from database.connection import get_connection


def normalizar_nome_produto(nome):
    return re.sub(r"\s+", " ", str(nome or "").strip()).upper()


def carregar_produtos(somente_ativos=True):
    conn = get_connection()
    filtro = "WHERE Ativo = 1" if somente_ativos else ""
    df = pd.read_sql_query(
        f"""
        SELECT ID, Nome, Unidade, Categoria, Ativo, CriadoEm
        FROM produtos
        {filtro}
        ORDER BY Nome
        """,
        conn,
    )
    conn.close()
    return df


def listar_nomes_produtos(somente_ativos=True, incluir=None):
    df = carregar_produtos(somente_ativos)
    nomes = df["Nome"].dropna().astype(str).tolist() if not df.empty else []
    for nome in incluir or []:
        nome = normalizar_nome_produto(nome)
        if nome and nome not in nomes:
            nomes.append(nome)
    return nomes


def obter_produto_por_nome(nome, incluir_inativo=True):
    nome = normalizar_nome_produto(nome)
    if not nome:
        return None
    conn = get_connection()
    filtro = "" if incluir_inativo else "AND Ativo = 1"
    linha = conn.execute(
        f"SELECT * FROM produtos WHERE Nome = ? COLLATE NOCASE {filtro}",
        (nome,),
    ).fetchone()
    conn.close()
    return dict(linha) if linha else None


def obter_ou_criar_produto(nome, unidade="", categoria=""):
    nome = normalizar_nome_produto(nome)
    if not nome:
        raise ValueError("Informe o nome do produto.")

    conn = get_connection()
    existente = conn.execute(
        "SELECT * FROM produtos WHERE Nome = ? COLLATE NOCASE",
        (nome,),
    ).fetchone()
    if existente:
        conn.close()
        return dict(existente), False

    produto_id = str(uuid.uuid4())
    conn.execute("""
        INSERT INTO produtos (ID, Nome, Unidade, Categoria, Ativo, CriadoEm)
        VALUES (?, ?, ?, ?, 1, ?)
    """, (
        produto_id,
        nome,
        re.sub(r"\s+", " ", str(unidade or "").strip()),
        re.sub(r"\s+", " ", str(categoria or "").strip()),
        datetime.now().isoformat(timespec="seconds"),
    ))
    conn.commit()
    st.cache_data.clear()
    linha = conn.execute("SELECT * FROM produtos WHERE ID = ?", (produto_id,)).fetchone()
    conn.close()
    return dict(linha), True


def salvar_produto(nome, unidade="", categoria=""):
    try:
        produto, criado = obter_ou_criar_produto(nome, unidade, categoria)
        if not criado:
            return False, "Produto já cadastrado."
        return True, produto["ID"]
    except Exception as erro:
        return False, str(erro)


def atualizar_produto(produto_id, nome, unidade="", categoria="", ativo=True):
    nome = normalizar_nome_produto(nome)
    if not nome:
        return False, "Informe o nome do produto."

    conn = get_connection()
    duplicado = conn.execute(
        "SELECT 1 FROM produtos WHERE Nome = ? COLLATE NOCASE AND ID <> ?",
        (nome, produto_id),
    ).fetchone()
    if duplicado:
        conn.close()
        return False, "Já existe um produto com esse nome."

    conn.execute("""
        UPDATE produtos
        SET Nome = ?, Unidade = ?, Categoria = ?, Ativo = ?
        WHERE ID = ?
    """, (
        nome,
        re.sub(r"\s+", " ", str(unidade or "").strip()),
        re.sub(r"\s+", " ", str(categoria or "").strip()),
        1 if ativo else 0,
        produto_id,
    ))
    conn.commit()
    st.cache_data.clear()
    conn.close()
    return True, None


def definir_produto_ativo(produto_id, ativo):
    conn = get_connection()
    conn.execute("UPDATE produtos SET Ativo = ? WHERE ID = ?", (1 if ativo else 0, produto_id))
    conn.commit()
    st.cache_data.clear()
    conn.close()


def migrar_insumos_para_produtos():
    conn = get_connection()
    if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] > 0:
        conn.close()
        return
    try:
        nomes = conn.execute(
            "SELECT DISTINCT Material FROM insumos WHERE Material IS NOT NULL AND trim(Material) <> ''"
        ).fetchall()
    except Exception:
        conn.close()
        return
    conn.close()

    for linha in nomes:
        obter_ou_criar_produto(linha["Material"])
