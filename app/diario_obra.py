import calendar
import re

import pandas as pd
import streamlit as st

from app.ui_utils import texto as _texto
from services.cronograma import carregar_cronograma
from services.diario_obra import (
    carregar_diarios,
    excluir_diario,
    obter_diario,
    salvar_diario,
)
from services.listas import listar_etapas_ativas


CLIMAS = ["Ensolarado", "Parcialmente nublado", "Nublado", "Chuva", "Chuva intensa"]
MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

def _resumo(texto, limite=48):
    limpo = " ".join(str(texto or "").split())
    return limpo if len(limpo) <= limite else limpo[:limite - 1] + "…"


def _quantidade_equipe(equipe):
    numeros = re.findall(r"\d+", str(equipe or ""))
    return int(numeros[0]) if numeros else 0


def _etapas_disponiveis(obra_id, obra_nome, incluir=None):
    cronograma = carregar_cronograma(obra_id, obra_nome)
    etapas_cronograma = (
        cronograma["Etapa"].dropna().astype(str).drop_duplicates().tolist()
        if not cronograma.empty else []
    )
    etapas = etapas_cronograma + [
        etapa for etapa in listar_etapas_ativas(incluir=incluir)
        if etapa not in etapas_cronograma
    ]
    return etapas, set(etapas_cronograma)


def _calendario(obra_id, ano, mes):
    inicio = pd.Timestamp(ano, mes, 1)
    fim = inicio + pd.offsets.MonthEnd(1)
    diarios = carregar_diarios(obra_id, inicio, fim)
    por_dia = {}
    if not diarios.empty:
        diarios["_dia"] = pd.to_datetime(diarios["Data"], errors="coerce").dt.day
        por_dia = {int(dia): grupo for dia, grupo in diarios.groupby("_dia")}

    st.markdown(f"### {MESES[mes - 1]} {ano}")
    cabecalho = st.columns(7)
    for coluna, nome in zip(cabecalho, ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]):
        coluna.markdown(f"**{nome}**")

    for semana in calendar.monthcalendar(ano, mes):
        colunas = st.columns(7)
        for coluna, dia in zip(colunas, semana):
            with coluna:
                if dia == 0:
                    st.markdown("&nbsp;", unsafe_allow_html=True)
                    continue
                grupo = por_dia.get(dia)
                if st.button(str(dia), key=f"diario_dia_{ano}_{mes}_{dia}", use_container_width=True):
                    st.session_state["diario_data_selecionada"] = pd.Timestamp(ano, mes, dia).date()
                    st.rerun()
                if grupo is not None:
                    primeiro = grupo.iloc[0]
                    pessoas = sum(_quantidade_equipe(v) for v in grupo["Equipe"])
                    fotos = int(grupo["QuantidadeFotos"].sum())
                    st.caption(
                        f"{pessoas} pessoa(s) · {_resumo(primeiro['Etapa'], 18)}\n\n"
                        f"{_resumo(primeiro['ServicosExecutados'], 30)} · 📸 {fotos}"
                    )


def _visualizar_diarios(diarios):
    for _, diario in diarios.iterrows():
        with st.container(border=True):
            st.markdown(
                f"""<div class="delta-evolution-head">
                    <span class="delta-badge">{_texto(diario["Etapa"])}</span>
                    <h3>{_texto(_resumo(diario["ServicosExecutados"], 100))}</h3>
                    <p><b>Clima:</b> {_texto(diario["Clima"])} · <b>Responsável:</b> {_texto(diario["Responsavel"])}</p>
                    <p><b>Equipe:</b> {_texto(diario["Equipe"])}</p>
                    <p><b>Ocorrências:</b> {_texto(diario["Ocorrencias"] or "Nenhuma")}</p>
                    <p><b>Observações:</b> {_texto(diario["Observacoes"] or "Nenhuma")}</p>
                    <small>Progresso informado: {float(diario["ProgressoEtapa"] or 0):.0f}% · 📸 {int(diario["QuantidadeFotos"] or 0)} foto(s)</small>
                </div>""",
                unsafe_allow_html=True,
            )


