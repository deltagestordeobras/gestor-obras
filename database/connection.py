from pathlib import Path
import sqlite3
import os
import shutil


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CLEAN_DB_PATH = BASE_DIR / "database" / "gestor_clean.db"


def _modo_producao():
    modo = os.environ.get("DELTA_GESTOR_MODE") or os.environ.get("DELTA_GESTOR_ENV") or ""
    return modo.strip().lower() in {"prod", "producao", "produção", "production"}


def resolver_db_path():
    caminho_env = os.environ.get("DELTA_GESTOR_DB_PATH")
    if caminho_env:
        return Path(caminho_env)

    nome_banco = "gestor.db" if _modo_producao() else "gestor_dev.db"
    return DATA_DIR / nome_banco


DB_PATH = resolver_db_path()


def instalar_banco_inicial():
    if DB_PATH.exists():
        return

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CLEAN_DB_PATH.exists():
        shutil.copy2(CLEAN_DB_PATH, DB_PATH)


def get_connection():
    instalar_banco_inicial()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabela_insumos():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS insumos (
            ID TEXT,
            Obra TEXT,
            Etapa TEXT,
            Material TEXT,
            Quantidade REAL,
            ValorUnitario REAL,
            ValorTotal REAL,
            Data TEXT,
            NotaID TEXT
        )
    """)

    conn.commit()
    conn.close()
