# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata


block_cipher = None
root = Path.cwd()


def add_tree(folder, prefix, exclude_names=None, exclude_suffixes=None):
    exclude_names = set(exclude_names or [])
    exclude_suffixes = tuple(exclude_suffixes or [])
    datas = []
    base = root / folder
    if not base.exists():
        return datas
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(base)
        if any(part in exclude_names for part in rel.parts):
            continue
        if path.suffix.lower() in exclude_suffixes:
            continue
        datas.append((str(path), str(Path(prefix) / rel.parent)))
    return datas


datas = []
datas += add_tree("app", "app", exclude_suffixes=[".pyc"])
datas += add_tree("services", "services", exclude_suffixes=[".pyc"])
datas += add_tree("core", "core", exclude_suffixes=[".pyc"])
datas += add_tree("database", "database", exclude_suffixes=[".pyc", ".db"])
datas.append((str(root / "database" / "gestor_clean.db"), "database"))
datas += add_tree("icons", "icons")
datas.append((str(root / "manifest.json"), "."))
if (root / ".streamlit" / "config.toml").exists():
    datas.append((str(root / ".streamlit" / "config.toml"), ".streamlit"))

datas += collect_data_files("streamlit")
datas += copy_metadata("streamlit")
datas += copy_metadata("altair")
datas += copy_metadata("pandas")
datas += copy_metadata("plotly")

hiddenimports = []
hiddenimports += collect_submodules("streamlit")
hiddenimports += collect_submodules("plotly")
hiddenimports += collect_submodules("PIL")
hiddenimports += collect_submodules("openpyxl")
hiddenimports += collect_submodules("reportlab")


a = Analysis(
    ["run_delta_gestor.py"],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "pytest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DeltaGestor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(root / "icons" / "favicon.ico"),
    version=str(root / "version_info.txt"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="DeltaGestor",
)
