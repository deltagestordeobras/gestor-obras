from pathlib import Path

import streamlit as st

from services.backup import (
    BACKUP_DIR,
    criar_backup_manual,
    limpar_backups_antigos,
    listar_backups,
    abrir_pasta_backups,
    restaurar_backup,
    resumo_backups,
)


def _card_metrica(titulo, valor, detalhe):
    st.markdown(
        f"""
        <div class="delta-admin-card">
            <h3>{titulo}</h3>
            <strong style="font-size: 1.45rem;">{valor}</strong>
            <p>{detalhe}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def tela_backup():
    st.markdown(
        """
        <div class="delta-admin-hero">
            <span>Seguranca dos dados</span>
            <h1>Backup e Restauracao</h1>
            <p>Proteja bancos, anexos, recibos, logs e configuracoes sensiveis do DELTA Gestor.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    resumo = resumo_backups()
    ultimo = resumo["ultimo"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        _card_metrica(
            "Ultimo backup",
            ultimo["modificado_em"].strftime("%d/%m/%Y %H:%M") if ultimo else "Nenhum",
            ultimo["nome"] if ultimo else "Nenhum backup localizado.",
        )
    with col2:
        _card_metrica("Backups", resumo["quantidade"], "Arquivos .zip encontrados.")
    with col3:
        _card_metrica("Tamanho total", resumo["tamanho_total_formatado"], "Espaco usado pela pasta.")
    with col4:
        _card_metrica("Pasta", "backups", resumo["pasta"])

    st.divider()

    acao1, acao2, acao3 = st.columns(3)
    with acao1:
        if st.button("Fazer backup agora", type="primary", use_container_width=True):
            try:
                caminho = criar_backup_manual()
                st.success("Backup criado com sucesso.")
                st.code(str(caminho))
            except Exception as erro:
                st.error(f"Nao foi possivel criar o backup: {erro}")
    with acao2:
        if st.button("Abrir pasta de backups", use_container_width=True):
            try:
                abrir_pasta_backups()
            except Exception as erro:
                st.error(f"Nao foi possivel abrir a pasta: {erro}")
    with acao3:
        confirmar_limpeza = st.text_input(
            "Digite LIMPAR para remover backups antigos",
            key="backup_confirmar_limpeza",
        )
        if st.button("Limpar backups antigos", use_container_width=True):
            if confirmar_limpeza.strip().upper() != "LIMPAR":
                st.warning("Digite LIMPAR para confirmar a limpeza.")
            else:
                removidos = limpar_backups_antigos(30)
                st.success(f"Limpeza concluida. Backups removidos: {len(removidos)}")

    st.divider()
    st.subheader("Restaurar backup")
    st.warning(
        "A restauracao sobrescreve arquivos presentes no backup. Antes de restaurar, "
        "o sistema cria automaticamente um backup PRE_RESTAURACAO do estado atual."
    )

    backups = listar_backups()
    opcoes = ["Selecionar backup existente"] + [backup["nome"] for backup in backups]
    selecionado = st.selectbox("Backup", opcoes)
    upload = st.file_uploader("Ou enviar arquivo .zip", type=["zip"])
    confirmacao = st.text_input('Para restaurar, digite exatamente "RESTAURAR"')

    caminho_para_restaurar = None
    if selecionado != "Selecionar backup existente":
        caminho_para_restaurar = next(
            (backup["caminho"] for backup in backups if backup["nome"] == selecionado),
            None,
        )
    elif upload is not None:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        nome_upload = Path(upload.name).name
        caminho_upload = BACKUP_DIR / f"UPLOAD_RESTAURACAO_{nome_upload}"
        caminho_upload.write_bytes(upload.getbuffer())
        caminho_para_restaurar = caminho_upload

    if st.button("Restaurar backup", type="primary", use_container_width=True):
        if confirmacao != "RESTAURAR":
            st.error('Digite exatamente "RESTAURAR" para confirmar.')
        elif not caminho_para_restaurar:
            st.error("Selecione ou envie um backup para restaurar.")
        else:
            try:
                backup_previo = restaurar_backup(Path(caminho_para_restaurar))
                st.success("Backup restaurado com sucesso. Reinicie o sistema para concluir.")
                st.info(f"Backup pre-restauracao criado em: {backup_previo}")
            except Exception as erro:
                st.error(f"Nao foi possivel restaurar o backup: {erro}")

    st.divider()
    st.subheader("Backups existentes")
    if not backups:
        st.info("Nenhum backup encontrado.")
        return

    tabela = [
        {
            "Arquivo": backup["nome"],
            "Data": backup["modificado_em"].strftime("%d/%m/%Y %H:%M"),
            "Tamanho": backup["tamanho_formatado"],
            "Caminho": backup["caminho"],
        }
        for backup in backups
    ]
    st.dataframe(tabela, use_container_width=True, hide_index=True)
