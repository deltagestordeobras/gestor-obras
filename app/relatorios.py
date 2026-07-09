import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import pagesizes
from reportlab.lib.units import inch


# =========================================================
# 🎨 ESTILO TABELA
# =========================================================
def estilo_tabela():

    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),

        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.whitesmoke,
            colors.HexColor("#f8fafc")
        ]),

        ("ALIGN", (0, 0), (-1, -1), "CENTER"),

        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),

        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ])


# =========================================================
# 💰 RESUMO FINANCEIRO
# =========================================================
def calcular_resumo(df):

    total_pago = abs(
        df[
            (df["Status"].str.contains("Pago", na=False))
            & (df["Valor"] < 0)
        ]["Valor"].sum()
    )

    total_pendente = abs(
        df[
            (df["Status"] == "Pendente")
            & (df["Valor"] < 0)
        ]["Valor"].sum()
    )

    total_aportado = df[
        df["Valor"] > 0
    ]["Valor"].sum()

    saldo = df["Valor"].sum()

    fornecedores = (
        df["Descrição"]
        .fillna("")
        .nunique()
    )

    notas = len(df)

    return {
        "pago": total_pago,
        "pendente": total_pendente,
        "aportado": total_aportado,
        "saldo": saldo,
        "fornecedores": fornecedores,
        "notas": notas,
    }


