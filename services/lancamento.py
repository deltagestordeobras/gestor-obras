import uuid
import logging
from datetime import datetime

import pandas as pd
import streamlit as st
from database.connection import get_connection


def salvar_lancamento(dados):
    obra = str(dados.get("Obra") or "").strip()
    tipo = str(dados.get("Tipo") or "").strip()
    fornecedor = str(dados.get("Fornecedor") or "").strip()
    fornecedor_id = str(dados.get("FornecedorID") or "").strip()
    categoria = str(dados.get("Categoria") or "").strip()
    etapa = str(dados.get("Etapa") or "").strip()
    entrada_nota = dados.get("Entrada Nota")

    try:
        valor = float(dados.get("Valor", 0))
    except (TypeError, ValueError):
        return False, "Informe um valor maior que zero."

    if not obra:
        return False, "Informe a obra."

    if ("sa" in tipo.casefold() or valor < 0) and not (fornecedor or fornecedor_id):
        return False, "Informe o fornecedor."

    if abs(valor) <= 0:
        return False, "Informe um valor maior que zero."

    if entrada_nota is None or pd.isna(entrada_nota) or not str(entrada_nota).strip():
        return False, "Informe a data de entrada."

    if not categoria:
        return False, "Informe a categoria."

    if not etapa:
        return False, "Informe a etapa."

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO lancamentos (
                ID,
                Obra,
                Tipo,
                "Nº Nota",
                "Entrada Nota",
                "Data Vencimento",
                "Data Pagto",
                "Criado Em",
                "Pago Em",
                "Descrição",
                Categoria,
                Etapa,
                Valor,
                Status,
                Foto,
                Fornecedor,
                FornecedorID,
                StatusNota
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            dados.get("ID", str(uuid.uuid4())),
            obra,
            tipo,
            dados.get("Nº Nota", ""),
            str(dados.get("Entrada Nota", "")),
            str(dados.get("Data Vencimento", "")),
            str(dados.get("Data Pagto", "")),
            str(dados.get("Criado Em", "")),
            str(dados.get("Pago Em", "")),
            dados.get("Descrição", ""),
            categoria,
            etapa,
            valor,
            dados.get("Status", "Pendente"),
            dados.get("Foto", ""),
            fornecedor,
            fornecedor_id,
            "ABERTA"

        ))

        conn.commit()
        st.cache_data.clear()

        return True, "Lançamento salvo com sucesso."

    except Exception as e:

        logging.exception("Erro ao salvar lançamento.")
        return False, str(e)

    finally:

        conn.close()


@st.cache_data(ttl=15)
def carregar_lancamentos(obra):

    conn = get_connection()

    try:

        df = pd.read_sql(
            """
            SELECT *
            FROM lancamentos
            WHERE Obra = ?
            ORDER BY "Criado Em" DESC
            """,
            conn,
            params=(obra,)
        )

        return df

    except Exception as e:

        logging.exception("Erro ao carregar lançamentos da obra %s.", obra)
        return pd.DataFrame()

    finally:

        conn.close()


def atualizar_lancamento(id, dados):
    conn = get_connection()

    try:
        conn.execute("""
            UPDATE lancamentos
            SET "Descri??o" = ?, Categoria = ?, Valor = ?
            WHERE ID = ?
        """, (
            dados["Descricao"],
            dados["Categoria"],
            dados["Valor"],
            id
        ))

        conn.commit()
        st.cache_data.clear()
        return True, None
    except Exception as e:
        logging.exception("Erro ao atualizar lancamento %s.", id)
        return False, str(e)
    finally:
        conn.close()

def excluir_lancamento(id):
    conn = get_connection()

    try:
        conn.execute("DELETE FROM lancamentos WHERE ID = ?", (id,))

        conn.commit()
        st.cache_data.clear()
        return True, None
    except Exception as e:
        logging.exception("Erro ao excluir lancamento %s.", id)
        return False, str(e)
    finally:
        conn.close()

def dar_baixa_pagamento(id, data_pagto):
    conn = get_connection()

    try:
        conn.execute("""
            UPDATE lancamentos
            SET Status = ?, "Data Pagto" = ?, "Pago Em" = ?
            WHERE ID = ?
        """, (
            "Pago",
            str(data_pagto),
            datetime.now().isoformat(),
            id
        ))

        conn.commit()
        st.cache_data.clear()
        return True, None

    except Exception as e:
        logging.exception("Erro ao dar baixa no pagamento %s.", id)
        return False, str(e)

    finally:
        conn.close()

def dar_baixa_pagamentos(ids, data_pagto):
    ids = [str(lancamento_id) for lancamento_id in ids if lancamento_id]
    if not ids:
        return False, "Nenhum lan?amento selecionado."

    conn = get_connection()
    try:
        conn.executemany("""
            UPDATE lancamentos
            SET Status = ?, "Data Pagto" = ?, "Pago Em" = ?
            WHERE ID = ?
        """, [
            ("Pago", str(data_pagto), datetime.now().isoformat(), lancamento_id)
            for lancamento_id in ids
        ])
        conn.commit()
        st.cache_data.clear()
        return True, None
    except Exception as e:
        logging.exception("Erro ao dar baixa em pagamentos em lote.")
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def atualizar_campos_financeiros():
    conn = get_connection()
    try:
        c = conn.cursor()

        for campo in ("Frete", "Desconto", "Imposto"):
            try:
                c.execute(f'ALTER TABLE lancamentos ADD COLUMN {campo} REAL')
            except Exception:
                logging.debug(
                    "Campo financeiro %s ja existe ou nao pode ser criado.",
                    campo,
                    exc_info=True,
                )

        conn.commit()
        st.cache_data.clear()
        return True, None
    except Exception as e:
        logging.exception("Erro ao atualizar campos financeiros.")
        return False, str(e)
    finally:
        conn.close()

def marcar_como_pago(lancamento_id):

    conn = get_connection()

    try:
        conn.execute("""
            UPDATE lancamentos
            SET Status = 'Pago',
                "Data Pagto" = CURRENT_TIMESTAMP
            WHERE ID = ?
        """, (lancamento_id,))

        conn.commit()
        st.cache_data.clear()
        return True, None
    except Exception as e:
        logging.exception("Erro ao marcar lancamento como pago %s.", lancamento_id)
        return False, str(e)
    finally:
        conn.close()
