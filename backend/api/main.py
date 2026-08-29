"""Basit web arayüzü: FastAPI ile çözücüyü tarayıcıdan çalıştırma.

Bu, CLAUDE.md §7'deki 'api/' katmanının ilk, en yalın halidir. Takvim ızgarası,
sürükle-bırak, hücre kilitleme gibi Aşama 4 özellikleri burada YOK — yalnızca
bir form üzerinden JSON girdisi verip sonucu okunabilir bir tabloda görmeyi
sağlar. Girdi/çıktı şeması CLI ile birebir aynıdır (bkz. ../cli.py).
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from cli import load_request, result_to_dict
from solver.solve import solve

app = FastAPI(title="Nöbet Çözücü — Basit Arayüz")

_INDEX_HTML = (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _INDEX_HTML


@app.post("/api/solve")
def api_solve(data: dict) -> JSONResponse:
    try:
        request = load_request(data)
    except (KeyError, ValueError, TypeError) as exc:
        return JSONResponse(status_code=400, content={"error": f"Girdi hatası: {exc}"})

    result = solve(request)
    return JSONResponse(content=result_to_dict(result))
