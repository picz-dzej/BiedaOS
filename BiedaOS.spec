# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ["run.py"],
    datas=[("biedaos/static", "biedaos/static")],
    hiddenimports=[
        "uvicorn.logging", "uvicorn.loops", "uvicorn.loops.auto",
        "uvicorn.protocols", "uvicorn.protocols.http", "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets", "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan", "uvicorn.lifespan.on", "uvicorn.lifespan.off",
    ],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas,
    name="BiedaOS",
    console=True,
    upx=False,
)
