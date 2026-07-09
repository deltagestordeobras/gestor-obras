import streamlit as st
import pandas as pd
import os
import logging
from database.connection import get_connection


# ==========================================
# 🔎 BUSCAR PIX DO FORNECEDOR
# ==========================================
def buscar_pix_fornecedor(nome_fornecedor):

    conn = get_connection()

    try:

        cursor = conn.execute("""
            SELECT ChavePix
            FROM fornecedores
            WHERE Nome = ?
        """, (nome_fornecedor,))

        resultado = cursor.fetchone()

        if resultado:
            return resultado[0]

        return ""

    except Exception:
        logging.exception("Erro ao buscar PIX do fornecedor %s.", nome_fornecedor)
        return ""

    finally:
        conn.close()


# ==========================================
# 💳 TELA PARCEIRO
# ==========================================
def tela_lancamentos_parceiro(
    df_obra,
    obra_selecionada,
    key_prefix="notas_parceiro",
):

    # ==========================================
    # 🧹 DADOS
    # ==========================================
    df = df_obra.copy()

    df["Valor"] = pd.to_numeric(
        df["Valor"],
        errors="coerce"
    ).fillna(0)

    df["Entrada Nota"] = pd.to_datetime(
        df["Entrada Nota"],
        errors="coerce"
    )

    # fornecedor fallback
    df["FornecedorFinal"] = (
        df["Fornecedor"]
        .fillna(df["Descrição"])
        .astype(str)
        .str.strip()
    )

    df["FornecedorFinal"] = df[
        "FornecedorFinal"
    ].replace("", "Sem fornecedor")

    entradas = df[df["Valor"] > 0]["Valor"].sum()

    saidas = df[df["Valor"] < 0]["Valor"].sum()

    saldo = entradas + saidas

    # ==========================================
    # 💳 HEADER
    # ==========================================
    st.markdown(
    f"""
    <div style="
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    padding:22px;
    border-radius:18px;
    color:white;
    margin-bottom:15px;
    ">
    <div style="font-size:13px;">
    Saldo disponível
    </div>

    <div style="
    font-size:32px;
    font-weight:700;
    ">
    R$ {saldo:,.2f}
    </div>
    </div>
    """,
    unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Entradas",
        f"R$ {entradas:,.2f}"
    )

    col2.metric(
        "Saídas",
        f"R$ {abs(saidas):,.2f}"
    )

    st.divider()

    # ==========================================
    # 🔘 FILTROS
    # ==========================================
    filtro = st.radio(
        "Filtrar lançamentos",
        ["Tudo", "Pagos", "Pendentes"],
        horizontal=True,
        label_visibility="collapsed",
        key=key_prefix,
    )

    if filtro == "Pagos":

        df = df[
            df["Status"].str.contains(
                "Pago",
                na=False
            )
        ]

    elif filtro == "Pendentes":

        df = df[
            ~df["Status"].str.contains(
                "Pago",
                na=False
            )
        ]

    # ==========================================
    # 💳 SOMENTE SAÍDAS
    # ==========================================
    df_fornecedor = df[
        df["Valor"] < 0
    ].copy()

    df_fornecedor["FornecedorFinal"] = (
        df_fornecedor["Fornecedor"]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.strip()
    )

    # se vazio usa descrição
    df_fornecedor.loc[
        df_fornecedor["FornecedorFinal"] == "",
        "FornecedorFinal"
    ] = (
        df_fornecedor["Descrição"]
        .astype(str)
        .str.upper()
        .str.strip()
    )
    # ==========================================
    # 📊 AGRUPAMENTO
    # ==========================================
    agrupado = (
        df_fornecedor
        .groupby("FornecedorFinal")
        .agg(
            total=("Valor", "sum"),
            qtd_notas=("Nº Nota", "count")
        )
        .reset_index()
    )

    # ==========================================
    # 📄 DETALHES DAS NOTAS
    # ==========================================
    notas_por_fornecedor = (
        df_fornecedor
        .groupby("FornecedorFinal")
        .apply(
            lambda x: x[
                [
                    "Nº Nota",
                    "Valor",
                    "Foto",
                    "Entrada Nota"
                ]
            ].to_dict("records")
        )
        .to_dict()
    )

    # ==========================================
    # 💳 CARDS
    # ==========================================
    for i, row in agrupado.iterrows():

        fornecedor = row["FornecedorFinal"]

        total = abs(row["total"])

        qtd_notas = row["qtd_notas"]

        pix = buscar_pix_fornecedor(
            fornecedor
        )

        st.markdown(
        f"""
        <div style="
        background:#111827;
        padding:18px;
        border-radius:16px;
        margin-bottom:12px;
        border:1px solid #1f2937;
        ">

        <div style="
        font-size:18px;
        font-weight:700;
        color:white;
        ">
        {fornecedor}
        </div>

        <div style="
        font-size:28px;
        color:#ef4444;
        font-weight:800;
        margin-top:8px;
        ">
        R$ {total:,.2f}
        </div>

        <div style="
        color:#facc15;
        font-size:13px;
        margin-top:5px;
        ">
        {qtd_notas} notas pendentes
        </div>

        </div>
        """,
        unsafe_allow_html=True
        )

        # ==========================================
        # ⚡ AÇÕES
        # ==========================================
        col1, col2 = st.columns(2)

        with col1:

            if filtro == "Pendentes" and pix:

                if st.button(
                    f"📋 PIX {i}",
                    key=f"{key_prefix}_pix_{i}",
                ):

                    st.code(pix)

        with col2:

            if filtro == "Pendentes":

                if st.button(
                    f"💸 Pagar {i}",
                    key=f"{key_prefix}_pagar_{i}",
                ):

                    st.success(
                        "Pagamento enviado para confirmação"
                    )
        # ==========================================
        # 📄 NOTAS
        # ==========================================
        notas = notas_por_fornecedor[
            fornecedor
        ]

        with st.expander(
            f"🧾 Ver notas ({qtd_notas})"
        ):

            for nota in notas:

                numero = nota.get(
                    "Nº Nota",
                    "-"
                )

                valor = abs(
                    nota.get("Valor", 0)
                )

                foto = nota.get("Foto")

                data = nota.get(
                    "Entrada Nota"
                )

                if pd.notna(data):

                    data = data.strftime(
                        "%d/%m/%Y"
                    )

                else:

                    data = "-"

                st.markdown(
                f"""
                <div style="
                background:#0f172a;
                padding:10px;
                border-radius:10px;
                margin-bottom:8px;
                border:1px solid #1e293b;
                ">

                <div style="
                font-weight:600;
                color:white;
                ">
                Nota {numero}
                </div>

                <div style="
                color:#ef4444;
                font-size:16px;
                font-weight:700;
                ">
                R$ {valor:,.2f}
                </div>

                <div style="
                color:#94a3b8;
                font-size:12px;
                ">
                {data}
                </div>

                </div>
                """,
                unsafe_allow_html=True
                )

                if (
                    foto
                    and isinstance(foto, str)
                    and os.path.exists(foto)
                ):

                    st.image(
                        foto,
                        width=250
                    )

    # ==========================================
    # 🚨 ALERTAS
    # ==========================================
    if saldo < 0:

        st.error(
            "🚨 Saldo negativo"
        )

    if abs(saidas) > entradas:

        st.warning(
            "⚠️ Gastos maiores que entradas"
        )
