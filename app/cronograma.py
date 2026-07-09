import pandas as pd
import plotly.express as px
import streamlit as st

from services.cronograma import (
    carregar_cronograma,
    excluir_etapa,
    salvar_etapa,
    sincronizar_calculos,
)
from services.evolucao import contagem_fotos_por_etapa
from services.listas import listar_etapas_ativas
from services.permissoes import tem_permissao


STATUS_EXIBICAO = {
    "Nao iniciada": "Não iniciada",
    "Em andamento": "Em andamento",
    "Atrasada": "Atrasada",
    "Concluida": "Concluída",
}

CORES_STATUS = {
    "Nao iniciada": "#94a3b8",
    "Em andamento": "#62a8ff",
    "Atrasada": "#ff6376",
    "Concluida": "#37d67a",
}


def _data_input(valor, padrao=None):
    convertido = pd.to_datetime(valor, errors="coerce")
    return convertido.date() if pd.notna(convertido) else padrao


def _inteiro(valor, padrao):
    convertido = pd.to_numeric(valor, errors="coerce")
    return int(convertido) if pd.notna(convertido) else int(padrao)


def _seletor_dependencia(opcoes, valor_atual, etapa_atual=None, key=None):
    disponiveis = ["Sem dependência"] + [
        etapa for etapa in opcoes if etapa != etapa_atual
    ]
    indice = disponiveis.index(valor_atual) if valor_atual in disponiveis else 0
    selecionada = st.selectbox("Dependência", disponiveis, index=indice, key=key)
    return None if selecionada == "Sem dependência" else selecionada


def _formulario_etapa(obra_id, obra_nome, df, registro=None):
    editando = registro is not None
    etapa_id = registro.get("ID") if editando else None
    prefixo = str(etapa_id or "novo")
    nomes = df["Etapa"].dropna().astype(str).tolist() if not df.empty else []
    inicio_padrao = _data_input(registro.get("Inicio"), pd.Timestamp.today().date()) if editando else pd.Timestamp.today().date()

    with st.form(f"cronograma_form_{etapa_id or 'novo'}"):
        esquerda, centro, direita = st.columns([2.2, 1, 1])
        with esquerda:
            etapa_atual = str(registro.get("Etapa", "")) if editando else None
            etapas_disponiveis = listar_etapas_ativas(
                incluir=[etapa_atual] if etapa_atual else None
            )
            etapa = st.selectbox(
                "Etapa",
                etapas_disponiveis,
                index=etapas_disponiveis.index(etapa_atual) if etapa_atual in etapas_disponiveis else 0,
                key=f"cronograma_etapa_{prefixo}",
            )
            dependencia = _seletor_dependencia(
                nomes,
                registro.get("Dependencia") if editando else None,
                registro.get("Etapa") if editando else None,
                key=f"cronograma_dependencia_{prefixo}",
            )
        with centro:
            duracao = st.number_input(
                "Duração em dias",
                min_value=1,
                value=_inteiro(registro.get("Duracao"), 1) if editando else 5,
                step=1,
                key=f"cronograma_duracao_{prefixo}",
            )
            ordem = st.number_input(
                "Ordem",
                min_value=1,
                value=_inteiro(registro.get("Ordem"), len(df) + 1) if editando else len(df) + 1,
                step=1,
                key=f"cronograma_ordem_{prefixo}",
            )
        with direita:
            inicio = st.date_input(
                "Data de início",
                value=inicio_padrao,
                key=f"cronograma_inicio_{prefixo}",
            )
            progresso = st.slider(
                "Progresso",
                min_value=0,
                max_value=100,
                value=_inteiro(registro.get("Progresso"), 0) if editando else 0,
                step=5,
                format="%d%%",
                key=f"cronograma_progresso_{prefixo}",
            )

        salvar = st.form_submit_button(
            "Salvar alterações" if editando else "Adicionar etapa",
            type="primary",
            use_container_width=True,
        )

    if not salvar:
        return

    etapa = etapa.strip()
    nomes_outras = {
        nome.casefold() for nome in nomes
        if not editando or nome != str(registro.get("Etapa"))
    }
    if not etapa:
        st.error("Informe o nome da etapa.")
        return
    if etapa.casefold() in nomes_outras:
        st.error("Já existe uma etapa com esse nome nesta obra.")
        return

    salvar_etapa({
        "ID": etapa_id,
        "ObraID": str(obra_id) if obra_id else None,
        "Obra": obra_nome,
        "Etapa": etapa,
        "Duracao": duracao,
        "Dependencia": dependencia,
        "Inicio": inicio.isoformat(),
        "Fim": None,
        "Progresso": progresso,
        "Status": None,
        "Ordem": ordem,
    })
    sincronizar_calculos(obra_id, obra_nome)
    st.success("Etapa atualizada." if editando else "Etapa adicionada.")
    st.rerun()


def _resumo(df):
    progresso = pd.to_numeric(df["Progresso"], errors="coerce").fillna(0)
    duracao = pd.to_numeric(df["Duracao"], errors="coerce").fillna(1).clip(lower=1)
    execucao = float((progresso * duracao).sum() / duracao.sum()) if not df.empty else 0
    atrasadas = int((df["Status"] == "Atrasada").sum()) if not df.empty else 0
    criticas = int(df["Critico"].fillna(False).sum()) if "Critico" in df.columns else 0
    termino = pd.to_datetime(df["Fim"], errors="coerce").max() if not df.empty else pd.NaT

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Execução física", f"{execucao:.0f}%")
    c2.metric("Etapas atrasadas", atrasadas)
    c3.metric("Caminho crítico", f"{criticas} etapa(s)")
    c4.metric("Previsão de término", termino.strftime("%d/%m/%Y") if pd.notna(termino) else "Sem previsão")


