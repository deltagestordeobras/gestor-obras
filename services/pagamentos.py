import pandas as pd


def formatar_moeda(valor):
    return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def normalizar_nome_fornecedor(valor):
    nome = " ".join(str(valor or "").split())
    return nome if nome and nome.lower() != "nan" else "Sem fornecedor"


def agrupar_pendentes_por_fornecedor(df_pendentes, coluna_fornecedor="Fornecedor"):
    despesas = df_pendentes[df_pendentes["Valor"] < 0].copy()
    if despesas.empty:
        return []
    despesas["_FornecedorGrupo"] = despesas[coluna_fornecedor].apply(normalizar_nome_fornecedor)
    despesas["_FornecedorChave"] = despesas["_FornecedorGrupo"].str.casefold()
    return [
        (notas["_FornecedorGrupo"].iloc[0], notas.copy())
        for _, notas in despesas.groupby("_FornecedorChave", sort=True, dropna=False)
    ]


def montar_resumo_pagamento(fornecedor, chave_pix, notas):
    linhas = [
        fornecedor,
        f"{len(notas)} nota(s) pendente(s)",
        f"Total a pagar: {formatar_moeda(notas['Valor'].abs().sum())}",
        f"PIX: {chave_pix or 'Não cadastrado'}",
        "",
        "Notas:",
    ]
    for _, nota in notas.sort_values("Entrada Nota", ascending=False, na_position="last").iterrows():
        data_nota = nota.get("Entrada Nota")
        data_texto = data_nota.strftime("%d/%m/%Y") if pd.notna(data_nota) else "Sem data"
        numero = str(nota.get("Nº Nota") or "").strip()
        sufixo = f" - Nota {numero}" if numero and numero.lower() != "nan" else ""
        linhas.append(f"- {data_texto} - {formatar_moeda(abs(nota.get('Valor', 0)))}{sufixo}")
    return "\n".join(linhas)
