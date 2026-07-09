import pandas as pd
import streamlit as st

from app.ui_utils import data_br as _data, texto as _texto
from services.evolucao import (
    caminho_absoluto,
    carregar_evolucoes,
    excluir_registro_evolucao,
    salvar_evolucao,
)
from services.listas import listar_etapas_ativas


def _formulario_upload(obra_id, obra_nome, etapas):
    with st.expander("Registrar nova evolução", expanded=False):
        with st.form("form_nova_evolucao", clear_on_submit=True):
            col1, col2, col3 = st.columns([1, 1.4, 1.2])
            with col1:
                data = st.date_input("Data", value=pd.Timestamp.today().date())
            with col2:
                etapa = st.selectbox("Etapa da obra", etapas)
            with col3:
                responsavel = st.text_input(
                    "Responsável",
                    value=str(st.session_state.get("usuario", "")),
                )

            titulo = st.text_input("Título", placeholder="Ex.: Concretagem das sapatas")
            descricao = st.text_area(
                "Descrição",
                placeholder="Registre o avanço executado, ocorrências e observações.",
            )
            fotos = st.file_uploader(
                "Fotos",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                help="JPG, JPEG ou PNG. Limite de 10 MB por arquivo.",
            )
            enviar = st.form_submit_button(
                "Salvar evolução",
                type="primary",
                use_container_width=True,
            )

        if not enviar:
            return
        if not str(etapa).strip() or not titulo.strip() or not responsavel.strip():
            st.error("Preencha etapa, título e responsável.")
            return

        ok, erro = salvar_evolucao(
            obra_id,
            obra_nome,
            etapa,
            data,
            titulo,
            descricao,
            responsavel,
            fotos,
        )
        if ok:
            st.success("Evolução registrada com sucesso.")
            st.rerun()
        st.error(erro)


def _filtros(df, etapas):
    etapa_pendente = st.session_state.pop("evolucao_etapa_pendente", None)
    etapas_disponiveis = sorted(
        set(etapas)
        | set(df["Etapa"].dropna().astype(str).tolist() if not df.empty else [])
    )
    opcoes_etapa = ["Todas"] + etapas_disponiveis
    if etapa_pendente in opcoes_etapa:
        st.session_state["evolucao_filtro_etapa"] = etapa_pendente

    responsaveis = ["Todos"] + sorted(
        df["Responsavel"].dropna().astype(str).unique().tolist()
        if not df.empty else []
    )
    hoje = pd.Timestamp.today().date()
    datas = pd.to_datetime(df["Data"], errors="coerce") if not df.empty else pd.Series(dtype="datetime64[ns]")
    data_minima = datas.min().date() if not datas.empty and pd.notna(datas.min()) else hoje
    data_maxima = datas.max().date() if not datas.empty and pd.notna(datas.max()) else hoje

    c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1.2])
    with c1:
        etapa = st.selectbox("Filtrar por etapa", opcoes_etapa, key="evolucao_filtro_etapa")
    with c2:
        inicio = st.date_input("De", value=data_minima, key="evolucao_filtro_inicio")
    with c3:
        fim = st.date_input("Até", value=data_maxima, key="evolucao_filtro_fim")
    with c4:
        responsavel = st.selectbox(
            "Filtrar por responsável",
            responsaveis,
            key="evolucao_filtro_responsavel",
        )
    return etapa, inicio, fim, responsavel


def _miniaturas(grupo, chave):
    fotos = grupo.to_dict("records")
    colunas = st.columns(min(4, max(1, len(fotos))))
    for indice, foto in enumerate(fotos):
        miniatura = caminho_absoluto(foto.get("Miniatura"))
        if miniatura:
            with colunas[indice % len(colunas)]:
                st.image(str(miniatura), use_container_width=True)

    if st.button(
        f"Ver {len(fotos)} foto(s) ampliada(s)",
        key=f"evolucao_ampliar_{chave}",
        use_container_width=True,
    ):
        atual = st.session_state.get("evolucao_grupo_ampliado")
        st.session_state["evolucao_grupo_ampliado"] = None if atual == chave else chave

    if st.session_state.get("evolucao_grupo_ampliado") == chave:
        for foto in fotos:
            arquivo = caminho_absoluto(foto.get("Arquivo"))
            if arquivo:
                st.image(str(arquivo), use_container_width=True)


def _timeline(df, obra_id, admin):
    if df.empty:
        st.info("Nenhuma evolução fotográfica encontrada para os filtros selecionados.")
        return

    grupos = df.groupby(
        ["Data", "Etapa", "Titulo", "Descricao", "Responsavel", "CriadoEm", "Origem"],
        dropna=False,
        sort=False,
    )
    for indice, (chaves, grupo) in enumerate(grupos):
        data, etapa, titulo, descricao, responsavel, criado_em, origem = chaves
        chave = str(criado_em).replace(":", "_").replace(".", "_")

        with st.container(border=True):
            cabecalho, acoes = st.columns([6, 1], vertical_alignment="center")
            with cabecalho:
                st.markdown(
                    f"""<div class="delta-evolution-head">
                        <span class="delta-evolution-date">{_texto(_data(data))}</span>
                        <span class="delta-badge">{_texto(etapa)}</span>
                        <h3>{_texto(titulo)}</h3>
                        <p>{_texto(descricao) if descricao else "Sem descrição."}</p>
                        <small>Responsável: {_texto(responsavel)} · {len(grupo)} foto(s)</small>
                        {f'<small>Origem: {_texto(origem)}</small>' if pd.notna(origem) and origem else ''}
                    </div>""",
                    unsafe_allow_html=True,
                )
            with acoes:
                if admin:
                    confirmar = st.checkbox(
                        "Excluir",
                        key=f"evolucao_confirmar_{chave}_{indice}",
                        help="Marque para habilitar a exclusão deste registro.",
                    )
                    if st.button(
                        "Excluir registro",
                        disabled=not confirmar,
                        key=f"evolucao_excluir_{chave}_{indice}",
                    ):
                        excluir_registro_evolucao(obra_id, criado_em)
                        st.success("Registro excluído.")
                        st.rerun()
            _miniaturas(grupo, chave)


def tela_evolucao(obra_id, obra_nome):
    admin = str(st.session_state.get("perfil", "")).upper() == "ADMIN"
    st.markdown("## Evolução da obra")
    st.caption(f"Registro fotográfico da execução real de {obra_nome}")

    etapas = listar_etapas_ativas()
    if admin:
        _formulario_upload(obra_id, obra_nome, etapas)

    todos = carregar_evolucoes(obra_id)
    st.markdown('<div class="delta-section-title">Linha do tempo</div>', unsafe_allow_html=True)
    etapa, inicio, fim, responsavel = _filtros(todos, etapas)
    filtrados = carregar_evolucoes(obra_id, etapa, inicio, fim, responsavel)
    _timeline(filtrados, obra_id, admin)
