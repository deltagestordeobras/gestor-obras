from pathlib import Path
import os
import sqlite3
import sys


ROOT_DIR = Path(__file__).resolve().parent.parent
CLEAN_DB = ROOT_DIR / "database" / "gestor_clean.db"


def limpar_tabelas_operacionais(db_path):
    tabelas_operacionais = [
        "obras",
        "lancamentos",
        "insumos",
        "fornecedores",
        "cronograma",
        "evolucao_obra",
        "diario_obra",
        "usuarios",
    ]

    conn = sqlite3.connect(db_path)
    try:
        for tabela in tabelas_operacionais:
            conn.execute(f'DELETE FROM "{tabela}"')
        conn.commit()
        conn.execute("VACUUM")
    finally:
        conn.close()


def criar_banco_limpo():
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))

    CLEAN_DB.parent.mkdir(parents=True, exist_ok=True)
    if CLEAN_DB.exists():
        CLEAN_DB.unlink()

    os.environ["DELTA_GESTOR_DB_PATH"] = str(CLEAN_DB)

    from database.init_db import inicializar_banco

    inicializar_banco()
    limpar_tabelas_operacionais(CLEAN_DB)
    print(f"Banco limpo gerado em: {CLEAN_DB}")


if __name__ == "__main__":
    criar_banco_limpo()
