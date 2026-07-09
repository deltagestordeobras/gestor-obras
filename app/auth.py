import streamlit as st

from services.recuperacao_senha import (
    resetar_senha,
    solicitar_recuperacao_senha,
    validar_token_reset,
)


def _limpar_estado_recuperacao():
    for chave in [
        "recuperacao_etapa",
        "recuperacao_identificador",
        "recuperacao_codigo",
        "recuperacao_usuario_validado",
    ]:
        st.session_state.pop(chave, None)


def tela_recuperacao():
    if "recuperacao_etapa" not in st.session_state:
        st.session_state["recuperacao_etapa"] = "solicitar"

    _, centro, _ = st.columns([1.25, 0.9, 1.25])
    with centro:
        st.image("icons/logo.png", use_container_width=True)
        st.markdown(
            """
            <div class="delta-login-title">
                <span>Recuperação segura</span>
                <h1>DELTA Gestor de Obras</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("recuperar_senha", border=True):
            identificador = st.text_input(
                "Login ou e-mail",
                key="recuperacao_identificador",
                disabled=st.session_state["recuperacao_etapa"] != "solicitar",
            )

            if st.session_state["recuperacao_etapa"] == "solicitar":
                enviar = st.form_submit_button(
                    "Enviar código",
                    type="primary",
                    use_container_width=True,
                )
                if enviar:
                    if not identificador.strip():
                        st.warning("Informe seu login ou e-mail.")
                        return

                    ok, erro = solicitar_recuperacao_senha(identificador)
                    if ok:
                        st.session_state["recuperacao_etapa"] = "validar"
                        st.success("Se os dados estiverem cadastrados, o código foi enviado.")
                        st.rerun()
                    else:
                        st.error(erro)

            elif st.session_state["recuperacao_etapa"] == "validar":
                codigo = st.text_input(
                    "Código recebido",
                    max_chars=6,
                    key="recuperacao_codigo",
                )
                validar = st.form_submit_button(
                    "Validar código",
                    type="primary",
                    use_container_width=True,
                )
                if validar:
                    ok, usuario_ou_erro = validar_token_reset(identificador, codigo)
                    if ok:
                        st.session_state["recuperacao_usuario_validado"] = usuario_ou_erro
                        st.session_state["recuperacao_etapa"] = "alterar"
                        st.rerun()
                    else:
                        st.error(usuario_ou_erro)

            else:
                st.success("Código validado.")
                nova_senha = st.text_input("Nova senha", type="password")
                confirmar = st.text_input("Confirmar nova senha", type="password")
                alterar = st.form_submit_button(
                    "Alterar senha",
                    type="primary",
                    use_container_width=True,
                )
                if alterar:
                    if not nova_senha or nova_senha != confirmar:
                        st.warning("Informe senhas iguais.")
                        return

                    ok, erro = resetar_senha(
                        identificador,
                        st.session_state.get("recuperacao_codigo", ""),
                        nova_senha,
                    )
                    if ok:
                        _limpar_estado_recuperacao()
                        st.session_state.recuperacao = False
                        st.success("Senha redefinida com sucesso.")
                        st.rerun()
                    else:
                        st.error(erro)

        if st.button("Voltar ao login", use_container_width=True):
            _limpar_estado_recuperacao()
            st.session_state.recuperacao = False
            st.rerun()

        st.markdown(
            '<div class="delta-login-footer">Powered by Delta Sistemas</div>',
            unsafe_allow_html=True,
        )
