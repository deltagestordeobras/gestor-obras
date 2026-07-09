import logging
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from database.connection import BASE_DIR, DB_PATH


BACKUP_DIR = BASE_DIR / "backups"
MAX_BACKUPS_AUTOMATICOS = 30
PASTAS_BACKUP = ["uploads", "recibos", "logs"]


def _timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def _data_hoje():
    return datetime.now().strftime("%Y-%m-%d")


def _caminho_relativo(caminho):
    caminho = Path(caminho)
    try:
        return caminho.resolve().relative_to(BASE_DIR.resolve())
    except ValueError:
        return Path("data") / caminho.name


def _adicionar_arquivo(zipf, caminho, destino=None):
    caminho = Path(caminho)
    if caminho.exists() and caminho.is_file():
        zipf.write(caminho, destino or _caminho_relativo(caminho))


def _adicionar_pasta(zipf, pasta):
    pasta = Path(pasta)
    if not pasta.exists() or not pasta.is_dir():
        return

    for arquivo in pasta.rglob("*"):
        if arquivo.is_file():
            zipf.write(arquivo, _caminho_relativo(arquivo))


def _tamanho_pasta(pasta):
    pasta = Path(pasta)
    if not pasta.exists():
        return 0
    return sum(arquivo.stat().st_size for arquivo in pasta.rglob("*") if arquivo.is_file())


def _formatar_bytes(tamanho):
    valor = float(tamanho)
    for unidade in ["B", "KB", "MB", "GB"]:
        if valor < 1024 or unidade == "GB":
            return f"{valor:.2f} {unidade}"
        valor /= 1024
    return f"{valor:.2f} GB"


def _criar_zip(prefixo):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    caminho_backup = BACKUP_DIR / f"{prefixo}_{_timestamp()}.zip"

    with zipfile.ZipFile(caminho_backup, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        _adicionar_arquivo(zipf, DB_PATH)

        for pasta in PASTAS_BACKUP:
            _adicionar_pasta(zipf, BASE_DIR / pasta)

        secrets = BASE_DIR / ".streamlit" / "secrets.toml"
        _adicionar_arquivo(zipf, secrets)

    if not caminho_backup.exists() or caminho_backup.stat().st_size == 0:
        raise RuntimeError("O arquivo de backup nao foi criado corretamente.")

    return caminho_backup


def criar_backup_manual():
    return _criar_zip("Backup_DELTA_Gestor")


def criar_backup_pre_restauracao():
    return _criar_zip("Backup_PRE_RESTAURACAO")


def listar_backups():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backups = []
    for arquivo in sorted(BACKUP_DIR.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True):
        backups.append({
            "nome": arquivo.name,
            "caminho": str(arquivo),
            "tamanho": arquivo.stat().st_size,
            "tamanho_formatado": _formatar_bytes(arquivo.stat().st_size),
            "modificado_em": datetime.fromtimestamp(arquivo.stat().st_mtime),
        })
    return backups


def resumo_backups():
    backups = listar_backups()
    return {
        "ultimo": backups[0] if backups else None,
        "quantidade": len(backups),
        "tamanho_total": _tamanho_pasta(BACKUP_DIR),
        "tamanho_total_formatado": _formatar_bytes(_tamanho_pasta(BACKUP_DIR)),
        "pasta": str(BACKUP_DIR),
    }


def _validar_zip_backup(caminho_backup):
    caminho_backup = Path(caminho_backup)
    if caminho_backup.suffix.lower() != ".zip":
        raise ValueError("Selecione um arquivo .zip valido.")
    if not caminho_backup.exists():
        raise FileNotFoundError("Arquivo de backup nao encontrado.")
    if not zipfile.is_zipfile(caminho_backup):
        raise ValueError("O arquivo selecionado nao e um zip valido.")

    banco_esperado = str(_caminho_relativo(DB_PATH)).replace("\\", "/")

    with zipfile.ZipFile(caminho_backup, "r") as zipf:
        nomes = zipf.namelist()
        for nome in nomes:
            destino = (BASE_DIR / nome).resolve()
            if BASE_DIR.resolve() not in destino.parents and destino != BASE_DIR.resolve():
                raise ValueError("Backup recusado por conter caminho inseguro.")

        if not any(nome.replace("\\", "/") == banco_esperado for nome in nomes):
            raise ValueError("Backup recusado: banco esperado nao encontrado no arquivo.")


def restaurar_backup(caminho_backup):
    caminho_backup = Path(caminho_backup)
    _validar_zip_backup(caminho_backup)
    backup_previo = criar_backup_pre_restauracao()

    with zipfile.ZipFile(caminho_backup, "r") as zipf:
        for membro in zipf.infolist():
            nome = membro.filename.replace("\\", "/")
            destino = (BASE_DIR / nome).resolve()
            if BASE_DIR.resolve() not in destino.parents and destino != BASE_DIR.resolve():
                raise ValueError("Backup recusado por conter caminho inseguro.")
            if membro.is_dir():
                destino.mkdir(parents=True, exist_ok=True)
                continue
            destino.parent.mkdir(parents=True, exist_ok=True)
            with zipf.open(membro, "r") as origem, open(destino, "wb") as saida:
                shutil.copyfileobj(origem, saida)

    return backup_previo


def limpar_backups_antigos(limite=30, apenas_automaticos=False):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    padrao = "Backup_AUTO_DELTA_Gestor_*.zip" if apenas_automaticos else "*.zip"
    backups = sorted(BACKUP_DIR.glob(padrao), key=lambda p: p.stat().st_mtime, reverse=True)
    removidos = []
    for arquivo in backups[limite:]:
        arquivo.unlink()
        removidos.append(str(arquivo))
    return removidos


def abrir_pasta_backups():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    os.startfile(str(BACKUP_DIR))


def criar_backup_automatico_diario():
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        prefixo_dia = f"Backup_AUTO_DELTA_Gestor_{_data_hoje()}_"
        if any(arquivo.name.startswith(prefixo_dia) for arquivo in BACKUP_DIR.glob("Backup_AUTO_DELTA_Gestor_*.zip")):
            return None

        caminho = _criar_zip("Backup_AUTO_DELTA_Gestor")
        limpar_backups_antigos(MAX_BACKUPS_AUTOMATICOS, apenas_automaticos=True)
        return caminho
    except Exception:
        logging.exception("Falha ao criar backup automatico diario.")
        return None
