import pandas as pd
import streamlit as st

from app.relatorios import gerar_pdf_financeiro
from app.ui_utils import data_br as _data, moeda as _moeda, texto as _texto
from services.extrato_financeiro import preparar_extrato
from services.permissoes import tem_permissao
from services.status import STATUS_PAGO, STATUS_PENDENTE
from services.cronograma import resumo_cronograma
from services.evolucao import ultima_evolucao
from services.diario_obra import ultimo_diario


def _serie_datas(df, coluna):
    if coluna not in df.columns:
        return pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
    return pd.to_datetime(df[coluna], errors="coerce")


def _card_operacional(icone, titulo, valor, subtitulo, tom="azul"):
    st.markdown(
        f'''<div class="delta-kpi delta-kpi--{tom}">
            <div class="delta-kpi__top"><span class="delta-kpi__icon">{icone}</span>
            <span class="delta-kpi__label">{_texto(titulo)}</span></div>
            <div class="delta-kpi__value">{_texto(valor)}</div>
            <div class="delta-kpi__sub">{_texto(subtitulo)}</div>
        </div>''',
        unsafe_allow_html=True,
    )


def _alerta(icone, titulo, descricao, tipo="alerta"):
    st.markdown(
        f'''<div class="delta-message delta-message--{tipo}">
            <span class="delta-message__icon">{icone}</span><div>
            <div class="delta-message__title">{_texto(titulo)}</div>
            <div class="delta-message__description">{_texto(descricao)}</div></div>
        </div>''',
        unsafe_allow_html=True,
    )


def _ir_para_aba(aba):
    st.session_state["painel_aba_ativa"] = aba
    st.rerun()


def _orcamento_existente(obra):
    orcamento = st.session_state.get("ultimo_orcamento")
    return (
        isinstance(orcamento, dict)
        and str(orcamento.get("obra", "")) == str(obra)
    )


