from datetime import datetime
import streamlit as st
import pandas as pd
import os
import uuid
import re

from core.config import limpar_nome_arquivo, PASTA_RECIBOS
from services.lancamento import salvar_lancamento, carregar_lancamentos
from services.fornecedores import carregar_fornecedores
from services.insumos import (
    salvar_insumo,
    carregar_insumos,
    excluir_insumo,
    atualizar_insumo
)
from services.produtos import listar_nomes_produtos, normalizar_nome_produto

def tela_erp_lancamento(obra_selecionada):

    
    st.subheader("🧾 Lançamento + Materiais (Modo ERP)")

    df_notas = carregar_lancamentos(obra_selecionada)

    if df_notas.empty:
        st.warning("Nenhuma nota encontrada")
        return

    df_notas["Valor"] = pd.to_numeric(df_notas["Valor"], errors="coerce")

    col1, col2 = st.columns([1, 1])

    # =========================
    # 📄 NOTA
    # =========================
    with col1:

        df_insumos = carregar_insumos(obra_selecionada)

        df_insumos["ValorTotal"] = pd.to_numeric(df_insumos["ValorTotal"], errors="coerce")
        df_notas["Valor"] = pd.to_numeric(df_notas["Valor"], errors="coerce")

        # soma materiais por nota
        soma = df_insumos.groupby("NotaID")["ValorTotal"].sum()

        # cria coluna auxiliar
        df_notas["TotalMateriais"] = df_notas["ID"].map(soma).fillna(0)

        # 🔥 REGRA FINAL
        df_notas_abertas = df_notas[
            df_notas["TotalMateriais"] < df_notas["Valor"].abs()
        ]

        # 🔥 ordenação segura
        if "Entrada Nota" in df_notas_abertas.columns:
            df_notas_abertas = df_notas_abertas.sort_values(
                by="Entrada Nota", ascending=True
            )

        if df_notas_abertas.empty:
            st.warning("Nenhuma nota aberta disponível")
            return
        st.write(df_notas_abertas)
        nota_sel = st.selectbox(
            "📄 Selecionar Nota",
            df_notas_abertas.to_dict("records"),
            format_func=lambda x: (
                f"{x['Descrição']} | "
                f"R$ {abs(x['Valor']):,.2f} | "
                f"{x.get('Etapa','-')}"
            )
        )

        if not nota_sel:
            st.stop()

        nota_id = nota_sel["ID"]

        # 🔥 CALCULO VEM PRIMEIRO
        valor_base = abs(nota_sel["Valor"])

        frete = nota_sel.get("Frete", 0) or 0
        imposto = nota_sel.get("Imposto", 0) or 0
        desconto = nota_sel.get("Desconto", 0) or 0

        valor_nota = valor_base + frete + imposto - desconto

        # 🔽 AGORA PODE USAR
        st.metric("💰 Valor da Nota", f"R$ {abs(nota_sel['Valor']):,.2f}")
        st.write(f"🏗 Etapa: {nota_sel.get('Etapa','-')}")
        st.write(f"🏢 Fornecedor: {nota_sel.get('Descrição','-')}")

        st.write(f"📄 Base: R$ {valor_base:,.2f}")
        st.write(f"🚚 Frete: R$ {frete:,.2f}")
        st.write(f"🧾 Imposto: R$ {imposto:,.2f}")
        st.write(f"💸 Desconto: R$ {desconto:,.2f}")

        st.metric("💰 Total da Nota", f"R$ {valor_nota:,.2f}")

    # =========================
    # 📊 ITENS DA NOTA
    # =========================

    df_mat = df_insumos[df_insumos["NotaID"] == nota_id]

    total_materiais = 0

    if not df_mat.empty:
        df_mat["ValorTotal"] = pd.to_numeric(df_mat["ValorTotal"], errors="coerce")
        total_materiais = df_mat["ValorTotal"].sum()

    # =========================
    # 📊 AUDITORIA
    # =========================

    valor_base = abs(nota_sel["Valor"])

    frete = nota_sel.get("Frete", 0) or 0
    imposto = nota_sel.get("Imposto", 0) or 0
    desconto = nota_sel.get("Desconto", 0) or 0

    valor_nota = valor_base + frete + imposto - desconto

    diferenca = valor_nota - total_materiais
    nota_fechada = abs(diferenca) < 0.01
    # =========================
    # 📦 FORM
    # =========================
    with col2:

        st.markdown("### ➕ Adicionar Material")

        if nota_fechada:
            st.success("🔒 Nota travada")

        else:

            with st.form("form_add_material", clear_on_submit=True):

                produtos_ativos = listar_nomes_produtos()
                opcao_novo = "CADASTRAR NOVO PRODUTO..."
                produto_selecionado = st.selectbox(
                    "Produto / material",
                    [opcao_novo] + produtos_ativos,
                    help="Digite para pesquisar produtos ativos ou escolha cadastrar novo.",
                )
                novo_produto = st.text_input(
                    "Novo produto",
                    placeholder="Preencha somente ao cadastrar um produto novo",
                )
                unidade = st.text_input("Unidade", placeholder="Ex.: kg, un, m², saco")
                categoria_produto = st.text_input("Categoria do produto")
                qtd = st.number_input("Quantidade", min_value=0.0)
                valor_unit = st.number_input("Valor Unitário", min_value=0.0)

                total_item = qtd * valor_unit
                st.metric("💰 Total", f"R$ {total_item:,.2f}")

                st.caption("Os itens são salvos automaticamente ao adicionar")

                salvar = st.form_submit_button("➕ Adicionar Item")

                if salvar:

                    material = novo_produto if produto_selecionado == opcao_novo else produto_selecionado
                    if not material or qtd <= 0 or valor_unit <= 0:
                        st.warning("Preencha corretamente")
                        st.stop()

                    ok, erro = salvar_insumo({
                        "Obra": obra_selecionada,
                        "Etapa": nota_sel["Etapa"],
                        "Material": material,
                        "Unidade": unidade,
                        "CategoriaProduto": categoria_produto,
                        "Quantidade": qtd,
                        "ValorUnitario": valor_unit,
                        "NotaID": nota_id
                    })

                    if ok:
                        st.success("Item adicionado")
                        st.rerun()
                    else:
                        st.error(erro)

    st.divider()
    # =========================
    # 📦 LISTA DE ITENS
    # =========================
    if not df_mat.empty:

        df_mat = df_mat[df_mat["NotaID"] == nota_id]

        if not df_mat.empty:

            st.subheader("📦 Materiais da Nota")

            for i, row in df_mat.iterrows():

                col1, col2, col3, col4, col5, col6 = st.columns([2,1,1,1,1,1])

                material_atual = normalizar_nome_produto(row["Material"])
                opcoes_produto = listar_nomes_produtos(incluir=[material_atual])
                material = col1.selectbox(
                    "Produto",
                    opcoes_produto,
                    index=opcoes_produto.index(material_atual),
                    key=f"mat_{row['ID']}",
                    label_visibility="collapsed",
                )
                qtd = col2.number_input("", value=float(row["Quantidade"]), key=f"qtd_{row['ID']}")
                valor = col3.number_input("", value=float(row["ValorUnitario"]), key=f"val_{row['ID']}")

                total = qtd * valor
                col4.write(f"R$ {total:,.2f}")

                if nota_fechada:
                    col5.write("🔒")
                    col6.write("🔒")
                else:
                    if col5.button("💾", key=f"save_{row['ID']}"):
                        atualizar_insumo(row["ID"], {
                            "Material": material,
                            "Quantidade": qtd,
                            "ValorUnitario": valor
                        })
                        st.rerun()

                    if col6.button("🗑", key=f"del_{row['ID']}"):
                        excluir_insumo(row["ID"])
                        st.rerun()

    # =========================
    # 📊 RESUMO
    # =========================
    st.divider()

    colA, colB, colC = st.columns(3)

    colA.metric("📄 Nota", f"R$ {valor_nota:,.2f}")
    colB.metric("📦 Materiais", f"R$ {total_materiais:,.2f}")
    colC.metric("⚖️ Saldo", f"R$ {diferenca:,.2f}")

    if diferenca > 0:
        st.warning(f"⚠️ Ainda faltam R$ {diferenca:,.2f}")

    elif abs(diferenca) < 0.01:
        st.success("✅ Nota fechada corretamente")

    else:
        st.error(f"🚨 Você lançou R$ {abs(diferenca):,.2f} a mais")