# =========================================================
# 📄 PDF FINANCEIRO COMPLETO
# =========================================================
def gerar_pdf_financeiro(df_obra, obra_selecionada):

    if df_obra is None or df_obra.empty:

        st.info("Sem dados para gerar relatório.")
        return

    df = df_obra.copy()

    df["Valor"] = pd.to_numeric(
        df["Valor"],
        errors="coerce"
    ).fillna(0)

    resumo = calcular_resumo(df)

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=pagesizes.A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25,
    )

    styles = getSampleStyleSheet()

    elements = []

    # =========================================================
    # 🏗️ CAPA
    # =========================================================
    elements.append(
        Paragraph(
            f"""
            <font size=24>
            <b>RELATÓRIO FINANCEIRO</b>
            </font>
            """,
            styles["Title"]
        )
    )

    elements.append(Spacer(1, 0.2 * inch))

    elements.append(
        Paragraph(
            f"""
            <font size=18>
            {obra_selecionada}
            </font>
            """,
            styles["Heading2"]
        )
    )

    elements.append(Spacer(1, 0.3 * inch))

    elements.append(
        Paragraph(
            f"""
            Data de emissão:
            {datetime.now().strftime('%d/%m/%Y %H:%M')}
            """,
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 0.5 * inch))

    # =========================================================
    # 💰 RESUMO EXECUTIVO
    # =========================================================
    elements.append(
        Paragraph(
            "<b>RESUMO EXECUTIVO</b>",
            styles["Heading2"]
        )
    )

    elements.append(Spacer(1, 0.15 * inch))

    resumo_data = [

        ["Indicador", "Valor"],

        ["Total Aportado",
         f"R$ {resumo['aportado']:,.2f}"],

        ["Total Pago",
         f"R$ {resumo['pago']:,.2f}"],

        ["Total Pendente",
         f"R$ {resumo['pendente']:,.2f}"],

        ["Saldo Atual",
         f"R$ {resumo['saldo']:,.2f}"],

        ["Fornecedores",
         str(resumo["fornecedores"])],

        ["Quantidade Notas",
         str(resumo["notas"])],
    ]

    tabela_resumo = Table(
        resumo_data,
        colWidths=[250, 200]
    )

    tabela_resumo.setStyle(
        estilo_tabela()
    )

    elements.append(tabela_resumo)

    elements.append(Spacer(1, 0.4 * inch))

    # =========================================================
    # 💸 CONTAS PENDENTES
    # =========================================================
    pendentes = df[
        (df["Status"] == "Pendente")
        & (df["Valor"] < 0)
    ]

    elements.append(
        Paragraph(
            "<b>CONTAS PENDENTES</b>",
            styles["Heading2"]
        )
    )

    elements.append(Spacer(1, 0.15 * inch))

    dados_pendentes = [[
        "Fornecedor",
        "Nota",
        "Categoria",
        "Valor",
        "Vencimento",
    ]]

    for _, row in pendentes.iterrows():

        dados_pendentes.append([
            str(row.get("Descrição", "")),
            str(row.get("Nº Nota", "")),
            str(row.get("Categoria", "")),
            f"R$ {abs(row.get('Valor', 0)):,.2f}",
            str(row.get("Data Vencimento", "")),
        ])

    tabela_pendentes = Table(
        dados_pendentes,
        repeatRows=1
    )

    tabela_pendentes.setStyle(
        estilo_tabela()
    )

    elements.append(tabela_pendentes)

    elements.append(Spacer(1, 0.4 * inch))

    # =========================================================
    # 🏢 FORNECEDORES
    # =========================================================
    fornecedor_df = (
        df[df["Valor"] < 0]
        .groupby("Descrição")
        .agg(
            total=("Valor", "sum"),
            qtd_notas=("Nº Nota", "count")
        )
        .reset_index()
    )

    elements.append(
        Paragraph(
            "<b>GASTOS POR FORNECEDOR</b>",
            styles["Heading2"]
        )
    )

    elements.append(Spacer(1, 0.15 * inch))

    dados_fornecedor = [[
        "Fornecedor",
        "Total",
        "Qtd Notas",
    ]]

    for _, row in fornecedor_df.iterrows():

        dados_fornecedor.append([
            str(row["Descrição"]),
            f"R$ {abs(row['total']):,.2f}",
            str(row["qtd_notas"]),
        ])

    tabela_fornecedor = Table(
        dados_fornecedor,
        repeatRows=1
    )

    tabela_fornecedor.setStyle(
        estilo_tabela()
    )

    elements.append(tabela_fornecedor)

    elements.append(Spacer(1, 0.4 * inch))

    # =========================================================
    # 🏗️ ETAPAS
    # =========================================================
    if "Etapa" in df.columns:

        etapa_df = (
            df[df["Valor"] < 0]
            .groupby("Etapa")
            .agg(
                total=("Valor", "sum")
            )
            .reset_index()
        )

        elements.append(
            Paragraph(
                "<b>CUSTO POR ETAPA</b>",
                styles["Heading2"]
            )
        )

        elements.append(Spacer(1, 0.15 * inch))

        dados_etapa = [[
            "Etapa",
            "Total",
        ]]

        for _, row in etapa_df.iterrows():

            dados_etapa.append([
                str(row["Etapa"]),
                f"R$ {abs(row['total']):,.2f}",
            ])

        tabela_etapa = Table(
            dados_etapa,
            repeatRows=1
        )

        tabela_etapa.setStyle(
            estilo_tabela()
        )

        elements.append(tabela_etapa)

    elements.append(PageBreak())

    # =========================================================
    # 📋 LANÇAMENTOS COMPLETOS
    # =========================================================
    elements.append(
        Paragraph(
            "<b>LANÇAMENTOS COMPLETOS</b>",
            styles["Heading2"]
        )
    )

    elements.append(Spacer(1, 0.2 * inch))

    dados_tabela = [[
        "Data",
        "Nota",
        "Fornecedor",
        "Categoria",
        "Valor",
        "Status",
    ]]

    for _, row in df.iterrows():

        dados_tabela.append([

            str(row.get("Entrada Nota", ""))[:10],

            str(row.get("Nº Nota", "")),

            str(row.get("Descrição", "")),

            str(row.get("Categoria", "")),

            f"R$ {row.get('Valor', 0):,.2f}",

            str(row.get("Status", "")),
        ])

    tabela = Table(
        dados_tabela,
        repeatRows=1
    )

    tabela.setStyle(
        estilo_tabela()
    )

    elements.append(tabela)

    # =========================================================
    # 🚀 GERAR PDF
    # =========================================================
    doc.build(elements)

    pdf = buffer.getvalue()

    buffer.close()

    # =========================================================
    # ⬇️ DOWNLOAD
    # =========================================================
    st.download_button(
        label="📄 Baixar Relatório Financeiro",
        data=pdf,
        file_name=f"Relatorio_{obra_selecionada}.pdf",
        mime="application/pdf",
        use_container_width=True
    )