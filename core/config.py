import re
import os

# =========================
# 📁 PASTA DE RECIBOS
# =========================
PASTA_RECIBOS = "uploads/recibos"

os.makedirs(PASTA_RECIBOS, exist_ok=True)

# =========================
# 🧼 LIMPAR NOME DE ARQUIVO
# =========================
def limpar_nome_arquivo(nome):
    nome = nome.lower()
    nome = re.sub(r"[^a-zA-Z0-9_.-]", "_", nome)
    return nome
