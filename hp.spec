# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for HP Assistant — single-folder distribution."""

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[
        (".venv/Lib/site-packages/openwakeword/resources", "openwakeword/resources"),
        ("hp.ico", "."),
    ],
    hiddenimports=[
        "pydantic",
        "pydantic_settings",
        "pydantic_settings.env_settings",
        "PySide6.QtWidgets",
        "PySide6.QtGui",
        "PySide6.QtCore",
        "app.assistant",
        "app.actions",
        "app.config",
        "app.llm",
        "app.llm.claude_provider",
        "app.llm.groq_provider",
        "app.llm.ollama_provider",
        "groq",
        "app.memory",
        "app.memory.tasks",
        "app.memory.memories",
        "app.memory.reminders",
        "app.services",
        "app.ui",
        "app.utils",
        "app.vision",
        "app.voice",
        "pycaw",
        "pycaw.pycaw",
        "comtypes",
        "comtypes.client",
        "anthropic",
        "httpx",
        "httpcore",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "ruff"],
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
    name="HP",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon="hp.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="HP",
)
