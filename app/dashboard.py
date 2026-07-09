import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.relatorios import gerar_pdf_financeiro
from app.ui_utils import moeda as _moeda, texto as _texto
from services.inteligencia import calcular_risco_obra, gerar_alertas, gerar_sugestoes
from services.status import STATUS_PAGO, STATUS_PENDENTE, preparar_valor_status


CORES = {
    "verde": "#37d67a", "vermelho": "#ff6376", "amarelo": "#f5c451",
    "azul": "#62a8ff", "texto": "#eef3f8", "muted": "#92a0b2",
    "grid": "rgba(148, 163, 184, 0.12)",
}

def _card_kpi(icone, titulo, valor, subtitulo, tom="azul"):
    st.markdown(f'''<div class="delta-kpi delta-kpi--{tom}">
        <div class="delta-kpi__top"><span class="delta-kpi__icon">{icone}</span><span class="delta-kpi__label">{_texto(titulo)}</span></div>
        <div class="delta-kpi__value">{_texto(valor)}</div><div class="delta-kpi__sub">{_texto(subtitulo)}</div>
    </div>''', unsafe_allow_html=True)


def _card_mensagem(icone, titulo, descricao, tipo="alerta"):
    st.markdown(f'''<div class="delta-message delta-message--{tipo}">
        <span class="delta-message__icon">{icone}</span><div><div class="delta-message__title">{_texto(titulo)}</div>
        <div class="delta-message__description">{_texto(descricao)}</div></div>
    </div>''', unsafe_allow_html=True)


def _estilo_grafico(fig, altura=290):
    fig.update_layout(
        height=altura, margin=dict(l=18, r=18, t=46, b=18),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=CORES["texto"], family="Inter, Arial, sans-serif", size=12),
        title=dict(font=dict(size=15, color=CORES["texto"]), x=0.02, xanchor="left"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(bgcolor="#151d28", font_color=CORES["texto"]),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, color=CORES["muted"])
    fig.update_yaxes(gridcolor=CORES["grid"], zeroline=False, color=CORES["muted"])
    return fig


def _nome_obra(df=None):
    if df is not None and "Obra" in df.columns and not df["Obra"].dropna().empty:
        return df["Obra"].dropna().iloc[0]

    return st.session_state.get("obra_nome") or st.session_state.get("obra") or "Obra selecionada"


