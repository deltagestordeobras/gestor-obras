import streamlit as st
import pandas as pd
import json
from database.connection import get_connection


def tela_config():

    st.subheader("⚙️ Configurações do Sistema")

    abas = st.tabs([
        "🏗 Obra",
        "📊 Financeiro",
        "🏗 Etapas",
        "🔔 Alertas"
    ])

    # =====================================================
    # 🏗 CONFIG OBRA
    # =====================================================
    with abas[0]:

        st.subheader("🏗 Parâmetros da Obra")

        nome = st.text_input("Nome da Obra")
        metragem = st.number_input("Área (m²)", min_value=0.0)
        prazo = st.number_input("Prazo (dias)", min_value=0)

        if st.button("Salvar Configuração da Obra"):

            config = {
                "nome": nome,
                "metragem": metragem,
                "prazo": prazo
            }

            salvar_config("obra", config)
            st.success("Configuração salva!")

    # =====================================================
    # 📊 CONFIG FINANCEIRO
    # =====================================================
    with abas[1]:

        st.subheader("📊 Parâmetros Financeiros")

        margem = st.number_input("Margem de Lucro (%)", min_value=0.0)
        custo_m2 = st.number_input("Custo por m² (R$)", min_value=0.0)

        if st.button("Salvar Configuração Financeira"):

            config = {
                "margem": margem,
                "custo_m2": custo_m2
            }

            salvar_config("financeiro", config)
            st.success("Configuração salva!")

    # =====================================================
    # 🏗 ETAPAS PADRÃO
    # =====================================================
    with abas[2]:

        st.subheader("🏗 Etapas da Obra")

        etapas_padrao = st.text_area(
            "Etapas (uma por linha)",
            value="Fundação\nEstrutura\nAlvenaria\nAcabamento"
        )

        if st.button("Salvar Etapas"):

            lista = [e.strip() for e in etapas_padrao.split("\n") if e.strip()]

            salvar_config("etapas", lista)
            st.success("Etapas salvas!")

    # =====================================================
    # 🔔 ALERTAS
    # =====================================================
    with abas[3]:

        st.subheader("🔔 Regras de Alerta")

        limite_orcamento = st.slider("Alerta de estouro (%)", 50, 150, 100)
        dias_atraso = st.number_input("Dias para considerar atraso", min_value=0)

        if st.button("Salvar Alertas"):

            config = {
                "limite_orcamento": limite_orcamento,
                "dias_atraso": dias_atraso
            }

            salvar_config("alertas", config)
            st.success("Alertas configurados!")


# =====================================================
# 💾 SALVAR CONFIG
# =====================================================
def salvar_config(chave, valor):

    conn = get_connection()

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes (
                chave TEXT PRIMARY KEY,
                valor TEXT
            )
        """)

        conn.execute("""
            INSERT OR REPLACE INTO configuracoes (chave, valor)
            VALUES (?, ?)
        """, (chave, json.dumps(valor)))

        conn.commit()

    finally:
        conn.close()


# =====================================================
# 📥 CARREGAR CONFIG
# =====================================================
def carregar_config(chave):

    conn = get_connection()

    try:
        df = pd.read_sql(
            "SELECT valor FROM configuracoes WHERE chave = ?",
            conn,
            params=(chave,)
        )

        if df.empty:
            return None

        return json.loads(df.iloc[0]["valor"])

    finally:
        conn.close()