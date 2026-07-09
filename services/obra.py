import uuid
import pandas as pd
from datetime import datetime
import re
import logging
import streamlit as st
from database.connection import get_connection


def normalizar_nome_obra(nome):
    if nome is None:
        return ""

    nome = re.sub(r"\s+", " ", str(nome).strip())
    return nome.upper()


def criar_obra(nome):
    nome_normalizado = normalizar_nome_obra(nome)
    if not nome_normalizado:
        return False, "Informe o nome da obra para continuar."

    conn = get_connection()

    try:
        obras = conn.execute("SELECT Nome FROM obras").fetchall()
        for obra in obras:
            nome_existente = obra["Nome"] if hasattr(obra, "keys") else obra[0]
            if normalizar_nome_obra(nome_existente) == nome_normalizado:
                return False, "Já existe uma obra cadastrada com esse nome."

        conn.execute("""
            INSERT INTO obras (ID, Nome, DataCriacao)
            VALUES (?, ?, ?)
        """, (str(uuid.uuid4()), nome_normalizado, str(datetime.now())))

        conn.commit()
        st.cache_data.clear()
        return True, None

    except Exception as e:
        logging.exception("Erro ao criar obra %s.", nome_normalizado)
        return False, str(e)

    finally:
        conn.close()



@st.cache_data(ttl=15)
def listar_obras():
    conn = get_connection()

    try:
        df = pd.read_sql("SELECT ID, Nome FROM obras ORDER BY Nome", conn)
        return df

    except Exception:
        logging.exception("Erro ao listar obras.")
        return pd.DataFrame(columns=["ID", "Nome"])

    finally:
        conn.close()




def buscar_nome_obra(obra_id):

    conn = get_connection()

    try:
        row = conn.execute("""
            SELECT Nome FROM obras WHERE ID = ?
        """, (obra_id,)).fetchone()

        if row:
            return row["Nome"] if hasattr(row, "keys") else row[0]

        return None

    except Exception:
        logging.exception("Erro ao buscar nome da obra %s.", obra_id)
        return None

    finally:
        conn.close()
