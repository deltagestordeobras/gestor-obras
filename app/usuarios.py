import streamlit as st
import pandas as pd

from services.usuario import (
    carregar_usuarios,
    salvar_usuario,
    atualizar_permissoes,
    atualizar_contato_usuario,
)
from services.obra import listar_obras
from services.permissoes import PERMISSOES_MODULOS, normalizar_permissoes


def tela_usuarios():
    secao = st.session_state.get("usuarios_secao", "usuarios")
    mostrar_usuarios = secao != "permissoes"
    mostrar_permissoes = secao == "permissoes"

    st.title("👤 Cadastro de Usuários" if mostrar_usuarios else "🔐 Editar Permissões")

    df_obras = listar_obras()
    df_usuarios = carregar_usuarios()
    modulos = PERMISSOES_MODULOS

    if mostrar_usuarios:
        with st.form("form_usuario", clear_on_submit=True):
            usuario = st.text_input("Usuário")
            email = st.text_input("E-mail")
            telefone = st.text_input("Telefone (opcional)")
            perfil = st.selectbox("Perfil", ["ADMIN", "FUNCIONARIO", "PARCEIRO"])

            st.subheader("🔐 Permissões de acesso")
            permissoes = []
            col1, col2 = st.columns(2)

            for i, modulo in enumerate(modulos):
                if i % 2 == 0:
                    if col1.checkbox(modulo.capitalize()):
                        permissoes.append(modulo)
                else:
                    if col2.checkbox(modulo.capitalize()):
                        permissoes.append(modulo)

            obra_id = None
            if perfil == "PARCEIRO":
                if df_obras is not None and not df_obras.empty:
                    obras_dict = {row["Nome"]: row["ID"] for _, row in df_obras.iterrows()}
                    obra_nome = st.selectbox(
                        "Vincular à Obra",
                        list(obras_dict.keys()),
                        help="Selecione a obra que o parceiro terá acesso",
                    )
                    obra_id = obras_dict[obra_nome]
                else:
                    st.warning("Cadastre uma obra primeiro.")

            if st.form_submit_button("💾 Criar Usuário"):
                if usuario.strip() == "":
                    st.warning("Informe o usuário.")
                    return

                if not email.strip() or "@" not in email:
                    st.warning("Informe um e-mail válido.")
                    return

                if perfil == "ADMIN":
                    permissoes = modulos

                sucesso = salvar_usuario(
                    usuario.strip(),
                    "",
                    perfil,
                    obra_id,
                    permissoes,
                    email.strip().lower(),
                    telefone.strip() or None,
                )

                if sucesso:
                    st.success("Usuário criado! (senha será definida no primeiro acesso)")
                    st.rerun()
                else:
                    st.error("Erro ao criar usuário")

    if df_usuarios is None or df_usuarios.empty:
        st.info("Nenhum usuário cadastrado.")
        return

    if mostrar_usuarios:
        st.divider()
        st.subheader("📋 Usuários Cadastrados")
        st.dataframe(df_usuarios, use_container_width=True)

        st.divider()
        st.subheader("Contato para recuperação")

        contato_indice = st.selectbox(
            "Selecione o usuário para atualizar contato",
            df_usuarios.reset_index(drop=True).index.tolist(),
            format_func=lambda indice: str(
                df_usuarios.reset_index(drop=True).loc[indice, "Usuario"]
            ),
            key="usuario_editar_contato",
        )
        contato_info = df_usuarios.reset_index(drop=True).loc[contato_indice]

        with st.form(f"form_contato_{contato_info['Usuario']}"):
            contato_email = st.text_input(
                "E-mail",
                value="" if pd.isna(contato_info.get("Email")) else str(contato_info.get("Email")),
            )
            contato_telefone = st.text_input(
                "Telefone (opcional)",
                value="" if pd.isna(contato_info.get("Telefone")) else str(contato_info.get("Telefone")),
            )

            if st.form_submit_button("Salvar contato"):
                if not contato_email.strip() or "@" not in contato_email:
                    st.warning("Informe um e-mail válido.")
                else:
                    ok, erro = atualizar_contato_usuario(
                        str(contato_info["Usuario"]),
                        contato_email.strip().lower(),
                        contato_telefone.strip() or None,
                    )
                    if ok:
                        st.success("Contato atualizado.")
                        st.rerun()
                    else:
                        st.error(erro)

    if mostrar_permissoes:
        st.divider()
        st.subheader("✏️ Editar Permissões")

        usuarios_edicao = df_usuarios.reset_index(drop=True).copy()
        nomes_obras = {
            str(row["ID"]): str(row["Nome"])
            for _, row in df_obras.iterrows()
        } if df_obras is not None and not df_obras.empty else {}

        usuario_indice = st.selectbox(
            "Selecione o usuário",
            usuarios_edicao.index.tolist(),
            format_func=lambda indice: (
                f"{usuarios_edicao.loc[indice, 'Usuario']} · "
                f"{usuarios_edicao.loc[indice, 'Perfil']} · "
                f"{nomes_obras.get(str(usuarios_edicao.loc[indice, 'ObraID']), 'Sem obra vinculada')}"
            ),
            key="usuario_editar_permissoes",
        )

        user_info = usuarios_edicao.loc[usuario_indice]
        usuario_sel = str(user_info["Usuario"])
        obra_id_sel = "" if pd.isna(user_info["ObraID"]) else str(user_info["ObraID"])
        permissoes_atuais = normalizar_permissoes(user_info["Permissoes"])

        st.markdown("### 🔐 Permissões")
        novas_permissoes = []
        col1, col2 = st.columns(2)

        for i, modulo in enumerate(modulos):
            checked = modulo in permissoes_atuais
            checkbox_key = f"perm_{usuario_sel}_{obra_id_sel or 'sem_obra'}_{modulo}"

            if i % 2 == 0:
                if col1.checkbox(modulo.capitalize(), value=checked, key=checkbox_key):
                    novas_permissoes.append(modulo)
            else:
                if col2.checkbox(modulo.capitalize(), value=checked, key=checkbox_key):
                    novas_permissoes.append(modulo)

        if st.button("💾 Atualizar Permissões", use_container_width=True):
            ok, erro = atualizar_permissoes(
                usuario_sel,
                novas_permissoes,
                obra_id_sel or None,
            )

            if ok:
                st.success("Permissões atualizadas!")
                st.rerun()
            else:
                st.error(erro)
