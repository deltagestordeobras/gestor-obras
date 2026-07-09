import streamlit as st

from services.permissoes import tem_permissao
from services.produtos import atualizar_produto, carregar_produtos, salvar_produto


def tela_produtos():
    if not tem_permissao("produtos"):
        st.warning("Sem permissão para acessar Produtos / Insumos.")
        return

    st.markdown("## Produtos / Insumos")
    st.caption("Cadastro mestre utilizado nos itens das notas e no ERP.")

    with st.expander("Adicionar produto", expanded=False):
        with st.form("form_novo_produto", clear_on_submit=True):
            nome = st.text_input("Nome do produto")
            unidade = st.text_input("Unidade", placeholder="Ex.: kg, un, m², saco")
            categoria = st.text_input("Categoria", placeholder="Ex.: Material bruto")
            if st.form_submit_button("Adicionar produto", type="primary", use_container_width=True):
                ok, retorno = salvar_produto(nome, unidade, categoria)
                if ok:
                    st.success("Produto cadastrado.")
                    st.rerun()
                st.error(retorno)

    produtos = carregar_produtos(somente_ativos=False)
    if produtos.empty:
        st.info("Nenhum produto cadastrado.")
        return

    filtro = st.text_input("Pesquisar produto", placeholder="Digite parte do nome")
    if filtro.strip():
        produtos = produtos[
            produtos["Nome"].astype(str).str.contains(filtro.strip(), case=False, na=False)
        ]

    st.markdown('<div class="delta-section-title">Cadastro mestre</div>', unsafe_allow_html=True)
    for _, produto in produtos.iterrows():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 1.2, 1.8, 1], vertical_alignment="center")
            with c1:
                nome = st.text_input("Produto", value=str(produto["Nome"] or ""), key=f"produto_nome_{produto['ID']}")
            with c2:
                unidade = st.text_input("Unidade", value=str(produto["Unidade"] or ""), key=f"produto_unidade_{produto['ID']}")
            with c3:
                categoria = st.text_input("Categoria", value=str(produto["Categoria"] or ""), key=f"produto_categoria_{produto['ID']}")
            with c4:
                ativo = st.toggle("Ativo", value=bool(produto["Ativo"]), key=f"produto_ativo_{produto['ID']}")
                if st.button("Salvar", key=f"produto_salvar_{produto['ID']}", use_container_width=True):
                    ok, erro = atualizar_produto(produto["ID"], nome, unidade, categoria, ativo)
                    if ok:
                        st.success("Produto atualizado.")
                        st.rerun()
                    st.error(erro)
