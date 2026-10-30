from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from careertracker import __version__

WEB_DIR = Path(__file__).parent

app = FastAPI(title="Career Mode Tracker", version=__version__)
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
templates = Jinja2Templates(directory=WEB_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"version": __version__})


@app.get("/status", response_class=HTMLResponse)
def status(request: Request):
    """Fragment HTML podmieniany przez HTMX (przykład komunikacji z serwerem)."""
    context = {"version": __version__, "time": datetime.now().strftime("%H:%M:%S")}
    return templates.TemplateResponse(request, "partials/status.html", context)


@app.get("/health")
def health():
    return {"status": "ok", "version": __version__}
