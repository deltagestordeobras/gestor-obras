import streamlit as st
from io import BytesIO

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import pagesizes
from reportlab.lib.units import inch

from services.status import STATUS_PAGO, STATUS_PENDENTE, preparar_valor_status


def gerar_pdf_obra(df_obra, obra_selecionada):

    if df_obra is None or df_obra.empty:
        st.info("Sem dados para gerar relatório.")
        return

    if st.button("📄 Gerar Relatório em PDF"):

        df = preparar_valor_status(df_obra)

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=pagesizes.A4)

        elements = []
        styles = getSampleStyleSheet()

        # ===============================
        # TITULO
        # ===============================
        elements.append(
            Paragraph(
                f"Relatório Financeiro - {obra_selecionada}",
                styles["Heading1"],
            )
        )
        elements.append(Spacer(1, 0.3 * inch))

        # ===============================
        # RESUMO
        # ===============================
        total_pago = df[
            (df["StatusNormalizado"] == STATUS_PAGO)
            & (df["Tipo"] == "Saída (Gasto)")
        ]["Valor"].sum()

        total_pago = abs(total_pago)

        total_pendente = df[
            (df["StatusNormalizado"] == STATUS_PENDENTE)
            & (df["Tipo"] == "Saída (Gasto)")
        ]["Valor"].sum()

        total_pendente = abs(total_pendente)

        total_aportado = df[
            (df["Tipo"] == "Entrada (Recebido)")
            & (df["Categoria"] == "Aporte de Capital")
        ]["Valor"].sum()

        saldo_obra = df["Valor"].sum()

        elements.append(Paragraph(f"Total Aportado: R$ {total_aportado:,.2f}", styles["Normal"]))
        elements.append(Paragraph(f"Total Pago: R$ {total_pago:,.2f}", styles["Normal"]))
        elements.append(Paragraph(f"Total Pendente: R$ {total_pendente:,.2f}", styles["Normal"]))
        elements.append(Paragraph(f"Saldo Atual: R$ {saldo_obra:,.2f}", styles["Normal"]))

        elements.append(Spacer(1, 0.3 * inch))

        # ===============================
        # TABELA
        # ===============================
        dados_tabela = [[
            "Data Entrada",
            "Nº Nota",
            "Descrição",
            "Categoria",
            "Valor (R$)",
            "Status",
        ]]

        for _, row in df.iterrows():
            dados_tabela.append([
                str(row.get("Entrada Nota", "")),
                str(row.get("Nº Nota", "")),
                str(row.get("Descrição", "")),
                str(row.get("Categoria", "")),
                f"{row.get('Valor', 0):,.2f}",
                str(row.get("Status", "")),
            ])

        tabela = Table(dados_tabela, repeatRows=1)

        tabela.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (4, 1), (4, -1), "RIGHT"),
            ])
        )

        elements.append(tabela)

        doc.build(elements)

        pdf = buffer.getvalue()
        buffer.close()

        st.download_button(
            label="⬇️ Baixar PDF",
            data=pdf,
            file_name=f"Relatorio_{obra_selecionada}.pdf",
            mime="application/pdf",
        )