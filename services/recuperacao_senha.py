import hashlib
import os
import secrets
import smtplib
import tomllib
import uuid
from datetime import datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

import streamlit as st

from core.auth import hash_senha
from database.connection import get_connection


SMTP_FIELDS = [
    "smtp_server",
    "smtp_port",
    "smtp_user",
    "smtp_password",
    "smtp_from",
]
SECRETS_PATH = Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml"


def _hash_token(token):
    return hashlib.sha256(str(token).encode("utf-8")).hexdigest()


def _auditar(conn, usuario, identificador, evento, detalhes=""):
    conn.execute(
        """
        INSERT INTO auditoria_recuperacao_senha (
            ID, Usuario, Identificador, Evento, DataHora, Detalhes
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid.uuid4()),
            usuario,
            identificador,
            evento,
            datetime.now().isoformat(),
            detalhes,
        ),
    )


def _config_email():
    config = {
        "smtp_server": os.getenv("DELTA_SMTP_HOST", ""),
        "smtp_port": os.getenv("DELTA_SMTP_PORT", ""),
        "smtp_user": os.getenv("DELTA_SMTP_USER", ""),
        "smtp_password": os.getenv("DELTA_SMTP_PASSWORD", ""),
        "smtp_from": os.getenv("DELTA_SMTP_FROM", ""),
    }

    try:
        dados = tomllib.loads(SECRETS_PATH.read_text(encoding="utf-8"))
        smtp = dados.get("smtp", {}) if isinstance(dados.get("smtp"), dict) else {}
        aliases = {
            "smtp_server": smtp.get("host"),
            "smtp_port": smtp.get("port"),
            "smtp_user": smtp.get("user"),
            "smtp_password": smtp.get("password"),
            "smtp_from": smtp.get("from"),
        }
        for campo in config:
            valor = dados.get(campo, aliases.get(campo))
            if valor not in (None, ""):
                config[campo] = str(valor).strip()
    except Exception:
        pass

    return config


def diagnosticar_configuracao_smtp():
    config = _config_email()
    return {
        "arquivo": str(SECRETS_PATH),
        "existe": SECRETS_PATH.exists(),
        "faltando": [
            campo for campo in SMTP_FIELDS
            if not str(config.get(campo, "")).strip()
        ],
    }


def salvar_configuracao_smtp(
    smtp_server,
    smtp_port,
    smtp_user,
    smtp_password,
    smtp_from,
):
    atual = _config_email()
    senha = str(smtp_password or "").strip() or atual.get("smtp_password", "")
    config = {
        "smtp_server": str(smtp_server or "").strip(),
        "smtp_port": str(smtp_port or "").strip(),
        "smtp_user": str(smtp_user or "").strip(),
        "smtp_password": senha,
        "smtp_from": str(smtp_from or "").strip(),
    }
    faltando = [campo for campo in SMTP_FIELDS if not config[campo]]
    if faltando:
        return False, "Campos obrigatórios: " + ", ".join(faltando)

    def valor_toml(valor):
        return '"' + str(valor).replace("\\", "\\\\").replace('"', '\\"') + '"'

    conteudo = "\n".join(
        f"{campo} = {valor_toml(config[campo])}"
        for campo in SMTP_FIELDS
    ) + "\n"

    try:
        SECRETS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SECRETS_PATH.write_text(conteudo, encoding="utf-8")
        try:
            os.chmod(SECRETS_PATH, 0o600)
        except OSError:
            pass
        return True, None
    except Exception as e:
        return False, f"Não foi possível salvar a configuração: {type(e).__name__}"


def _enviar_mensagem(email, assunto, conteudo):
    config = _config_email()
    faltando = diagnosticar_configuracao_smtp()["faltando"]
    if faltando:
        return False, "Campos SMTP ausentes: " + ", ".join(faltando)

    mensagem = EmailMessage()
    mensagem["Subject"] = assunto
    mensagem["From"] = config["smtp_from"]
    mensagem["To"] = email
    mensagem.set_content(conteudo)

    try:
        porta = int(config["smtp_port"])
        servidor_cls = smtplib.SMTP_SSL if porta == 465 else smtplib.SMTP
        with servidor_cls(config["smtp_server"], porta, timeout=15) as servidor:
            if porta != 465:
                servidor.starttls()
            servidor.login(config["smtp_user"], config["smtp_password"])
            servidor.send_message(mensagem)
        return True, None
    except Exception as e:
        return False, f"Falha SMTP: {type(e).__name__}"


def _enviar_email(email, token):
    return _enviar_mensagem(
        email,
        "Código de recuperação DELTA",
        f"Seu código de recuperação DELTA é {token}. "
        "Ele expira em 10 minutos. Se você não solicitou, ignore esta mensagem.",
    )


def testar_envio_email(email):
    return _enviar_mensagem(
        email,
        "Teste SMTP DELTA",
        "Este é um e-mail de teste do DELTA Gestor de Obras.",
    )


def solicitar_recuperacao_senha(identificador, canal="email"):
    identificador = str(identificador or "").strip()
    canal = str(canal or "email").strip().lower()
    if canal != "email":
        return False, "Canal de recuperação ainda não disponível."

    conn = get_connection()

    try:
        user = conn.execute(
            """
            SELECT Usuario, Email FROM usuarios
            WHERE lower(Usuario) = lower(?) OR lower(Email) = lower(?)
            """,
            (identificador, identificador),
        ).fetchone()

        if not user:
            _auditar(conn, None, identificador, "SOLICITACAO_USUARIO_NAO_ENCONTRADO")
            conn.commit()
            st.cache_data.clear()
            return True, None

        usuario = user["Usuario"]
        email = str(user["Email"] or "").strip()
        if not email:
            _auditar(conn, usuario, identificador, "SOLICITACAO_SEM_EMAIL")
            conn.commit()
            st.cache_data.clear()
            return False, "Usuário sem e-mail cadastrado. Contate o administrador."

        token = f"{secrets.randbelow(1000000):06d}"
        expira = (datetime.now() + timedelta(minutes=10)).isoformat()
        conn.execute(
            """
            UPDATE usuarios
            SET TokenReset = ?, TokenExpira = ?, TokenTentativas = 0
            WHERE Usuario = ?
            """,
            (_hash_token(token), expira, usuario),
        )
        _auditar(conn, usuario, identificador, "TOKEN_GERADO")
        conn.commit()
        st.cache_data.clear()

        enviado, erro = _enviar_email(email, token)
        if not enviado:
            conn.execute(
                """
                UPDATE usuarios
                SET TokenReset = NULL, TokenExpira = NULL, TokenTentativas = 0
                WHERE Usuario = ?
                """,
                (usuario,),
            )
            _auditar(conn, usuario, identificador, "FALHA_ENVIO_EMAIL", erro)
            conn.commit()
            st.cache_data.clear()
            return False, erro

        _auditar(conn, usuario, identificador, "EMAIL_ENVIADO")
        conn.commit()
        st.cache_data.clear()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def validar_token_reset(identificador, token, registrar_tentativa=True):
    identificador = str(identificador or "").strip()
    token = str(token or "").strip()
    conn = get_connection()

    try:
        user = conn.execute(
            """
            SELECT Usuario, TokenReset, TokenExpira, TokenTentativas
            FROM usuarios
            WHERE lower(Usuario) = lower(?) OR lower(Email) = lower(?)
            """,
            (identificador, identificador),
        ).fetchone()

        if not user or not user["TokenReset"] or not user["TokenExpira"]:
            return False, "Código inválido ou expirado."

        usuario = user["Usuario"]
        tentativas = int(user["TokenTentativas"] or 0)
        if tentativas >= 5:
            return False, "Limite de tentativas excedido. Solicite um novo código."

        if datetime.fromisoformat(user["TokenExpira"]) < datetime.now():
            conn.execute(
                "UPDATE usuarios SET TokenReset = NULL, TokenExpira = NULL WHERE Usuario = ?",
                (usuario,),
            )
            _auditar(conn, usuario, identificador, "TOKEN_EXPIRADO")
            conn.commit()
            st.cache_data.clear()
            return False, "Código inválido ou expirado."

        if not secrets.compare_digest(_hash_token(token), user["TokenReset"]):
            if registrar_tentativa:
                tentativas += 1
                conn.execute(
                    "UPDATE usuarios SET TokenTentativas = ? WHERE Usuario = ?",
                    (tentativas, usuario),
                )
                _auditar(
                    conn,
                    usuario,
                    identificador,
                    "TOKEN_INVALIDO",
                    f"tentativa={tentativas}",
                )
                conn.commit()
                st.cache_data.clear()
            return False, "Código inválido ou expirado."

        _auditar(conn, usuario, identificador, "TOKEN_VALIDADO")
        conn.commit()
        st.cache_data.clear()
        return True, usuario
    finally:
        conn.close()


def resetar_senha(identificador, token, nova_senha):
    valido, usuario_ou_erro = validar_token_reset(
        identificador, token, registrar_tentativa=False
    )
    if not valido:
        return False, usuario_ou_erro

    usuario = usuario_ou_erro
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE usuarios
            SET Senha = ?, TokenReset = NULL, TokenExpira = NULL,
                TokenTentativas = 0
            WHERE Usuario = ?
            """,
            (hash_senha(nova_senha), usuario),
        )
        _auditar(conn, usuario, identificador, "SENHA_REDEFINIDA")
        conn.commit()
        st.cache_data.clear()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
