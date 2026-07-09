import streamlit as st

# TELAS
from app.painel import tela_painel
from app.lancamentos import tela_lancamentos, tela_erp_lancamento
from app.materiais import tela_materiais
from app.dashboard import tela_dashboard
from app.administracao import tela_administracao
from app.configuracoes import tela_configuracoes

# SERVICES
from services.lancamento import carregar_lancamentos


def render_painel(obra_selecionada, perfil):

    df_obra = carregar_lancamentos(obra_selecionada)

    # =========================
    # 🧭 ABAS DINÂMICAS
    # =========================
    abas = [
        "📊 Visão Geral",
        "📑 Lançamentos",
        "📦 Materiais",
        "🧾 ERP",
        "📈 Dashboard"
    ]

    # ADMIN vê tudo
    if perfil == "ADMIN":
        abas += ["⚙️ Administração", "🔧 Configurações"]

    tabs = st.tabs(abas)

    # =========================
    # 📊 VISÃO GERAL
    # =========================
    with tabs[0]:
        tela_painel(df_obra, obra_selecionada)

    # =========================
    # 📑 LANÇAMENTOS
    # =========================
    with tabs[1]:
        tela_lancamentos(obra_selecionada)

    # =========================
    # 📦 MATERIAIS (RELATÓRIO)
    # =========================
    with tabs[2]:
        tela_materiais(obra_selecionada)

    # =========================
    # 🧾 ERP (LANÇAMENTO + ITENS)
    # =========================
    with tabs[3]:
        tela_erp_lancamento(obra_selecionada)

    # =========================
    # 📈 DASHBOARD
    # =========================
    with tabs[4]:
        tela_dashboard(df_obra)

    # =========================
    # ⚙️ ADMIN
    # =========================
    if perfil == "ADMIN":
        with tabs[5]:
            tela_administracao(obra_selecionada)

        with tabs[6]:
            tela_configuracoes()