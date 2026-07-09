import re

import pandas as pd
import streamlit as st

from app.ui_utils import moeda as _moeda, texto as _texto
from services.fornecedores import (
    buscar_fornecedores,
    carregar_fornecedores,
    definir_fornecedor_ativo,
    filtrar_lancamentos_fornecedor,
    obter_fornecedor,
    preparar_lancamentos_fornecedores_df,
    preparar_lancamentos_fornecedores,
    ranking_fornecedores,
    salvar_fornecedor,
    situacao_financeira_fornecedores,
)


def _formulario_fornecedor(registro=None):
    editando = registro is not None
    prefixo = registro["ID"] if editando else "novo"
    with st.form(f"form_fornecedor_{prefixo}", clear_on_submit=not editando):
        nome = st.text_input("Nome", value=str(registro.get("Nome") or "") if editando else "")
        rua, numero = st.columns([3, 1])
        rua_valor = rua.text_input("Endereço", value=str(registro.get("Rua") or "") if editando else "")
        numero_valor = numero.text_input("Número", value=str(registro.get("Numero") or "") if editando else "")
        bairro, cidade, cep = st.columns([1.5, 2, 1])
        bairro_valor = bairro.text_input("Bairro", value=str(registro.get("Bairro") or "") if editando else "")
        cidade_valor = cidade.text_input("Cidade", value=str(registro.get("Cidade") or "") if editando else "")
        cep_valor = cep.text_input("CEP", value=str(registro.get("CEP") or "") if editando else "")
        telefone, documento, pix = st.columns(3)
        telefone_valor = telefone.text_input("Telefone", value=str(registro.get("Telefone") or "") if editando else "")
        documento_valor = documento.text_input("Documento", value=str(registro.get("Documento") or "") if editando else "")
        pix_valor = pix.text_input("Chave PIX", value=str(registro.get("ChavePix") or "") if editando else "")
        enviar = st.form_submit_button(
            "Salvar alterações" if editando else "Cadastrar fornecedor",
            type="primary",
            use_container_width=True,
        )

    if enviar:
        ok, erro, _ = salvar_fornecedor({
            "ID": registro.get("ID") if editando else None,
            "Nome": nome, "Rua": rua_valor, "Numero": numero_valor,
            "Bairro": bairro_valor, "Cidade": cidade_valor,
            "CEP": re.sub(r"\D", "", cep_valor), "Telefone": telefone_valor,
            "Documento": documento_valor, "ChavePix": pix_valor,
            "Ativo": registro.get("Ativo", 1) if editando else 1,
        })
        if ok:
            st.session_state.pop("fornecedor_editar_id", None)
            st.success("Fornecedor atualizado." if editando else "Fornecedor cadastrado.")
            st.rerun()
        st.error(erro)


def _gestao_fornecedores(admin):
    termo = st.text_input("Buscar fornecedor", placeholder="Nome, documento, telefone ou chave PIX")
    mostrar_inativos = st.toggle("Mostrar inativos", value=False)
    fornecedores = buscar_fornecedores(carregar_fornecedores(), termo)
    if not mostrar_inativos and not fornecedores.empty:
        fornecedores = fornecedores[fornecedores["Ativo"].fillna(1).astype(int) == 1]
    if fornecedores.empty:
        st.info("Nenhum fornecedor encontrado.")
        return

    cabecalho = st.columns([2.2, 1.3, 1.3, 1.5, 2.8])
    for coluna, titulo in zip(cabecalho, ["Fornecedor", "Documento", "Telefone", "PIX", "Ações"]):
        coluna.markdown(f"**{titulo}**")

    for _, fornecedor in fornecedores.iterrows():
        colunas = st.columns([2.2, 1.3, 1.3, 1.5, 2.8], vertical_alignment="center")
        ativo = int(fornecedor.get("Ativo") or 0) == 1
        colunas[0].markdown(
            f"**{_texto(fornecedor['Nome'])}**  \n"
            f"<small>{'Ativo' if ativo else 'Inativo'}</small>",
            unsafe_allow_html=True,
        )
        colunas[1].write(fornecedor.get("Documento") or "-")
        colunas[2].write(fornecedor.get("Telefone") or "-")
        if fornecedor.get("ChavePix"):
            colunas[3].code(str(fornecedor["ChavePix"]))
        else:
            colunas[3].warning("Sem PIX cadastrado")
        with colunas[4]:
            ver, editar, ativar = st.columns(3)
            if ver.button("Ver lançamentos", key=f"fornecedor_ver_{fornecedor['ID']}", use_container_width=True):
                st.session_state["fornecedor_historico_id"] = fornecedor["ID"]
                st.session_state["fornecedor_aba_pendente"] = "historico"
                st.rerun()
            if admin and editar.button(
                "Cadastrar PIX" if not fornecedor.get("ChavePix") else "Editar",
                key=f"fornecedor_editar_{fornecedor['ID']}", use_container_width=True,
            ):
                st.session_state["fornecedor_editar_id"] = fornecedor["ID"]
                st.rerun()
            if admin and ativar.button(
                "Inativar" if ativo else "Reativar",
                key=f"fornecedor_ativo_{fornecedor['ID']}", use_container_width=True,
            ):
                definir_fornecedor_ativo(fornecedor["ID"], not ativo)
                st.rerun()
        st.divider()

    editar_id = st.session_state.get("fornecedor_editar_id")
    if admin and editar_id:
        st.markdown("### Editar fornecedor")
        registro = obter_fornecedor(editar_id)
        if registro:
            _formulario_fornecedor(registro)