def tela_painel(df_obra, obra_selecionada, obra_id=None):
    df = preparar_extrato(df_obra.copy()) if df_obra is not None and not df_obra.empty else pd.DataFrame()
    hoje = pd.Timestamp.today().normalize()

    pagos = df[df["StatusNormalizado"] == STATUS_PAGO] if not df.empty else df
    pendentes = df[df["StatusNormalizado"] == STATUS_PENDENTE] if not df.empty else df
    total_pago = abs(pagos[pagos["Valor"] < 0]["Valor"].sum()) if not pagos.empty else 0
    total_pendente = abs(pendentes[pendentes["Valor"] < 0]["Valor"].sum()) if not pendentes.empty else 0
    saldo = df["Valor"].sum() if not df.empty else 0
    compromissos = total_pago + total_pendente
    andamento = min(100.0, total_pago / compromissos * 100) if compromissos > 0 else 0.0
    status_obra = "Em andamento" if andamento < 100 else "Concluída"

    vencimentos = _serie_datas(pendentes, "Data Vencimento")
    proximos = pendentes[vencimentos >= hoje].copy() if not pendentes.empty else pd.DataFrame()
    if not proximos.empty:
        proximos["_vencimento"] = pd.to_datetime(proximos["Data Vencimento"], errors="coerce")
        proximo = proximos.sort_values("_vencimento").iloc[0]
        proximo_valor = _data(proximo["_vencimento"])
        proximo_subtitulo = f"{proximo.get('Fornecedor', 'Pagamento')} · {_moeda(abs(proximo.get('Valor', 0)))}"
    else:
        proximo_valor = "Sem vencimentos"
        proximo_subtitulo = "Nenhum compromisso futuro"

    datas_referencia = _serie_datas(df, "Entrada Nota")
    recentes = df.assign(_data=datas_referencia).sort_values("_data", ascending=False, na_position="last") if not df.empty else df
    if not recentes.empty:
        ultima = recentes.iloc[0]
        ultima_valor = _data(ultima.get("_data"))
        ultima_subtitulo = f"{ultima.get('Fornecedor', 'Lançamento')} · {_moeda(abs(ultima.get('Valor', 0)))}"
    else:
        ultima_valor = "Sem lançamentos"
        ultima_subtitulo = "A obra ainda não possui movimentações"

    nome_obra = str(df["Obra"].dropna().iloc[0]) if not df.empty and "Obra" in df.columns and not df["Obra"].dropna().empty else str(obra_selecionada or "Obra selecionada")
    header, acoes = st.columns([5.5, 2.5], vertical_alignment="center")
    with header:
        st.markdown(
            f'''<div class="delta-header"><div class="delta-header__eyebrow">Visão operacional</div>
                <div class="delta-header__row"><h1>{_texto(nome_obra)}</h1><span class="delta-status">{status_obra}</span></div>
                <div class="delta-header__progress-row"><span>Andamento geral</span><strong>{andamento:.0f}%</strong></div>
                <div class="delta-progress"><span style="width:{andamento:.1f}%"></span></div></div>''',
            unsafe_allow_html=True,
        )
    with acoes:
        nova, notas = st.columns(2)
        with nova:
            if st.button("Nova nota", type="primary", width="stretch", key="geral_nova_nota"):
                st.session_state["notas_modo"] = "cadastro"
                _ir_para_aba("lancamentos")
        with notas:
            if st.button("Ver notas", width="stretch", key="geral_ver_notas"):
                st.session_state["notas_modo"] = "listar"
                _ir_para_aba("lancamentos")
        pode_ver_orcamento = tem_permissao("orcamento") and _orcamento_existente(obra_selecionada)
        relatorio, orcamento = st.columns(2) if pode_ver_orcamento else (st.container(), None)
        with relatorio:
            if st.button("Gerar relatório", width="stretch", key="geral_gerar_relatorio"):
                st.session_state["geral_mostrar_relatorio"] = True
        if orcamento is not None:
            with orcamento:
                if st.button("Ver orçamento", width="stretch", key="geral_ver_orcamento"):
                    st.session_state["orcamento_modo"] = "visualizar"
                    st.session_state["menu_principal_pendente"] = "📐 Orçamento da Obra"
                    st.rerun()

    if st.session_state.get("geral_mostrar_relatorio"):
        gerar_pdf_financeiro(df, nome_obra)

    st.markdown('<div class="delta-section-title">Rotina da obra</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _card_operacional("✓", "Total pago", _moeda(total_pago), "Despesas realizadas", "verde")
    with c2:
        _card_operacional("!", "Pendências", str(len(pendentes)), f"{_moeda(total_pendente)} aguardando pagamento", "amarelo")
    with c3:
        _card_operacional("◷", "Próximo vencimento", proximo_valor, proximo_subtitulo, "azul")
    with c4:
        _card_operacional("↗", "Última nota lançada", ultima_valor, ultima_subtitulo, "azul")

    fisico = resumo_cronograma(obra_id, obra_selecionada)
    termino_fisico = _data(fisico["termino"], "Sem previsão")
    st.markdown('<div class="delta-section-title">Resumo físico</div>', unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        _card_operacional("▰", "Execução física", f"{fisico['execucao']:.0f}%", "Progresso ponderado por duração", "verde")
    with f2:
        _card_operacional("!", "Etapas atrasadas", str(fisico["atrasadas"]), "Itens fora da previsão", "vermelho" if fisico["atrasadas"] else "verde")
    with f3:
        _card_operacional("→", "Próxima etapa", fisico["proxima_etapa"], "Próximo item do planejamento", "azul")
    with f4:
        _card_operacional("◷", "Previsão de término", termino_fisico, "Data calculada pelo cronograma", "azul")

    if tem_permissao("evolucao"):
        evolucao = ultima_evolucao(obra_id)
        st.markdown('<div class="delta-section-title">Última evolução da obra</div>', unsafe_allow_html=True)
        card_evolucao, acao_evolucao = st.columns([6.5, 1.5], vertical_alignment="center")
        with card_evolucao:
            if evolucao:
                st.markdown(
                    f"""<div class="delta-evolution-summary">
                        <span>{_texto(_data(evolucao["Data"]))} · {_texto(evolucao["Etapa"])}</span>
                        <strong>{_texto(evolucao["Titulo"])}</strong>
                        <small>📸 {int(evolucao["Quantidade"])} foto(s) registradas</small>
                    </div>""",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """<div class="delta-evolution-summary">
                        <span>Registro fotográfico</span>
                        <strong>Nenhuma evolução registrada</strong>
                        <small>A obra ainda não possui fotos de execução.</small>
                    </div>""",
                    unsafe_allow_html=True,
                )
        with acao_evolucao:
            if st.button("Ver evolução", key="geral_ver_evolucao", use_container_width=True):
                _ir_para_aba("evolucao")

    if tem_permissao("diario_obra"):
        diario = ultimo_diario(obra_id)
        st.markdown('<div class="delta-section-title">Último diário de obra</div>', unsafe_allow_html=True)
        card_diario, acao_diario = st.columns([6.5, 1.5], vertical_alignment="center")
        with card_diario:
            if diario:
                servico = str(diario.get("ServicosExecutados") or "Sem serviço informado")
                equipe = str(diario.get("Equipe") or "Equipe não informada")
                st.markdown(
                    f"""<div class="delta-evolution-summary">
                        <span>{_texto(_data(diario["Data"]))} · {_texto(diario["Etapa"])}</span>
                        <strong>{_texto(servico[:120])}</strong>
                        <small>Equipe: {_texto(equipe)}</small>
                    </div>""",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """<div class="delta-evolution-summary">
                        <span>Registro diário</span>
                        <strong>Nenhum diário registrado</strong>
                        <small>A obra ainda não possui registros diários.</small>
                    </div>""",
                    unsafe_allow_html=True,
                )
        with acao_diario:
            if st.button("Ver diário", key="geral_ver_diario", use_container_width=True):
                _ir_para_aba("diario_obra")

    st.markdown('<div class="delta-section-title">Situação rápida</div>', unsafe_allow_html=True)
    resumo, alertas = st.columns([1.2, 2.8])
    with resumo:
        st.markdown(
            f'''<div class="delta-ops-summary"><span>Saldo atual</span>
                <strong class="{'delta-negative' if saldo < 0 else ''}">{_texto(_moeda(saldo))}</strong>
                <small>Resumo simples da disponibilidade da obra</small></div>''',
            unsafe_allow_html=True,
        )
    with alertas:
        vencidos = pendentes[vencimentos < hoje] if not pendentes.empty else pd.DataFrame()
        alertas_lista = []
        if not vencidos.empty:
            alertas_lista.append(("!", "Contas vencidas", f"{len(vencidos)} pagamento(s) precisam de atenção.", "critico"))
        if total_pendente > max(saldo, 0):
            alertas_lista.append(("◷", "Saldo abaixo das pendências", "O saldo atual não cobre os compromissos pendentes.", "alerta"))
        if not alertas_lista:
            alertas_lista.append(("✓", "Operação em dia", "Nenhum alerta operacional crítico no momento.", "sucesso"))
        colunas_alerta = st.columns(len(alertas_lista))
        for indice, alerta_item in enumerate(alertas_lista):
            with colunas_alerta[indice]:
                _alerta(*alerta_item)

    st.markdown('<div class="delta-section-title">Últimas movimentações</div>', unsafe_allow_html=True)
    if recentes.empty:
        st.info("Nenhum lançamento registrado para esta obra.")
        return

    tabela = recentes.head(6).copy()
    tabela["Data"] = tabela["_data"].apply(_data)
    tabela["Fornecedor"] = tabela.get("Fornecedor", "").fillna("").replace("", "Não informado")
    tabela["Valor"] = tabela["Valor"].abs()
    colunas = [coluna for coluna in ["Data", "Fornecedor", "Etapa", "Valor", "Status"] if coluna in tabela.columns]
    st.dataframe(
        tabela[colunas],
        hide_index=True,
        width="stretch",
        column_config={"Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f")},
    )
