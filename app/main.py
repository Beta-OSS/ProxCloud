from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import auth, users, new_user_vm
from app.api.routes.admin import admin, users as admin_users, vm_templates

from app.core.config import get_settings
from app.core.templating import BASE_DIR, render


SAFE_MESSAGES = {
    400: "That request was not valid.",
    403: "You do not have permission to do that.",
    404: "Page not found.",
    405: "Method not allowed.",
    429: "Too many requests. Please try again later.",
}


CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "img-src 'self' data:; "
    "frame-ancestors 'none'; "
    "base-uri 'none'; "
    "form-action 'self'"
)


def create_app() -> FastAPI:
    s = get_settings()

    app = FastAPI(
        title=s.app_name,
        docs_url="/docs" if s.enable_api_docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if s.enable_api_docs else None,
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)

        response.headers["Content-Security-Policy"] = CSP
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"

        if s.cookie_secure:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        if not request.url.path.startswith("/static"):
            response.headers["Cache-Control"] = "no-store"

        return response

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ):
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                {"detail": exc.detail},
                status_code=exc.status_code,
                headers=exc.headers,
            )

        if exc.status_code == 401:
            if request.headers.get("hx-request") == "true":
                return Response(
                    status_code=401,
                    headers={"HX-Redirect": "/login"},
                )

            return RedirectResponse("/login", status_code=303)

        message = SAFE_MESSAGES.get(
            exc.status_code,
            "Something went wrong.",
        )

        return render(
            request,
            "error.html",
            status_code=exc.status_code,
            code=exc.status_code,
            message=message,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        # Never echo submitted input back (it may contain passwords).
        if request.url.path.startswith("/api/"):
            errors = [
                {
                    "loc": list(error["loc"]),
                    "msg": error["msg"],
                }
                for error in exc.errors()
            ]

            return JSONResponse(
                {"detail": errors},
                status_code=422,
            )

        return render(
            request,
            "error.html",
            status_code=400,
            code=400,
            message=SAFE_MESSAGES[400],
        )

    @app.get("/healthz", include_in_schema=False)
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.mount(
        "/static",
        StaticFiles(directory=str(BASE_DIR / "static")),
        name="static",
    )

    # Public/user routes.
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(new_user_vm.router)

    # Admin HTML routes.
    app.include_router(admin.router)
    app.include_router(admin_users.router)
    app.include_router(vm_templates.router)

    # Admin JSON API routes.
    app.include_router(admin_users.api_router)
    app.include_router(vm_templates.api_router)
    

    return app


app = create_app()