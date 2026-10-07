from typing import Annotated

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.core.templating import render

router = APIRouter()
api_router = APIRouter(prefix="/api")

@router.get("/dashboard")
def dashboard(request: Request):
    return render(request, "dashboard.html",)

@router.get("/")
def index() -> RedirectResponse:
    return RedirectResponse("/dashboard", status_code=303)
