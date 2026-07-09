import re
import uuid
import logging

import pandas as pd
import streamlit as st

from database.connection import get_connection
from services.lancamento import carregar_lancamentos
from services.status import STATUS_PAGO, STATUS_PENDENTE, serie_status_normalizado


COLUNAS_FORNECEDOR = [
    "ID", "Nome", "Rua", "Numero", "Bairro", "Cidade", "CEP",
    "Telefone", "Documento", "ChavePix", "Ativo",
]


def normalizar_nome_fornecedor(valor):
    return " ".join(str(valor or "").split()).casefold()


def normalizar_documento_fornecedor(valor):
    return re.sub(r"\D", "", str(valor or ""))


@st.cache_data(ttl=15)
def carregar_fornecedores(apenas_ativos=False):
    conn = get_connection()
    try:
        where = "WHERE COALESCE(Ativo, 1) = 1" if apenas_ativos else ""
        return pd.read_sql_query(
            f"SELECT {', '.join(COLUNAS_FORNECEDOR)} FROM fornecedores {where} ORDER BY Nome",
            conn,
        )
    except Exception as e:
        logging.exception("Erro ao carregar fornecedores.")
        return pd.DataFrame(columns=COLUNAS_FORNECEDOR)
    finally:
        conn.close()


def obter_fornecedor(fornecedor_id):
    conn = get_connection()
    try:
        linha = conn.execute(
            f"SELECT {', '.join(COLUNAS_FORNECEDOR)} FROM fornecedores WHERE ID = ?",
            (str(fornecedor_id),),
        ).fetchone()
        return dict(linha) if linha else None
    except Exception:
        logging.exception("Erro ao obter fornecedor %s.", fornecedor_id)
        return None
    finally:
        conn.close()


