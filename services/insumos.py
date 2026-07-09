import uuid
import pandas as pd
import logging
from datetime import datetime
import streamlit as st
from database.connection import get_connection
from services.produtos import normalizar_nome_produto, obter_ou_criar_produto


def salvar_insumo(dados):
    conn = get_connection()

    try:
        material = normalizar_nome_produto(dados.get("Material"))
        if not material:
            return False, "Informe o material."
        produto, _ = obter_ou_criar_produto(
            material,
            dados.get("Unidade", ""),
            dados.get("CategoriaProduto", ""),
        )
        if not int(produto.get("Ativo", 0)):
            return False, "Produto inativo. Reative-o no cadastro mestre antes de lançar."
        quantidade = float(dados.get("Quantidade", 0))
        valor_unit = float(dados.get("ValorUnitario", 0))
        valor_total = quantidade * valor_unit

        insumo_id = str(uuid.uuid4())

        # ===============================
        # SALVA INSUMO
        # ===============================
        conn.execute("""
            INSERT INTO insumos (
                ID, Obra, Etapa, Material,
                Quantidade, ValorUnitario, ValorTotal, Data, NotaID
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            insumo_id,
            dados.get("Obra"),
            dados.get("Etapa"),
            material,
            quantidade,
            valor_unit,
            valor_total,
            datetime.now().isoformat(),
            dados.get("NotaID")
        ))

        # ===============================
        # 🔒 LOG DE AUDITORIA
        # ===============================
        conn.execute("""
            INSERT INTO historico_insumos (
                ID, InsumoID, Acao, ValorAntes, ValorDepois, Usuario, Data
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            insumo_id,
            "CRIACAO",
            0,
            valor_total,
            dados.get("Usuario", "admin"),
            datetime.now().isoformat()
        ))

        conn.commit()
        st.cache_data.clear()
        return True, None

    except Exception as e:
        logging.exception("Erro ao salvar insumo.")
        return False, str(e)

    finally:
        conn.close()


@st.cache_data(ttl=15)
def carregar_insumos(obra):
    conn = get_connection()

    try:
        df = pd.read_sql(
            "SELECT * FROM insumos WHERE Obra = ?",
            conn,
            params=(obra,)
        )

        # 🔥 GARANTIAS
        if df is None:
            df = pd.DataFrame()

        if "NotaID" not in df.columns:
            df["NotaID"] = None

        if "ValorTotal" in df.columns:
            df["ValorTotal"] = pd.to_numeric(df["ValorTotal"], errors="coerce")

        return df

    except Exception as e:
        logging.exception("Erro ao carregar insumos da obra %s.", obra)
        return pd.DataFrame(columns=[
            "ID", "Obra", "Etapa", "Material",
            "Quantidade", "ValorUnitario", "ValorTotal",
            "Data", "NotaID"
        ])

    finally:
        conn.close()

def excluir_insumo(insumo_id, usuario="admin"):
    conn = get_connection()

    try:
        # pegar valor antes de excluir
        df = pd.read_sql(
            "SELECT ValorTotal FROM insumos WHERE ID = ?",
            conn,
            params=(insumo_id,)
        )

        valor_antes = float(df["ValorTotal"].iloc[0]) if not df.empty else 0

        # excluir
        conn.execute("DELETE FROM insumos WHERE ID = ?", (insumo_id,))

        # log
        conn.execute("""
            INSERT INTO historico_insumos (
                ID, InsumoID, Acao, ValorAntes, ValorDepois, Usuario, Data
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            insumo_id,
            "EXCLUSAO",
            valor_antes,
            0,
            usuario,
            datetime.now().isoformat()
        ))

        conn.commit()
        st.cache_data.clear()
        return True, None

    except Exception as e:
        logging.exception("Erro ao excluir insumo %s.", insumo_id)
        return False, str(e)

    finally:
        conn.close()

def atualizar_insumo(insumo_id, dados, usuario="admin"):
    conn = get_connection()

    try:
        material = normalizar_nome_produto(dados.get("Material"))
        if not material:
            return False, "Informe o material."
        obter_ou_criar_produto(
            material,
            dados.get("Unidade", ""),
            dados.get("CategoriaProduto", ""),
        )
        quantidade = float(dados.get("Quantidade", 0))
        valor_unit = float(dados.get("ValorUnitario", 0))
        valor_total = quantidade * valor_unit

        # pegar valor antigo
        df = pd.read_sql(
            "SELECT ValorTotal FROM insumos WHERE ID = ?",
            conn,
            params=(insumo_id,)
        )

        valor_antes = float(df["ValorTotal"].iloc[0]) if not df.empty else 0

        # atualizar
        conn.execute("""
            UPDATE insumos
            SET Material = ?, Quantidade = ?, ValorUnitario = ?, ValorTotal = ?
            WHERE ID = ?
        """, (
            material,
            quantidade,
            valor_unit,
            valor_total,
            insumo_id
        ))

        # log
        conn.execute("""
            INSERT INTO historico_insumos (
                ID, InsumoID, Acao, ValorAntes, ValorDepois, Usuario, Data
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            insumo_id,
            "EDICAO",
            valor_antes,
            valor_total,
            usuario,
            datetime.now().isoformat()
        ))

        conn.commit()
        st.cache_data.clear()
        return True, None

    except Exception as e:
        logging.exception("Erro ao atualizar insumo %s.", insumo_id)
        return False, str(e)

    finally:
        conn.close()
