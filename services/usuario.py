import pandas as pd
import uuid
import logging
import streamlit as st
from database.connection import get_connection
from core.auth import verificar_senha, hash_senha
from datetime import datetime, timedelta
from services.permissoes import (
    normalizar_permissoes,
    permissoes_para_json,
    permissoes_por_perfil,
)


# ===============================
# 🔐 LOGIN
# ===============================

def autenticar_usuario(usuario, senha):

    conn = get_connection()

    try:
        cursor = conn.execute("""
            SELECT * FROM usuarios WHERE Usuario = ?
        """, (usuario,))

        row = cursor.fetchone()

        if not row:
            return None

        # Conversao segura, funciona com ou sem row_factory.
        if hasattr(row, "keys"):
            user_dict = dict(row)
        else:
            colunas = [col[0] for col in cursor.description]
            user_dict = dict(zip(colunas, row))

    except Exception:
        logging.exception("Erro ao autenticar usuario %s.", usuario)
        return None

    finally:
        conn.close()

    if not user_dict.get("Senha") or user_dict.get("Senha") == hash_senha(""):
        return {"primeiro_acesso": True, "usuario": usuario}

    if verificar_senha(senha, user_dict["Senha"]):
        user_dict["Permissoes"] = normalizar_permissoes(user_dict.get("Permissoes"))
        return user_dict

    return None

def carregar_usuarios():

    conn = get_connection()

    try:
        df = pd.read_sql("SELECT * FROM usuarios", conn)
        return df
    except Exception:
        logging.exception("Erro ao carregar usuários.")
        return pd.DataFrame(columns=["Usuario", "Perfil", "ObraID", "Permissoes"])
    finally:
        conn.close()


# ===============================
# 💾 SALVAR USUÁRIO
# ===============================
def salvar_usuario(
    usuario,
    senha,
    perfil,
    obra_id=None,
    permissoes=None,
    email=None,
    telefone=None,
    nome=None,
):
    nome = " ".join(str(nome or "").split())
    usuario = " ".join(str(usuario or "").split())
    email = str(email or "").strip().lower()

    if not nome:
        logging.warning("Cadastro de usu?rio bloqueado: nome vazio.")
        return False

    if not usuario:
        logging.warning("Cadastro de usu?rio bloqueado: login vazio.")
        return False

    if not senha:
        logging.warning("Cadastro de usu?rio bloqueado: senha vazia.")
        return False

    if not email or "@" not in email:
        logging.warning("Cadastro de usu?rio bloqueado: e-mail inv?lido.")
        return False

    conn = get_connection()

    permissoes = permissoes_por_perfil(perfil, permissoes)
    senha_hash = hash_senha(senha)
    permissoes_json = permissoes_para_json(permissoes)

    try:
        duplicado = conn.execute(
            "SELECT 1 FROM usuarios WHERE lower(trim(Usuario)) = lower(trim(?))",
            (usuario,),
        ).fetchone()
        if duplicado:
            logging.warning("Cadastro de usu?rio bloqueado: login duplicado %s.", usuario)
            return False

        conn.execute("""
            INSERT INTO usuarios (
                Nome, Usuario, Senha, Perfil, ObraID, Permissoes, Email, Telefone
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nome,
            usuario,
            senha_hash,
            perfil,
            obra_id,
            permissoes_json,
            email,
            telefone,
        ))

        conn.commit()
        st.cache_data.clear()
        return True

    except Exception:
        logging.exception("Erro ao salvar usu?rio %s.", usuario)
        return False

    finally:
        conn.close()


def existe_admin():
    conn = get_connection()

    try:
        cursor = conn.execute("""
            SELECT COUNT(*)
            FROM usuarios
            WHERE upper(Perfil) = 'ADMIN'
        """)
        return cursor.fetchone()[0] > 0
    except Exception:
        logging.exception("Erro ao verificar existÃªncia de ADMIN.")
        return False
    finally:
        conn.close()


def criar_primeiro_admin(nome, email, usuario, senha):
    if existe_admin():
        return False, "Já existe um usuário ADMIN cadastrado."

    if not nome.strip():
        return False, "Informe o nome."

    if not email.strip() or "@" not in email:
        return False, "Informe um e-mail válido."

    if not usuario.strip():
        return False, "Informe o usuário."

    if not senha:
        return False, "Informe a senha."

    sucesso = salvar_usuario(
        usuario.strip(),
        senha,
        "ADMIN",
        None,
        None,
        email.strip().lower(),
        None,
        nome.strip(),
    )

    if not sucesso:
        return False, "Não foi possível criar o primeiro ADMIN."

    return True, None


# ===============================
# ✏️ ATUALIZAR PERMISSÕES
# ===============================
def atualizar_permissoes(usuario, permissoes, obra_id=None):

    conn = get_connection()
    permissoes_json = permissoes_para_json(permissoes)

    try:
        if obra_id:
            conn.execute("""
                UPDATE usuarios
                SET Permissoes = ?
                WHERE Usuario = ? AND ObraID = ?
            """, (permissoes_json, usuario, obra_id))
        else:
            conn.execute("""
                UPDATE usuarios
                SET Permissoes = ?
                WHERE Usuario = ?
            """, (permissoes_json, usuario))

        conn.commit()
        st.cache_data.clear()
        return True, None

    except Exception as e:
        logging.exception("Erro ao atualizar permissões do usuário %s.", usuario)
        return False, str(e)

    finally:
        conn.close()


def atualizar_contato_usuario(usuario, email, telefone=None):
    conn = get_connection()

    try:
        conn.execute("""
            UPDATE usuarios
            SET Email = ?, Telefone = ?
            WHERE Usuario = ?
        """, (email, telefone, usuario))
        conn.commit()
        st.cache_data.clear()
        return True, None
    except Exception as e:
        logging.exception("Erro ao atualizar contato do usuário %s.", usuario)
        return False, str(e)
    finally:
        conn.close()



def definir_senha(usuario, nova_senha):

    conn = get_connection()

    try:
        senha_hash = hash_senha(nova_senha)

        conn.execute("""
            UPDATE usuarios
            SET Senha = ?
            WHERE Usuario = ?
        """, (senha_hash, usuario))

        conn.commit()
        st.cache_data.clear()
        return True, None

    except Exception as e:
        logging.exception("Erro ao definir senha do usuário %s.", usuario)
        return False, str(e)

    finally:
        conn.close()


def gerar_token_reset(usuario):
    from services.recuperacao_senha import solicitar_recuperacao_senha

    ok, resultado = solicitar_recuperacao_senha(usuario)
    if ok:
        return resultado, None
    return None, resultado

def resetar_senha(usuario, token, nova_senha):
    from services.recuperacao_senha import resetar_senha as resetar_senha_segura

    return resetar_senha_segura(usuario, token, nova_senha)
