from pathlib import Path
import os
import sys


def _app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _resource_dir():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def main():
    app_dir = _app_dir()
    resource_dir = _resource_dir()

    os.chdir(app_dir)
    os.environ.setdefault("DELTA_GESTOR_MODE", "production")
    os.environ.setdefault("DELTA_GESTOR_ENV", "production")
    os.environ.setdefault("DELTA_GESTOR_DB_PATH", str(app_dir / "data" / "gestor.db"))

    for pasta in ["data", "uploads", "recibos", "logs", "backups"]:
        (app_dir / pasta).mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(resource_dir))

    from streamlit.web import cli as stcli

    app_main = resource_dir / "app" / "main.py"
    sys.argv = [
        "streamlit",
        "run",
        str(app_main),
        "--server.address=127.0.0.1",
        "--server.port=8501",
        "--server.headless=false",
        "--browser.gatherUsageStats=false",
        "--global.developmentMode=false",
    ]
    stcli.main()


if __name__ == "__main__":
    main()
