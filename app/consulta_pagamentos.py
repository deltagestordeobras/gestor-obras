import base64
from datetime import date
import html
import json
import os

import pandas as pd
import streamlit as st

from app.lancamentos_parceiro import tela_lancamentos_parceiro
from services.extrato_financeiro import (
    COLUNA_FORNECEDOR,
    aplicar_filtros_extrato,
    calcular_indicadores_extrato,
    formatar_tabela_extrato,
    obter_opcoes_filtro,
    preparar_extrato,
)
from services.fornecedores import carregar_fornecedores, resolver_fornecedores_lancamentos
from services.lancamento import carregar_lancamentos, dar_baixa_pagamentos
from services.pagamentos import (
    agrupar_pendentes_por_fornecedor,
    formatar_moeda,
    montar_resumo_pagamento,
    normalizar_nome_fornecedor,
)
from services.status import STATUS_PAGO, STATUS_PENDENTE


def _mapa_pix(df_fornecedores):
    if df_fornecedores is None or df_fornecedores.empty:
        return {}
    return {
        normalizar_nome_fornecedor(row.get("Nome")).casefold(): str(row.get("ChavePix") or "").strip()
        for _, row in df_fornecedores.iterrows()
    }


def _botao_copiar(texto, rotulo, chave):
    st.components.v1.html(
        f"""
        <button id="{html.escape(chave)}" style="
            width:100%;height:38px;border:1px solid #334155;border-radius:6px;
            background:#111827;color:#f8fafc;font:600 14px sans-serif;cursor:pointer;">
            {html.escape(rotulo)}
        </button>
        <script>
        const botao = document.getElementById({json.dumps(chave)});
        botao.onclick = async () => {{
            await navigator.clipboard.writeText({json.dumps(str(texto), ensure_ascii=False)});
            botao.textContent = "Copiado";
            setTimeout(() => botao.textContent = {json.dumps(rotulo)}, 1400);
        }};
        </script>
        """,
        height=42,
    )


def _exibir_grupos_pendentes(df_pendentes, df_fornecedores):
    grupos = agrupar_pendentes_por_fornecedor(df_pendentes, COLUNA_FORNECEDOR)
    if not grupos:
        st.success("Não há pagamentos pendentes para fornecedores.")
        return

    mapa_pix = _mapa_pix(df_fornecedores)

    for indice, (fornecedor, notas) in enumerate(grupos):
        chave_pix = mapa_pix.get(fornecedor.casefold(), "")
        total = notas["Valor"].abs().sum()
        quantidade = len(notas)

        with st.container(border=True):
            st.markdown(f"### {html.escape(fornecedor)}")
            c1, c2, c3 = st.columns([1.2, 1.5, 2])
            c1.metric("Notas pendentes", quantidade)
            c2.metric("Total a pagar", formatar_moeda(total))
            with c3:
                st.caption("Chave PIX")
                st.code(chave_pix or "Fornecedor sem PIX")

            resumo = montar_resumo_pagamento(fornecedor, chave_pix, notas)
            copiar_pix, copiar_resumo, pagar = st.columns(3)
            with copiar_pix:
                if chave_pix:
                    _botao_copiar(chave_pix, "Copiar PIX", f"copiar_pix_{indice}")
                else:
                    st.warning("Cadastre o PIX do fornecedor para copiar.")
            with copiar_resumo:
                _botao_copiar(resumo, "Copiar resumo", f"copiar_resumo_{indice}")
            with pagar:
                confirmar = st.checkbox(
                    "Confirmar baixa do grupo",
                    key=f"confirmar_grupo_pagamento_{indice}",
                )
                if st.button(
                    "Marcar todas como pagas",
                    key=f"pagar_grupo_{indice}",
                    disabled=not confirmar,
                    use_container_width=True,
                ):
                    ok, erro = dar_baixa_pagamentos(
                        notas["ID"].dropna().astype(str).tolist(),
                        date.today(),
                    )
                    if not ok:
                        st.error("Não foi possível concluir as baixas: " + str(erro))
                    else:
                        st.success(f"{quantidade} nota(s) marcada(s) como pagas.")
                        st.rerun()

            with st.expander(f"Ver notas ({quantidade})"):
                tabela = notas.copy()
                tabela["Data"] = pd.to_datetime(tabela["Entrada Nota"], errors="coerce")
                tabela["Valor pendente"] = tabela["Valor"].abs()
                colunas = [
                    coluna for coluna in
                    ["Data", "Nº Nota", "Categoria", "Etapa", "Valor pendente", "Status"]
                    if coluna in tabela.columns
                ]
                st.dataframe(
                    tabela[colunas].sort_values("Data", ascending=False, na_position="last"),
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                        "Valor pendente": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                    },
                )