def salvar_fornecedor(dados):
    fornecedor_id = str(dados.get("ID") or uuid.uuid4())
    registro = {
        coluna: str(dados.get(coluna) or "").strip()
        for coluna in COLUNAS_FORNECEDOR
        if coluna not in {"ID", "Ativo"}
    }
    registro["Nome"] = " ".join(registro["Nome"].split())
    registro["Ativo"] = 1 if dados.get("Ativo", 1) else 0
    if not registro["Nome"]:
        return False, "Informe o nome do fornecedor.", fornecedor_id

    conn = get_connection()
    try:
        fornecedores_existentes = conn.execute(
            "SELECT ID, Nome, Documento FROM fornecedores WHERE ID <> ?",
            (fornecedor_id,),
        ).fetchall()
        for fornecedor in fornecedores_existentes:
            nome_existente = fornecedor["Nome"] if hasattr(fornecedor, "keys") else fornecedor[1]
            if normalizar_nome_fornecedor(nome_existente) == normalizar_nome_fornecedor(registro["Nome"]):
                return False, "Já existe um fornecedor cadastrado com esse nome.", fornecedor_id

            documento_existente = fornecedor["Documento"] if hasattr(fornecedor, "keys") else fornecedor[2]
            if registro["Documento"] and normalizar_documento_fornecedor(documento_existente) == registro["Documento"]:
                return False, "Já existe um fornecedor cadastrado com esse documento.", fornecedor_id

        existente = conn.execute(
            "SELECT ID FROM fornecedores WHERE ID = ?", (fornecedor_id,)
        ).fetchone()
        if existente:
            conn.execute("""
                UPDATE fornecedores SET
                    Nome=?, Rua=?, Numero=?, Bairro=?, Cidade=?, CEP=?,
                    Telefone=?, Documento=?, ChavePix=?, Ativo=?
                WHERE ID=?
            """, tuple(registro[coluna] for coluna in COLUNAS_FORNECEDOR[1:]) + (fornecedor_id,))
        else:
            conn.execute("""
                INSERT INTO fornecedores
                    (ID, Nome, Rua, Numero, Bairro, Cidade, CEP, Telefone, Documento, ChavePix, Ativo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (fornecedor_id,) + tuple(registro[coluna] for coluna in COLUNAS_FORNECEDOR[1:]))
        conn.commit()
        st.cache_data.clear()
        return True, None, fornecedor_id
    except Exception as erro:
        logging.exception("Erro ao salvar fornecedor %s.", registro.get("Nome"))
        conn.rollback()
        return False, str(erro), fornecedor_id
    finally:
        conn.close()


def definir_fornecedor_ativo(fornecedor_id, ativo):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE fornecedores SET Ativo = ? WHERE ID = ?",
            (1 if ativo else 0, str(fornecedor_id)),
        )
        conn.commit()
        st.cache_data.clear()
        return True, None
    except Exception as erro:
        logging.exception("Erro ao definir status do fornecedor %s.", fornecedor_id)
        return False, str(erro)
    finally:
        conn.close()


def resolver_fornecedores_lancamentos(df):
    if df is None or df.empty:
        return pd.DataFrame()

    resultado = df.copy()
    fornecedor = resultado.get("Fornecedor", pd.Series("", index=resultado.index))
    descricao = resultado.get("Descrição", pd.Series("", index=resultado.index))
    fornecedor = fornecedor.fillna("").astype(str).str.strip()
    descricao = descricao.fillna("").astype(str).str.strip()
    resultado["FornecedorEfetivo"] = fornecedor.mask(fornecedor == "", descricao)
    if "FornecedorID" in resultado.columns:
        conn = get_connection()
        try:
            mapa_ids = {
                str(linha["ID"]): str(linha["Nome"])
                for linha in conn.execute("SELECT ID, Nome FROM fornecedores").fetchall()
            }
        except Exception:
            logging.exception("Erro ao resolver fornecedores por ID.")
            mapa_ids = {}
        finally:
            conn.close()
        nomes_por_id = resultado["FornecedorID"].fillna("").astype(str).map(mapa_ids)
        resultado["FornecedorEfetivo"] = nomes_por_id.fillna(resultado["FornecedorEfetivo"])
        resultado["Fornecedor"] = resultado["FornecedorEfetivo"]
    resultado["FornecedorChave"] = resultado["FornecedorEfetivo"].apply(normalizar_nome_fornecedor)
    resultado["Valor"] = pd.to_numeric(resultado.get("Valor"), errors="coerce").fillna(0)
    resultado["StatusNormalizado"] = serie_status_normalizado(
        resultado.get("Status", pd.Series("", index=resultado.index))
    )
    resultado["Entrada Nota"] = pd.to_datetime(resultado.get("Entrada Nota"), errors="coerce")
    resultado["Data Pagto"] = pd.to_datetime(resultado.get("Data Pagto"), errors="coerce")
    resultado["Data Vencimento"] = pd.to_datetime(resultado.get("Data Vencimento"), errors="coerce")
    return resultado


def preparar_lancamentos_fornecedores(obra):
    return resolver_fornecedores_lancamentos(carregar_lancamentos(obra))


def preparar_lancamentos_fornecedores_df(df):
    return resolver_fornecedores_lancamentos(df)


def filtrar_lancamentos_fornecedor(df, nome, fornecedor_id=None):
    if df is None or df.empty:
        return pd.DataFrame()
    por_nome = df["FornecedorChave"] == normalizar_nome_fornecedor(nome)
    if fornecedor_id and "FornecedorID" in df.columns:
        por_id = df["FornecedorID"].fillna("").astype(str) == str(fornecedor_id)
        return df[por_id | por_nome].copy()
    return df[por_nome].copy()


def buscar_fornecedores(df, termo):
    if df is None or df.empty or not str(termo or "").strip():
        return df
    chave = re.sub(r"\s+", " ", str(termo)).strip().casefold()
    mascara = pd.Series(False, index=df.index)
    for coluna in ["Nome", "Documento", "Telefone", "ChavePix"]:
        if coluna in df.columns:
            mascara |= df[coluna].fillna("").astype(str).str.casefold().str.contains(
                re.escape(chave), regex=True
            )
    return df[mascara]


def ranking_fornecedores(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["Fornecedor", "Total negociado", "Quantidade de notas"])
    despesas = df[df["Valor"] < 0].copy()
    if despesas.empty:
        return pd.DataFrame(columns=["Fornecedor", "Total negociado", "Quantidade de notas"])
    resumo = despesas.groupby("FornecedorChave", dropna=False).agg(
        Fornecedor=("FornecedorEfetivo", "first"),
        **{"Total negociado": ("Valor", lambda valores: valores.abs().sum())},
        **{"Quantidade de notas": ("ID", "size")},
    ).reset_index(drop=True)
    return resumo.sort_values("Total negociado", ascending=False).reset_index(drop=True)


def situacao_financeira_fornecedores(df):
    colunas = [
        "Fornecedor", "Total pago", "Total pendente", "Total vencido",
        "Quantidade de notas", "Quantidade pagas", "Quantidade pendentes",
    ]
    if df is None or df.empty:
        return pd.DataFrame(columns=colunas)

    despesas = df[df["Valor"] < 0].copy()
    if despesas.empty:
        return pd.DataFrame(columns=colunas)
    hoje = pd.Timestamp.today().normalize()
    linhas = []
    for _, grupo in despesas.groupby("FornecedorChave", dropna=False):
        pagos = grupo["StatusNormalizado"] == STATUS_PAGO
        pendentes = grupo["StatusNormalizado"] == STATUS_PENDENTE
        vencidos = pendentes & grupo["Data Vencimento"].notna() & (grupo["Data Vencimento"] < hoje)
        linhas.append({
            "Fornecedor": grupo["FornecedorEfetivo"].iloc[0] or "Sem fornecedor",
            "Total pago": grupo.loc[pagos, "Valor"].abs().sum(),
            "Total pendente": grupo.loc[pendentes, "Valor"].abs().sum(),
            "Total vencido": grupo.loc[vencidos, "Valor"].abs().sum(),
            "Quantidade de notas": len(grupo),
            "Quantidade pagas": int(pagos.sum()),
            "Quantidade pendentes": int(pendentes.sum()),
        })
    return pd.DataFrame(linhas, columns=colunas).sort_values(
        "Total pendente", ascending=False
    ).reset_index(drop=True)
