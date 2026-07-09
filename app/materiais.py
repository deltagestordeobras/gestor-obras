

import pandas as pd
import streamlit as st

from services.insumos import carregar_insumos
from services.lancamento import carregar_lancamentos


def tela_materiais(obra_selecionada):

    st.subheader("📦 Gestão de Materiais da Obra")

    # ===============================
    # 📊 DADOS
    # ===============================
    df = carregar_insumos(obra_selecionada)

    if df.empty:
        st.info("Nenhum material cadastrado.")
        return

    df["ValorTotal"] = pd.to_numeric(df["ValorTotal"], errors="coerce")

    # ===============================
    # 📊 CUSTO POR ETAPA
    # ===============================
    st.subheader("📊 Custos por Etapa")

    resumo = (
        df.groupby("Etapa")["ValorTotal"]
        .sum()
        .sort_values(ascending=False)
    )

    for etapa, valor in resumo.items():
        st.markdown(f"**{etapa}** — R$ {valor:,.2f}")

    st.divider()

    # ===============================
    # 💰 TOTAL GERAL
    # ===============================
    total_geral = df["ValorTotal"].sum()
    st.success(f"💰 Total Geral: R$ {total_geral:,.2f}")

    st.divider()

    # ===============================
    # 📄 AUDITORIA POR NOTA
    # ===============================
    st.subheader("🔎 Auditoria por Nota")

    df_notas = carregar_lancamentos(obra_selecionada)

    if not df_notas.empty:
        df_notas["Valor"] = pd.to_numeric(df_notas["Valor"], errors="coerce")

    notas = df["NotaID"].dropna().unique()

    if len(notas) > 0:

        # 🔥 MELHOR UX (nome + valor)
        lista_notas = df_notas[df_notas["ID"].isin(notas)].to_dict("records")

        nota_sel = st.selectbox(
            "Selecione a Nota",
            lista_notas,
            format_func=lambda x: f"{x['Descrição']} | R$ {abs(x['Valor']):,.2f}"
        )

        nota_id = nota_sel["ID"]

        df_nota = df[df["NotaID"] == nota_id]
        total_materiais = df_nota["ValorTotal"].sum()

        valor_nota = abs(nota_sel["Valor"])
        diferenca = valor_nota - total_materiais

        st.write(f"📄 Nota: R$ {valor_nota:,.2f}")
        st.write(f"📦 Materiais: R$ {total_materiais:,.2f}")
        st.write(f"⚖️ Diferença: R$ {diferenca:,.2f}")

        # ===============================
        # 🚨 ALERTAS
        # ===============================
        if df_nota.empty:
            st.error("🚨 Nota sem materiais!")

        elif abs(diferenca) > 0.01:
            st.error("🚨 Diferença detectada!")

        else:
            st.success("✅ Nota consistente")

        st.divider()

        # ===============================
        # 📋 LISTA DE ITENS
        # ===============================
        st.subheader("📋 Materiais da Nota")

        df_nota = df_nota.sort_values(by="Data", ascending=False)

        for _, row in df_nota.iterrows():
            col1, col2 = st.columns([4, 1])
            col1.write(row["Material"])
            col2.write(f"R$ {row['ValorTotal']:,.2f}")

    else:
        st.info("Nenhuma nota com materiais ainda.")
