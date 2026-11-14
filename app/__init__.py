# app/__init__.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import (
    user_router,
    auth_router,
    category_router,
    ledger_router,
)

def create_app() -> FastAPI:
    app = FastAPI(title="Moni API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    routers = [
        user_router.router,
        auth_router.router,
        category_router.router,
        ledger_router.router,
    ]

    for r in routers:
        app.include_router(r)

    return app