def _historico_fornecedor(obra_selecionada, lancamentos_fornecedores=None):
    fornecedores = carregar_fornecedores()
    if fornecedores.empty:
        st.info("Nenhum fornecedor cadastrado.")
        return
    ids = fornecedores["ID"].tolist()
    id_pendente = st.session_state.pop("fornecedor_historico_id", None)
    if id_pendente in ids:
        st.session_state["fornecedor_historico_selecao"] = id_pendente
    selecionado_id = st.selectbox(
        "Fornecedor", ids, key="fornecedor_historico_selecao",
        format_func=lambda item: fornecedores.loc[fornecedores["ID"] == item, "Nome"].iloc[0],
    )
    fornecedor = fornecedores.loc[fornecedores["ID"] == selecionado_id].iloc[0]
    historico = filtrar_lancamentos_fornecedor(
        lancamentos_fornecedores
        if lancamentos_fornecedores is not None
        else preparar_lancamentos_fornecedores(obra_selecionada),
        fornecedor["Nome"],
        fornecedor["ID"],
    )
    despesas = historico[historico["Valor"] < 0] if not historico.empty else historico
    total = despesas["Valor"].abs().sum() if not despesas.empty else 0
    total_col, pix_col = st.columns(2)
    total_col.metric("Total negociado nesta obra", _moeda(total))
    if fornecedor.get("ChavePix"):
        pix_col.metric("Chave PIX", str(fornecedor["ChavePix"]))
    else:
        pix_col.warning("Sem PIX cadastrado")
        if str(st.session_state.get("perfil", "")).upper() == "ADMIN":
            if pix_col.button("Cadastrar PIX", key="historico_cadastrar_pix"):
                st.session_state["fornecedor_editar_id"] = selecionado_id
                st.rerun()
        if st.session_state.get("fornecedor_editar_id") == selecionado_id:
            _formulario_fornecedor(obter_fornecedor(selecionado_id))

    if historico.empty:
        st.info("Nenhum lançamento deste fornecedor encontrado na obra selecionada.")
        return
    tabela = historico.copy()
    tabela["Valor"] = tabela["Valor"].abs()
    colunas = [
        coluna for coluna in [
            "Nº Nota", "Entrada Nota", "Data Pagto", "Descrição", "Categoria",
            "Etapa", "Valor", "Status", "Foto",
        ] if coluna in tabela.columns
    ]
    st.dataframe(
        tabela[colunas].sort_values("Entrada Nota", ascending=False, na_position="last"),
        hide_index=True, use_container_width=True,
        column_config={
            "Entrada Nota": st.column_config.DateColumn("Data entrada", format="DD/MM/YYYY"),
            "Data Pagto": st.column_config.DateColumn("Data pagamento", format="DD/MM/YYYY"),
            "Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
            "Foto": st.column_config.ImageColumn("Comprovante", width="small"),
        },
    )


def _analise_fornecedores(obra_selecionada, lancamentos_fornecedores=None):
    lancamentos = (
        lancamentos_fornecedores
        if lancamentos_fornecedores is not None
        else preparar_lancamentos_fornecedores(obra_selecionada)
    )
    ranking = ranking_fornecedores(lancamentos)
    situacao = situacao_financeira_fornecedores(lancamentos)
    st.markdown("### Ranking de fornecedores")
    if ranking.empty:
        st.info("Nenhuma despesa com fornecedor encontrada nesta obra.")
    else:
        ranking = ranking.copy()
        ranking.insert(0, "Posição", [f"{indice}º" for indice in range(1, len(ranking) + 1)])
        st.dataframe(
            ranking, hide_index=True, use_container_width=True,
            column_config={"Total negociado": st.column_config.NumberColumn(format="R$ %.2f")},
        )
    st.markdown("### Situação financeira por fornecedor")
    if situacao.empty:
        st.info("Nenhuma situação financeira disponível.")
    else:
        st.dataframe(
            situacao, hide_index=True, use_container_width=True,
            column_config={
                coluna: st.column_config.NumberColumn(format="R$ %.2f")
                for coluna in ["Total pago", "Total pendente", "Total vencido"]
            },
        )


def tela_fornecedores(obra_selecionada, df_obra=None):
    admin = str(st.session_state.get("perfil", "")).upper() == "ADMIN"
    st.title("Fornecedores")
    st.caption(f"Cadastro e análise dos fornecedores da obra {obra_selecionada}")
    lancamentos_fornecedores = (
        preparar_lancamentos_fornecedores_df(df_obra)
        if df_obra is not None
        else None
    )
    aba_pendente = st.session_state.pop("fornecedor_aba_pendente", None)
    if aba_pendente == "historico":
        _historico_fornecedor(obra_selecionada, lancamentos_fornecedores)
        return

    nomes = ["Gestão", "Histórico", "Análise"]
    if admin:
        nomes.insert(0, "Cadastrar")
    abas = st.tabs(nomes)
    indice = 0
    if admin:
        with abas[indice]:
            _formulario_fornecedor()
        indice += 1
    with abas[indice]:
        _gestao_fornecedores(admin)
    with abas[indice + 1]:
        _historico_fornecedor(obra_selecionada, lancamentos_fornecedores)
    with abas[indice + 2]:
        _analise_fornecedores(obra_selecionada, lancamentos_fornecedores)
