import streamlit as st
import pandas as pd

from services.lancamento import carregar_lancamentos
from services.insumos import carregar_insumos


def tela_auditoria(obra_selecionada):

    st.subheader("🔎 Auditoria de Notas e Materiais")

    df_notas = carregar_lancamentos(obra_selecionada)
    df_insumos = carregar_insumos(obra_selecionada)

    if df_notas.empty:
        st.info("Nenhuma nota encontrada.")
        return

    if df_insumos is None or df_insumos.empty:
        st.warning("Nenhum material vinculado às notas ainda.")
        return

    notas = df_notas["ID"].dropna().unique()

    if len(notas) == 0:
        st.info("Nenhuma nota disponível.")
        return

    nota_sel = st.selectbox("Selecione a Nota", notas)

    df_nota = df_notas[df_notas["ID"] == nota_sel]
    df_mat = df_insumos[df_insumos["NotaID"] == nota_sel]

    valor_nota = 0
    if not df_nota.empty:
        valor_nota = pd.to_numeric(
            pd.Series([df_nota["Valor"].values[0]]),
            errors="coerce",
        ).fillna(0).iloc[0]
        valor_nota = abs(valor_nota)

    df_mat = df_mat.copy()
    df_mat["ValorTotal"] = pd.to_numeric(df_mat["ValorTotal"], errors="coerce").fillna(0)
    total_materiais = df_mat["ValorTotal"].sum()

    diferenca = valor_nota - total_materiais

    st.divider()

    st.write(f"📄 Nota: R$ {valor_nota:,.2f}")
    st.write(f"📦 Materiais: R$ {total_materiais:,.2f}")
    st.write(f"⚖️ Diferença: R$ {diferenca:,.2f}")

    # ===============================
    # 🚨 ALERTAS
    # ===============================
    if df_mat.empty:
        st.error("🚨 Nota sem materiais!")

    elif abs(diferenca) > 0.01:
        st.error("🚨 Diferença detectada entre nota e materiais!")

    else:
        st.success("✅ Nota conferida e consistente")

    st.divider()

    # ===============================
    # 📋 LISTA DE MATERIAIS
    # ===============================
    st.subheader("📦 Materiais da Nota")

    if not df_mat.empty:
        df_mat["ValorTotal"] = pd.to_numeric(df_mat["ValorTotal"], errors="coerce")

        st.dataframe(
            df_mat[["Material", "Quantidade", "ValorTotal"]],
            use_container_width=True
        )
    else:
        st.info("Nenhum material vinculado.")