def carregar_imagem_base64(caminho):
    if isinstance(caminho, str) and caminho != "-" and os.path.exists(caminho):
        with open(caminho, "rb") as f:
            dados = base64.b64encode(f.read()).decode()
            return f"data:image/png;base64,{dados}"

    return None


def exibir_resumo_periodo(df_periodo):
    indicadores = calcular_indicadores_extrato(df_periodo)

    c1, c2, c3 = st.columns(3)
    c1.metric("Saldo", f"R$ {indicadores['saldo_obra']:,.2f}")
    c2.metric("Pago", f"R$ {indicadores['total_pago']:,.2f}")
    c3.metric("Pendente", f"R$ {indicadores['total_pendente']:,.2f}")


def exibir_tabela_extrato(df, incluir_recibo=False):
    tabela = formatar_tabela_extrato(df)

    if incluir_recibo and df is not None and "Foto" in df.columns:
        tabela = tabela.copy()
        tabela["Recibo"] = df["Foto"].apply(carregar_imagem_base64)

    column_config = {
        "Entrada Nota": st.column_config.DateColumn("Entrada"),
        "Data Vencimento": st.column_config.DateColumn("Vencimento"),
        "Data Pagto": st.column_config.DateColumn("Pagamento"),
        "Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
    }

    if "Recibo" in tabela.columns:
        column_config["Recibo"] = st.column_config.ImageColumn("Recibo", width="small")

    st.dataframe(
        tabela,
        use_container_width=True,
        column_config=column_config,
    )


def tela_consulta_pagamentos(obra_selecionada, df_obra=None):
    perfil = st.session_state.get("perfil", "ADMIN")

    if df_obra is None:
        df_obra = carregar_lancamentos(obra_selecionada)
    df_extrato = resolver_fornecedores_lancamentos(preparar_extrato(df_obra))

    # =========================
    # 👤 PARCEIRO → TELA SEPARADA
    # =========================
    if perfil == "PARCEIRO":
        tela_lancamentos_parceiro(
            df_extrato,
            obra_selecionada,
            key_prefix="filtro_pagamentos_parceiro",
        )
        return

    # =========================
    # 👑 ADMIN
    # =========================
    st.subheader("📑 Lançamentos da Obra")

    if df_extrato is None or df_extrato.empty:
        st.info("Nenhum lançamento encontrado para esta obra.")
        return

    # =========================
    # 🔍 FILTRO FORNECEDOR
    # =========================
    lista_fornecedores = obter_opcoes_filtro(df_extrato, COLUNA_FORNECEDOR)
    fornecedor_filtro = st.selectbox("Filtrar por fornecedor", lista_fornecedores)

    df_filtrado = aplicar_filtros_extrato(
        df_extrato,
        fornecedor=fornecedor_filtro,
    )

    # =========================
    # 📑 ABAS
    # =========================
    aba1, aba2, aba3, aba4 = st.tabs(
        ["📋 Tudo", "✅ Já Pagos", "⏳ Pendentes", "📅 Período"]
    )

    # =========================
    # 📋 ABA 1 - TUDO
    # =========================
    with aba1:
        exibir_tabela_extrato(df_filtrado, incluir_recibo=True)

    # =========================
    # ✅ ABA 2 - PAGOS
    # =========================
    with aba2:
        df_pagos = df_filtrado[df_filtrado["StatusNormalizado"] == STATUS_PAGO]

        if not df_pagos.empty:
            indicadores = calcular_indicadores_extrato(df_pagos)

            st.success(f"Total já pago nesta obra: R$ {indicadores['total_pago']:,.2f}")
            exibir_tabela_extrato(df_pagos)
        else:
            st.info("Nenhum pagamento realizado ainda.")

    # =========================
    # ⏳ ABA 3 - PENDENTES
    # =========================
    with aba3:
        df_pendentes = df_filtrado[df_filtrado["StatusNormalizado"] == STATUS_PENDENTE]

        if df_pendentes.empty:
            st.success("Não há contas pendentes!")
        else:
            indicadores = calcular_indicadores_extrato(df_pendentes)

            st.warning(
                f"Você tem R$ {indicadores['total_pendente']:,.2f} em contas pendentes."
            )

            _exibir_grupos_pendentes(df_pendentes, carregar_fornecedores())

    # =========================
    # 📅 ABA 4 - PERÍODO
    # =========================
    with aba4:
        col1, col2 = st.columns(2)

        with col1:
            data_inicio = st.date_input("Data Inicial")

        with col2:
            data_fim = st.date_input("Data Final")

        if data_inicio and data_fim:
            df_periodo = aplicar_filtros_extrato(
                df_extrato,
                fornecedor=fornecedor_filtro,
                data_inicio=data_inicio,
                data_fim=data_fim,
            )

            if not df_periodo.empty:
                exibir_resumo_periodo(df_periodo)
                exibir_tabela_extrato(df_periodo)
            else:
                st.info("Nenhum lançamento encontrado nesse período.")