def _tabela(df):
    tabela = df.copy()
    tabela["Status"] = tabela["Status"].map(STATUS_EXIBICAO).fillna(tabela["Status"])
    tabela["Inicio"] = pd.to_datetime(tabela["Inicio"], errors="coerce")
    tabela["Fim"] = pd.to_datetime(tabela["Fim"], errors="coerce")
    tabela["Caminho crítico"] = tabela["Critico"].map({True: "Sim", False: ""})

    st.dataframe(
        tabela[[
            "Ordem", "Etapa", "Duracao", "Dependencia", "Inicio", "Fim",
            "Progresso", "Status", "Caminho crítico",
        ]],
        hide_index=True,
        use_container_width=True,
        column_config={
            "Ordem": st.column_config.NumberColumn("Ordem", format="%d"),
            "Duracao": st.column_config.NumberColumn("Duração", format="%d dias"),
            "Inicio": st.column_config.DateColumn("Início", format="DD/MM/YYYY"),
            "Fim": st.column_config.DateColumn("Fim", format="DD/MM/YYYY"),
            "Progresso": st.column_config.ProgressColumn("Progresso", min_value=0, max_value=100, format="%d%%"),
        },
    )


def _gantt(df):
    gantt = df.copy()
    gantt["EtapaExibicao"] = gantt.apply(
        lambda row: f"{row['Etapa']}  •  CRÍTICA" if row.get("Critico") else row["Etapa"],
        axis=1,
    )
    fig = px.timeline(
        gantt,
        x_start="Inicio",
        x_end="Fim",
        y="EtapaExibicao",
        color="Status",
        color_discrete_map=CORES_STATUS,
        hover_data={"Progresso": ":.0f", "Duracao": True, "Status": False},
    )
    fig.update_yaxes(autorange="reversed", title=None)
    fig.update_xaxes(title=None, gridcolor="rgba(148, 163, 184, 0.12)")
    fig.update_layout(
        height=max(300, min(600, 80 + len(gantt) * 42)),
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#eef3f8",
        legend_title_text="Status",
    )
    st.plotly_chart(fig, use_container_width=True, key="cronograma_gantt")


def _atalhos_fotos(df, obra_id):
    if not tem_permissao("evolucao"):
        return

    contagens = contagem_fotos_por_etapa(obra_id)
    st.markdown("### Registros fotográficos")
    for inicio in range(0, len(df), 3):
        colunas = st.columns(3)
        for coluna, (_, etapa) in zip(colunas, df.iloc[inicio:inicio + 3].iterrows()):
            nome = str(etapa["Etapa"])
            quantidade = contagens.get(nome, 0)
            with coluna:
                st.markdown(
                    f"""<div class="delta-stage-photo">
                        <strong>{nome}</strong>
                        <span>📸 {quantidade} foto(s)</span>
                    </div>""",
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Ver fotos da etapa",
                    key=f"cronograma_fotos_{etapa['ID']}",
                    use_container_width=True,
                ):
                    st.session_state["evolucao_etapa_pendente"] = nome
                    st.session_state["painel_aba_ativa"] = "evolucao"
                    st.rerun()


def tela_cronograma(obra_id, obra_nome):
    st.markdown("## Cronograma físico")
    st.caption(f"Planejamento e execução da obra {obra_nome}")

    df = carregar_cronograma(obra_id, obra_nome)
    if not df.empty:
        _resumo(df)
        st.markdown("### Planejamento")
        _gantt(df)
        st.markdown("### Etapas")
        _tabela(df)
        _atalhos_fotos(df, obra_id)
    else:
        st.info("Nenhuma etapa cadastrada para esta obra.")

    nova, editar = st.tabs(["Nova etapa", "Editar ou excluir"])
    with nova:
        _formulario_etapa(obra_id, obra_nome, df)

    with editar:
        if df.empty:
            st.caption("Cadastre uma etapa para habilitar a edição.")
            return

        nomes_por_id = {
            row["ID"]: f"{_inteiro(row['Ordem'], 0)}. {row['Etapa']}"
            for _, row in df.iterrows()
        }
        etapa_id = st.selectbox(
            "Selecionar etapa",
            list(nomes_por_id),
            format_func=lambda valor: nomes_por_id[valor],
            key="cronograma_etapa_edicao",
        )
        registro = df[df["ID"] == etapa_id].iloc[0].to_dict()
        _formulario_etapa(obra_id, obra_nome, df, registro)

        st.divider()
        confirmar = st.checkbox(
            "Confirmo a exclusão desta etapa",
            key=f"cronograma_confirmar_exclusao_{etapa_id}",
        )
        if st.button(
            "Excluir etapa",
            disabled=not confirmar,
            key=f"cronograma_excluir_{etapa_id}",
        ):
            excluir_etapa(etapa_id)
            sincronizar_calculos(obra_id, obra_nome)
            st.success("Etapa excluída.")
            st.rerun()
