from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=getattr(exc, "status_code", 500),
            content={
                "error": {
                    "code": getattr(exc, "code", "internal_error"),
                    "message": str(exc),
                    "fields": getattr(exc, "fields", {})
                }
            }
        )
