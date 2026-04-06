from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from store.database import init_db
from web.routers import backlog, goals, intel, career, product

load_dotenv()

BASE = Path(__file__).parent

app = FastAPI(title="YOS Dashboard", docs_url=None, redoc_url=None)

app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE / "templates"))

app.include_router(backlog.router)
app.include_router(goals.router)
app.include_router(intel.router)
app.include_router(career.router)
app.include_router(product.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return RedirectResponse(url="/intel")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("WEB_PORT", "8000"))
    uvicorn.run("web.app:app", host="0.0.0.0", port=port, reload=True)
