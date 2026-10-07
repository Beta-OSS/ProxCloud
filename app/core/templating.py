from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.core.config import get_settings

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))  # autoescape is on for .html


def is_htmx(request: Request) -> bool:
    return request.headers.get("hx-request") == "true"


def render(request: Request, name: str, *, user=None, csrf_token: str = "", status_code: int = 200, **context):
    ctx = {"user": user, "csrf_token": csrf_token, "app_name": get_settings().app_name, **context}
    return templates.TemplateResponse(request, name, ctx, status_code=status_code)
