import streamlit as st


def tela_administracao(obra):
    perfil = str(st.session_state.get("perfil", "ADMIN")).upper()
    titulo = "Administração" if perfil == "ADMIN" else "Minha Conta"

    st.markdown(
        f"""
        <div class="delta-admin-hero">
            <span>Controle do sistema</span>
            <h1>{titulo}</h1>
            <p>Atalhos seguros para configurações e gestão da obra {obra}.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    atalhos = [
        {
            "titulo": "Usuários",
            "descricao": "Cadastrar usuários e revisar acessos.",
            "icone": "👥",
            "rota": "usuarios",
            "grupo": "cadastros",
            "usuarios_secao": "usuarios",
            "admin": True,
        },
        {
            "titulo": "Permissões",
            "descricao": "Editar permissões por usuário e obra.",
            "icone": "🛡️",
            "rota": "usuarios",
            "grupo": "cadastros",
            "usuarios_secao": "permissoes",
            "admin": True,
        },
        {
            "titulo": "Configurações",
            "descricao": "Ajustar tabelas e parâmetros operacionais.",
            "icone": "🔧",
            "rota": "configuracoes",
            "grupo": "administracao_grupo",
            "admin": False,
        },
        {
            "titulo": "E-mail",
            "descricao": "Configurar SMTP e testar envio.",
            "icone": "✉️",
            "rota": "config_email",
            "grupo": "administracao_grupo",
            "admin": True,
        },
        {
            "titulo": "Listas do Sistema",
            "descricao": "Manter etapas e listas editáveis.",
            "icone": "📋",
            "rota": "config_listas",
            "grupo": "administracao_grupo",
            "admin": True,
        },
        {
            "titulo": "Auditoria",
            "descricao": "Conferir notas e materiais vinculados.",
            "icone": "🔎",
            "rota": "auditoria",
            "grupo": "administracao_grupo",
            "admin": True,
        },
        {
            "titulo": "Backup",
            "descricao": "Proteger e restaurar dados do sistema.",
            "icone": "💾",
            "rota": "backup",
            "grupo": "administracao_grupo",
            "admin": True,
        },
    ]

    atalhos_visiveis = [
        atalho for atalho in atalhos
        if perfil == "ADMIN" or not atalho["admin"]
    ]

    for inicio in range(0, len(atalhos_visiveis), 3):
        colunas = st.columns(3)
        for indice, atalho in enumerate(atalhos_visiveis[inicio:inicio + 3]):
            with colunas[indice]:
                st.markdown(
                    f"""
                    <div class="delta-admin-card">
                        <div class="delta-admin-card__icon">{atalho['icone']}</div>
                        <h3>{atalho['titulo']}</h3>
                        <p>{atalho['descricao']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(
                    f"Abrir {atalho['titulo']}",
                    key=f"admin_atalho_{atalho['rota']}_{atalho['titulo']}",
                    use_container_width=True,
                ):
                    st.session_state["modulo_ativo"] = atalho["rota"]
                    st.session_state["grupo_ativo"] = atalho["grupo"]
                    st.session_state["admin_navegacao_interna"] = True
                    if "usuarios_secao" in atalho:
                        st.session_state["usuarios_secao"] = atalho["usuarios_secao"]
                    else:
                        st.session_state.pop("usuarios_secao", None)
                    st.rerun()

    st.info("Dados técnicos, IDs internos e tabelas brutas foram ocultados desta visão administrativa.")
