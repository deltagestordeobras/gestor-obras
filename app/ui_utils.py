import html


def texto(valor):
    """Escapa HTML e converte para string segura."""
    return html.escape(str(valor or ""))


def moeda(valor, decimais=2):
    """Formata valor como moeda brasileira. Ex: R$ 1.200,00"""
    try:
        v = float(valor)
        formatado = f"{v:,.{decimais}f}"
        return "R$ " + formatado.replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "R$ 0,00"


def data_br(valor, padrao="Sem data"):
    """Formata data para padrão brasileiro DD/MM/AAAA."""
    import pandas as pd

    dt = pd.to_datetime(valor, errors="coerce")
    return dt.strftime("%d/%m/%Y") if pd.notna(dt) else padrao
