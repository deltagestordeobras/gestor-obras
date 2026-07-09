import streamlit as st


def tela_ia(df):

    st.subheader("🤖 IA da Obra")

    pergunta = st.text_input("Pergunte algo sobre a obra")

    if pergunta:

        if "gasto" in pergunta.lower():
            total = df["Valor"].sum()
            st.write(f"Gasto total: R$ {total:,.2f}")

        elif "fornecedor" in pergunta.lower():
            top = df.groupby("Fornecedor")["Valor"].sum().abs().idxmax()
            st.write(f"Fornecedor mais caro: {top}")

        else:
            st.write("Ainda estou aprendendo 😅")

def perguntar_ia(df, pergunta):
    contexto = df.to_string()
    prompt = f"Analise: {contexto}\nPergunta: {pergunta}"