import pandas as pd
import streamlit as st

from services.relatorio_despesas import (
    aplicar_filtros,
    caminho_comprovante,
    consolidar_despesas,
    gerar_excel_despesas,
    gerar_pdf_despesas,
)


def _opcoes(df, coluna):
    return ["Todos"] + sorted(df[coluna].dropna().astype(str).unique().tolist())


def _resumo_por(df, coluna):
    resumo = df.groupby(coluna, dropna=False)["Valor total"].sum().sort_values(ascending=False).reset_index()
    resumo[coluna] = resumo[coluna].fillna("Não informado")
    return resumo


def _comprovantes(df):
    notas = df[df["Comprovante"].fillna("").astype(str).str.strip().ne("")].drop_duplicates("NotaID")
    if notas.empty:
        return
    with st.expander("Comprovantes e imagens das notas"):
        opcoes = notas["NotaID"].tolist()
        selecionado = st.selectbox(
            "Selecionar comprovante",
            opcoes,
            format_func=lambda nota_id: (
                f"Nota {notas[notas['NotaID'] == nota_id].iloc[0]['Nº nota']} · "
                f"{notas[notas['NotaID'] == nota_id].iloc[0]['Fornecedor']}"
            ),
            key="relatorio_materiais_comprovante",
        )
        if st.button("Abrir comprovante", key="relatorio_materiais_abrir_comprovante"):
            st.session_state["relatorio_comprovante_aberto"] = selecionado
        if st.session_state.get("relatorio_comprovante_aberto") == selecionado:
            registro = notas[notas["NotaID"] == selecionado].iloc[0]
            caminho = caminho_comprovante(registro["Comprovante"])
            if not caminho:
                st.warning("O arquivo do comprovante não foi encontrado.")
            elif caminho.suffix.lower() == ".pdf":
                st.download_button("Baixar comprovante PDF", caminho.read_bytes(), file_name=caminho.name, mime="application/pdf")
            else:
                st.image(str(caminho), use_container_width=True)


def tela_relatorio_materiais(obra_selecionada):
    st.markdown("## Materiais e Despesas da Obra")
    st.caption(f"Visão detalhada e somente leitura de {obra_selecionada}")
    df = consolidar_despesas(obra_selecionada)
    if df.empty:
        st.info("Nenhuma despesa encontrada para esta obra.")
        return

    datas = pd.to_datetime(df["Data da nota"], errors="coerce")
    hoje = pd.Timestamp.today().date()
    inicio_padrao = datas.min().date() if pd.notna(datas.min()) else hoje
    fim_padrao = datas.max().date() if pd.notna(datas.max()) else hoje

    f1, f2, f3 = st.columns(3)
    with f1:
        inicio = st.date_input("Período inicial", value=inicio_padrao, key="rel_mat_inicio")
        categoria = st.selectbox("Categoria", _opcoes(df, "Categoria"), key="rel_mat_categoria")
    with f2:
        fim = st.date_input("Período final", value=fim_padrao, key="rel_mat_fim")
        etapa = st.selectbox("Etapa", _opcoes(df, "Etapa"), key="rel_mat_etapa")
    with f3:
        fornecedor = st.selectbox("Fornecedor", _opcoes(df, "Fornecedor"), key="rel_mat_fornecedor")
        status = st.selectbox("Status", ["Todos", "Pago", "A pagar"], key="rel_mat_status")

    filtrado = aplicar_filtros(df, inicio, fim, categoria, etapa, fornecedor, status)
    total = float(filtrado["Valor total"].sum()) if not filtrado.empty else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Total geral", f"R$ {total:,.2f}")
    c2.metric("Itens detalhados", len(filtrado))
    c3.metric("Fornecedores", filtrado["Fornecedor"].nunique())

    tabela = filtrado.drop(columns=["Comprovante", "NotaID"], errors="ignore").copy()
    st.dataframe(
        tabela,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Data da nota": st.column_config.DateColumn("Data da nota", format="DD/MM/YYYY"),
            "Data de pagamento": st.column_config.DateColumn("Data de pagamento", format="DD/MM/YYYY"),
            "Quantidade": st.column_config.NumberColumn("Quantidade", format="%.2f"),
            "Valor unitário": st.column_config.NumberColumn("Valor unitário", format="R$ %.2f"),
            "Valor total": st.column_config.NumberColumn("Valor total", format="R$ %.2f"),
        },
    )

    _comprovantes(filtrado)
    st.markdown('<div class="delta-section-title">Totalizadores</div>', unsafe_allow_html=True)
    r1, r2, r3 = st.tabs(["Por categoria", "Por fornecedor", "Por etapa"])
    with r1:
        st.dataframe(_resumo_por(filtrado, "Categoria"), hide_index=True, use_container_width=True)
    with r2:
        st.dataframe(_resumo_por(filtrado, "Fornecedor"), hide_index=True, use_container_width=True)
    with r3:
        st.dataframe(_resumo_por(filtrado, "Etapa"), hide_index=True, use_container_width=True)

    excel, pdf = st.columns(2)
    with excel:
        st.download_button(
            "Exportar Excel", gerar_excel_despesas(filtrado, obra_selecionada),
            file_name=f"Materiais_Despesas_{obra_selecionada}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with pdf:
        st.download_button(
            "Exportar PDF", gerar_pdf_despesas(filtrado, obra_selecionada),
            file_name=f"Materiais_Despesas_{obra_selecionada}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