def _formulario(obra_id, obra_nome, data, registro=None):
    editando = registro is not None
    diario_id = registro.get("ID") if editando else None
    etapa_atual = registro.get("Etapa") if editando else None
    etapas, etapas_cronograma = _etapas_disponiveis(obra_id, obra_nome, [etapa_atual] if etapa_atual else None)
    prefixo = diario_id or data.isoformat()

    with st.form(f"form_diario_{prefixo}"):
        c1, c2, c3 = st.columns([1, 1.4, 1.2])
        with c1:
            data_diario = st.date_input("Data", value=pd.Timestamp(registro.get("Data")).date() if editando else data)
            clima = st.selectbox(
                "Clima", CLIMAS,
                index=CLIMAS.index(registro.get("Clima")) if editando and registro.get("Clima") in CLIMAS else 0,
            )
        with c2:
            etapa = st.selectbox(
                "Etapa da obra", etapas,
                index=etapas.index(etapa_atual) if etapa_atual in etapas else 0,
            )
            responsavel = st.text_input(
                "Responsável",
                value=str(registro.get("Responsavel") or st.session_state.get("usuario", "")) if editando else str(st.session_state.get("usuario", "")),
            )
        with c3:
            equipe = st.text_input("Equipe", value=str(registro.get("Equipe") or "") if editando else "", placeholder="Ex.: 6 pessoas")
            progresso = st.slider(
                "Progresso da etapa",
                0, 100,
                value=int(float(registro.get("ProgressoEtapa") or 0)) if editando else 0,
                format="%d%%",
            )

        servicos = st.text_area("Serviços executados", value=str(registro.get("ServicosExecutados") or "") if editando else "")
        ocorrencias = st.text_area("Ocorrências", value=str(registro.get("Ocorrencias") or "") if editando else "")
        observacoes = st.text_area("Observações", value=str(registro.get("Observacoes") or "") if editando else "")
        fotos = st.file_uploader(
            "Fotos", type=["jpg", "jpeg", "png"], accept_multiple_files=True,
            help="JPG, JPEG ou PNG. Limite de 10 MB por arquivo.",
        )
        atualizar = st.checkbox(
            "Atualizar progresso no Cronograma",
            value=bool(registro.get("AtualizarCronograma")) if editando else False,
        )
        publicar = st.checkbox(
            "Publicar fotos na Evolução",
            value=bool(registro.get("CriarEvolucao")) if editando else True,
        )
        etapa_ausente = atualizar and etapa not in etapas_cronograma
        confirmar_sem_cronograma = False
        if etapa_ausente:
            st.warning("Esta etapa ainda não existe no cronograma. Deseja apenas salvar o diário sem atualizar o cronograma?")
            confirmar_sem_cronograma = st.checkbox("Salvar diário sem atualizar o Cronograma")

        enviar = st.form_submit_button(
            "Salvar alterações" if editando else "Salvar diário",
            type="primary", use_container_width=True,
        )

    if not enviar:
        return
    if not servicos.strip() or not responsavel.strip() or not equipe.strip():
        st.error("Preencha responsável, equipe e serviços executados.")
        return
    if etapa_ausente and not confirmar_sem_cronograma:
        st.error("Confirme o salvamento sem atualização do Cronograma.")
        return

    ok, avisos, _ = salvar_diario({
        "ID": diario_id,
        "ObraID": obra_id,
        "Obra": obra_nome,
        "Data": data_diario,
        "Etapa": etapa,
        "Clima": clima,
        "Responsavel": responsavel,
        "Equipe": equipe,
        "ServicosExecutados": servicos,
        "Ocorrencias": ocorrencias,
        "Observacoes": observacoes,
        "ProgressoEtapa": progresso,
        "AtualizarCronograma": atualizar and not etapa_ausente,
        "CriarEvolucao": publicar,
    }, fotos)
    if ok:
        st.success("Diário atualizado." if editando else "Diário registrado.")
        for aviso in avisos:
            st.warning(aviso)
        st.rerun()


def tela_diario_obra(obra_id, obra_nome):
    admin = str(st.session_state.get("perfil", "")).upper() == "ADMIN"
    st.markdown("## Diário de Obra")
    st.caption(f"Registro diário da execução de {obra_nome}")

    hoje = pd.Timestamp.today()
    navegacao = st.columns([1, 1, 1, 4])
    with navegacao[0]:
        mes = st.selectbox("Mês", range(1, 13), index=hoje.month - 1, format_func=lambda valor: MESES[valor - 1])
    with navegacao[1]:
        ano = st.number_input("Ano", min_value=2000, max_value=2100, value=hoje.year, step=1)
    with navegacao[2]:
        if st.button("Hoje", use_container_width=True):
            st.session_state["diario_data_selecionada"] = hoje.date()
            st.rerun()

    _calendario(obra_id, int(ano), int(mes))
    data = st.session_state.get("diario_data_selecionada", hoje.date())
    st.divider()
    st.markdown(f"### Diário de {pd.Timestamp(data).strftime('%d/%m/%Y')}")
    diarios_dia = carregar_diarios(obra_id, data, data)

    if not admin:
        if diarios_dia.empty:
            st.info("Nenhum diário registrado nesta data.")
        else:
            _visualizar_diarios(diarios_dia)
        return

    opcoes = ["Novo diário"] + diarios_dia["ID"].tolist() if not diarios_dia.empty else ["Novo diário"]
    selecionado = st.selectbox(
        "Registro",
        opcoes,
        format_func=lambda valor: "Novo diário" if valor == "Novo diário" else _resumo(obter_diario(valor, obra_id).get("ServicosExecutados"), 60),
    )
    registro = obter_diario(selecionado, obra_id) if selecionado != "Novo diário" else None
    _formulario(obra_id, obra_nome, data, registro)

    if registro:
        st.divider()
        remover_fotos = st.checkbox("Remover também as fotos publicadas na Evolução", key=f"diario_remover_fotos_{registro['ID']}")
        confirmar = st.checkbox("Confirmo a exclusão do diário", key=f"diario_confirmar_exclusao_{registro['ID']}")
        if st.button("Excluir diário", disabled=not confirmar, key=f"diario_excluir_{registro['ID']}"):
            excluir_diario(registro["ID"], obra_id, remover_fotos)
            st.success("Diário excluído.")
            st.rerun()
