from datetime import datetime
import streamlit as st
import pandas as pd
import os
import uuid
import re

from services.lancamento import salvar_lancamento, carregar_lancamentos
from services.fornecedores import carregar_fornecedores
from services.listas import listar_etapas_ativas

def limpar_nome_arquivo(nome):
    nome = nome.replace(" ", "_")
    return re.sub(r'[^a-zA-Z0-9_.-]', '', nome)

PASTA_RECIBOS = "recibos"

if not os.path.exists(PASTA_RECIBOS):
    os.makedirs(PASTA_RECIBOS)

def tela_painel_completo(obra_selecionada):

    perfil = st.session_state.get("perfil", "ADMIN")
    modo_parceiro = perfil == "PARCEIRO"
    modo_notas = st.session_state.get("notas_modo", "cadastro")

    if perfil == "ADMIN":

        if modo_notas == "listar":
            st.subheader("Notas lançadas")
            df_notas = carregar_lancamentos(obra_selecionada)

            if df_notas is None or df_notas.empty:
                st.info("Nenhuma nota lançada para esta obra.")
            else:
                tabela = df_notas.copy()
                tabela["Entrada Nota"] = pd.to_datetime(
                    tabela.get("Entrada Nota"), errors="coerce"
                )
                tabela["Valor"] = pd.to_numeric(
                    tabela.get("Valor"), errors="coerce"
                ).fillna(0).abs()
                colunas = [
                    coluna for coluna in [
                        "Entrada Nota", "Nº Nota", "Fornecedor",
                        "Descrição", "Categoria", "Etapa", "Valor", "Status"
                    ] if coluna in tabela.columns
                ]
                st.dataframe(
                    tabela[colunas],
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "Entrada Nota": st.column_config.DateColumn("Data"),
                        "Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                    },
                )

            if st.button("Nova nota", type="primary", key="notas_listar_nova"):
                st.session_state["notas_modo"] = "cadastro"
                st.rerun()
            return

        # ==============================
        # 🎨 ESTILO PROFISSIONAL
        # ==============================
        st.markdown("""
        <style>
        .block-container {
            max-width: 1400px;
            padding-top: 1rem;
        }

        [data-testid="stForm"] {
            background-color: #111827;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #1f2937;
        }
        </style>
        """, unsafe_allow_html=True)

        st.subheader("➕ Novo Lançamento")

        with st.expander("Abrir formulário", expanded=True):

            with st.form("form_registro", clear_on_submit=True):

                # ==============================
                # 🔹 LINHA 1 — TIPO + STATUS
                # ==============================
                col1, col2 = st.columns(2)

                with col1:
                    tipo = st.radio(
                        "Movimentação",
                        ["Saída (Gasto)", "Entrada (Recebido)"],
                        horizontal=True
                    )

                with col2:
                    situacao = st.radio(
                        "Situação",
                        ["Pendente", "Pago/Recebido"],
                        horizontal=True
                    )

                # ==============================
                # 🔹 LINHA 2 — FORNECEDOR + VALOR
                # ==============================
                col1, col2 = st.columns([2,1])

                df_forn = carregar_fornecedores(apenas_ativos=True)
                fornecedores_opcoes = (
                    df_forn.sort_values("Nome").to_dict("records")
                    if not df_forn.empty else []
                )

                with col1:
                    fornecedor_registro = st.selectbox(
                        "🏢 Fornecedor",
                        fornecedores_opcoes,
                        format_func=lambda item: item["Nome"],
                    )
                    fornecedor = fornecedor_registro["Nome"] if fornecedor_registro else ""

                with col2:
                    valor = st.number_input(
                        "💰 Valor (R$)",
                        min_value=0.0,
                        format="%.2f",
                        step=50.0
                    )

                # ==============================
                # 🔹 LINHA 3 — CATEGORIA + ETAPA
                # ==============================
                col1, col2 = st.columns(2)

                with col1:
                    lista_cat = (
                        ["Aporte de Capital"]
                        if tipo == "Entrada (Recebido)"
                        else [
                            "Serviços",
                            "Material Bruto",
                            "Acabamento",
                            "Elétrica/Hidráulica",
                            "Impostos",
                            "Outros",
                        ]
                    )

                    cat = st.selectbox("📂 Categoria", lista_cat)

                with col2:
                    etapa = None
                    if tipo == "Saída (Gasto)":
                        etapa = st.selectbox("🏗 Etapa da Obra", listar_etapas_ativas())

                # ==============================
                # 🔹 LINHA 4 — NOTA + DATAS
                # ==============================
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    num_nota = st.text_input("📄 Nº Nota") if tipo == "Saída (Gasto)" else "-"

                with col2:
                    dt_entrada = st.date_input("📅 Entrada")

                with col3:
                    dt_venc = st.date_input("📅 Vencimento")

                with col4:
                    dt_pg = (
                        st.date_input("📅 Pagamento")
                        if situacao == "Pago/Recebido"
                        else None
                    )

                # ==============================
                # 🔹 LINHA 5 — RECIBO
                # ==============================
                foto = st.file_uploader(
                    "📷 Recibo / Nota",
                    type=["png", "jpg", "jpeg", "pdf"]
                )

                # ==============================
                # 🔹 BOTÃO
                # ==============================
                st.divider()

                salvar = st.form_submit_button(
                    "💾 Salvar Lançamento",
                    use_container_width=True
                )
                
                # ==============================
                # 🔹 LÓGICA (INALTERADA)
                # ==============================
                if salvar:

                    if tipo == "Sa?da (Gasto)" and not fornecedor:
                        st.warning("Informe o fornecedor.")
                        return

                    if valor <= 0:
                        st.warning("Informe um valor maior que zero.")
                        return

                    if not cat:
                        st.warning("Informe a categoria.")
                        return

                    if not etapa:
                        st.warning("Informe a etapa.")
                        return

                    if situacao == "Pago/Recebido" and not dt_pg:
                        st.warning("Informe a data do pagamento.")
                        return

                    caminho_foto = "-"

                    if foto is not None:
                        nome_limpo = limpar_nome_arquivo(
                            f"{obra_selecionada}_{fornecedor}_{foto.name}"
                        )
                        caminho_foto = os.path.join(PASTA_RECIBOS, nome_limpo).replace("\\", "/")

                        with open(caminho_foto, "wb") as f:
                            f.write(foto.getbuffer())

                    agora = datetime.now()

                    valor_final = -valor if tipo == "Saída (Gasto)" else valor

                    ok, erro = salvar_lancamento({
                        
                        "Etapa": etapa,
                        "ID": str(uuid.uuid4()),
                        "Obra": obra_selecionada,
                        "Tipo": tipo,
                        "Nº Nota": num_nota,
                        "Entrada Nota": pd.to_datetime(dt_entrada),
                        "Data Vencimento": pd.to_datetime(dt_venc),
                        "Data Pagto": (
                            pd.to_datetime(dt_pg)
                            if situacao == "Pago/Recebido"
                            else pd.NaT
                        ),
                        "Criado Em": agora,
                        "Pago Em": agora if situacao == "Pago/Recebido" else pd.NaT,
                        "Descrição": fornecedor,
                        "Fornecedor": fornecedor,
                        "FornecedorID": fornecedor_registro["ID"] if fornecedor_registro else "",
                        "Categoria": cat,
                        "Valor": valor_final,
                        "Status": situacao,
                        "Foto": caminho_foto,
                    })
                    
                    if ok:
                        st.success("✅ Registro salvo com sucesso!")
                        st.write(ok)
                        st.write(erro)
                        df_debug = carregar_lancamentos(obra_selecionada)

                        st.dataframe(
                            df_debug[[
                                "Obra",
                                "Descrição",
                                "Nº Nota",
                                "Valor"
                            ]].tail(10)
                        )
                        #st.rerun()
                    else:
                        st.error(f"Erro: {erro}")
                        