def tela_dashboard(df, key_prefix="dashboard"):
    if df is None or df.empty:
        st.markdown("## Dashboard Financeiro")
        st.info("Sem dados financeiros para esta obra.")
        return

    df = preparar_valor_status(df.copy())
    hoje = pd.Timestamp.today().normalize()
    df_pago = df[df["StatusNormalizado"] == STATUS_PAGO]
    df_pendente = df[df["StatusNormalizado"] == STATUS_PENDENTE]

    entradas = df[df["Valor"] > 0]["Valor"].sum()
    saidas_pagas = abs(df_pago[df_pago["Valor"] < 0]["Valor"].sum())
    saidas_pendentes = abs(df_pendente[df_pendente["Valor"] < 0]["Valor"].sum())
    saldo = df["Valor"].sum()
    aporte = entradas
    if {"Tipo", "Categoria"}.issubset(df.columns):
        aporte_filtrado = df[(df["Tipo"] == "Entrada (Recebido)") & (df["Categoria"] == "Aporte de Capital")]["Valor"].sum()
        if aporte_filtrado > 0:
            aporte = aporte_filtrado

    andamento = min(100.0, (saidas_pagas / aporte * 100)) if aporte > 0 else 0.0
    score, _ = calcular_risco_obra(df)
    if score > 70:
        risco, badge_classe = "Baixo", "baixo"
    elif score > 40:
        risco, badge_classe = "Médio", "medio"
    elif score > 20:
        risco, badge_classe = "Alto", "alto"
    else:
        risco, badge_classe = "Crítico", "critico"
    status_obra = "Em andamento" if andamento < 100 else "Concluída"

    header_left, header_report, header_note = st.columns([6, 1.35, 1.15], vertical_alignment="center")
    with header_left:
        st.markdown(f'''<div class="delta-header"><div class="delta-header__eyebrow">Dashboard Financeiro</div>
            <div class="delta-header__row"><h1>{_texto(_nome_obra(df))}</h1><span class="delta-status">{status_obra}</span></div>
            <div class="delta-header__progress-row"><span>Andamento financeiro</span><strong>{andamento:.0f}%</strong></div>
            <div class="delta-progress"><span style="width:{andamento:.1f}%"></span></div></div>''', unsafe_allow_html=True)
    with header_report:
        if st.button("Gerar relatório", width="stretch", key=f"{key_prefix}_gerar_relatorio"):
            st.session_state[f"{key_prefix}_mostrar_relatorio"] = True
    with header_note:
        if st.button("Nova nota", type="primary", width="stretch", key=f"{key_prefix}_nova_nota"):
            st.session_state["notas_modo"] = "cadastro"
            st.session_state["painel_aba_ativa"] = "lancamentos"
            st.rerun()

    if st.session_state.get(f"{key_prefix}_mostrar_relatorio"):
        st.markdown(
            '<div class="delta-section-title">Relatório financeiro pronto</div>',
            unsafe_allow_html=True,
        )
        gerar_pdf_financeiro(df, _nome_obra(df))

    st.markdown('<div class="delta-section-title">Resumo financeiro</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: _card_kpi("↗", "Aporte", _moeda(aporte), "Capital registrado", "verde")
    with c2: _card_kpi("✓", "Pago", _moeda(saidas_pagas), "Despesas realizadas", "azul")
    with c3: _card_kpi("◷", "Pendente", _moeda(saidas_pendentes), "Compromissos futuros", "amarelo")
    with c4: _card_kpi("$", "Saldo", _moeda(saldo), "Disponibilidade atual", "verde" if saldo >= 0 else "vermelho")

    st.markdown('<div class="delta-section-title">Visão do investidor</div>', unsafe_allow_html=True)
    st.markdown(f'''<div class="delta-investor"><div class="delta-investor__head">
        <div><span class="delta-investor__eyebrow">Saúde financeira consolidada</span><h3>Controle e previsibilidade da obra</h3></div>
        <span class="delta-badge delta-badge--{badge_classe}">{risco}</span></div>
        <div class="delta-investor__metrics"><div><span>Saldo</span><strong>{_moeda(saldo)}</strong></div>
        <div><span>Risco</span><strong>{risco}</strong></div><div><span>Andamento</span><strong>{andamento:.0f}%</strong></div>
        <div><span>Score</span><strong>{score}/100</strong></div></div>
        <div class="delta-score-label"><span>Score financeiro</span><strong>{score}%</strong></div>
        <div class="delta-progress delta-progress--score"><span style="width:{score}%"></span></div></div>''', unsafe_allow_html=True)

    st.markdown('<div class="delta-section-title">Análise financeira</div>', unsafe_allow_html=True)
    chart_left, chart_right = st.columns(2)
    fluxo = pd.DataFrame({"Tipo": ["Entradas", "Pago", "Pendente"], "Valor": [entradas, saidas_pagas, saidas_pendentes],
                          "Cor": [CORES["verde"], CORES["azul"], CORES["amarelo"]]})
    fig_fluxo = go.Figure(go.Bar(x=fluxo["Tipo"], y=fluxo["Valor"], marker_color=fluxo["Cor"],
        text=[_moeda(v) for v in fluxo["Valor"]], textposition="outside", hovertemplate="%{x}<br>R$ %{y:,.2f}<extra></extra>"))
    fig_fluxo.update_layout(title="Fluxo Financeiro", showlegend=False)
    _estilo_grafico(fig_fluxo)
    with chart_left: st.plotly_chart(fig_fluxo, width="stretch", key=f"{key_prefix}_fluxo")

    etapa = pd.DataFrame()
    if "Etapa" in df.columns:
        etapa = df[df["Valor"] < 0].groupby("Etapa", dropna=False)["Valor"].sum().abs().sort_values(ascending=False).reset_index()
        etapa["Etapa"] = etapa["Etapa"].fillna("Sem etapa")
        etapa = etapa[etapa["Valor"] > 0]
    with chart_right:
        if len(etapa) == 1:
            nome_etapa, valor_etapa = etapa.iloc[0]["Etapa"], etapa.iloc[0]["Valor"]
            st.markdown(f'''<div class="delta-stage-card"><span class="delta-stage-card__icon">▰</span>
                <span class="delta-stage-card__percent">100%</span><h3>dos gastos estão em {_texto(nome_etapa)}</h3>
                <p>{_moeda(valor_etapa)} concentrados nesta etapa.</p><div class="delta-progress"><span style="width:100%"></span></div></div>''', unsafe_allow_html=True)
        elif not etapa.empty:
            fig_etapa = go.Figure(go.Pie(labels=etapa["Etapa"], values=etapa["Valor"], hole=0.62, textinfo="percent",
                hovertemplate="%{label}<br>R$ %{value:,.2f}<extra></extra>", marker=dict(colors=["#62a8ff", "#37d67a", "#f5c451", "#ff6376", "#9b8cff", "#55d6be"])))
            fig_etapa.update_layout(title="Custo por Etapa")
            _estilo_grafico(fig_etapa)
            st.plotly_chart(fig_etapa, width="stretch", key=f"{key_prefix}_etapa")
        else:
            st.markdown('<div class="delta-empty">Sem gastos classificados por etapa.</div>', unsafe_allow_html=True)

    if "Fornecedor" in df.columns:
        fornecedores = df[df["Valor"] < 0].groupby("Fornecedor", dropna=False)["Valor"].sum().abs().sort_values(ascending=True).tail(10).reset_index()
        fornecedores["Fornecedor"] = fornecedores["Fornecedor"].fillna("Não informado")
        fornecedores = fornecedores[fornecedores["Valor"] > 0]
        if not fornecedores.empty:
            fig_fornecedor = go.Figure(go.Bar(x=fornecedores["Valor"], y=fornecedores["Fornecedor"], orientation="h",
                marker_color=CORES["azul"], hovertemplate="%{y}<br>R$ %{x:,.2f}<extra></extra>"))
            fig_fornecedor.update_layout(title="Gasto por Fornecedor", showlegend=False)
            _estilo_grafico(fig_fornecedor, altura=280)
            st.plotly_chart(fig_fornecedor, width="stretch", key=f"{key_prefix}_fornecedor")

    contas_vencidas = pd.DataFrame()
    if "Data Vencimento" in df.columns:
        vencimentos = pd.to_datetime(df["Data Vencimento"], errors="coerce")
        contas_vencidas = df[(df["StatusNormalizado"] == STATUS_PENDENTE) & (vencimentos < hoje)]
    alertas_cards = []
    if not contas_vencidas.empty: alertas_cards.append(("🚨", "Contas vencidas", "Existem pagamentos em atraso.", "critico"))
    if saidas_pendentes > max(saldo, 0): alertas_cards.append(("⚠", "Saldo insuficiente", "O saldo atual não cobre despesas futuras.", "alerta"))
    if saldo < 0: alertas_cards.append(("↓", "Saldo negativo", "A obra apresenta resultado financeiro negativo.", "critico"))
    if gerar_alertas(df) and not alertas_cards: alertas_cards.append(("!", "Atenção financeira", "Revise os lançamentos e compromissos da obra.", "alerta"))

    st.markdown('<div class="delta-section-title">Alertas inteligentes</div>', unsafe_allow_html=True)
    if alertas_cards:
        cols_alerta = st.columns(min(3, len(alertas_cards)))
        for index, alerta in enumerate(alertas_cards):
            with cols_alerta[index % len(cols_alerta)]: _card_mensagem(*alerta)
    else: _card_mensagem("✓", "Operação saudável", "Nenhum problema crítico detectado.", "sucesso")

    sugestoes = gerar_sugestoes(df)
    st.markdown('<div class="delta-section-title">Sugestões inteligentes</div>', unsafe_allow_html=True)
    if sugestoes:
        cols_sugestao = st.columns(min(3, len(sugestoes)))
        for index, sugestao in enumerate(sugestoes):
            titulo = str(sugestao).replace("Reduzir custos na etapa:", "Reduzir custos na etapa").strip()
            with cols_sugestao[index % len(cols_sugestao)]:
                _card_mensagem("💡", titulo, "Revise fornecedores e compare preços dos principais insumos.", "recomendacao")
    else: _card_mensagem("💡", "Acompanhar evolução financeira", "Mantenha lançamentos e vencimentos atualizados.", "recomendacao")



