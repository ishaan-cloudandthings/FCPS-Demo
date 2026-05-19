"""FastAPI application entry point.

Run locally with:
    cd backend
    uvicorn main:app --reload --workers 1

The `--workers 1` flag is significant — see AC6-D2 (in-process OAuth
state cache). Multi-worker deploys must wait for a shared-store
implementation (phase 2).
"""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.procurement import router as procurement_router
from app.core.config import get_settings
from app.utils.logging import get_logger

app = FastAPI(
    title="FCPS Vendor Procurement Portal API",
    version="0.1.0-AC6",
)

app.include_router(auth_router)
app.include_router(procurement_router)

# Dev-only persona endpoint — ADR-014 (boot-time half of the DEV2 gate).
# The router is not registered at all in non-dev environments; FastAPI
# returns the same 404 it returns for any unknown path. Defence in depth:
# the handlers in dev_auth.py also re-check at request time.
_settings = get_settings()
if _settings.environment == "dev":
    from app.api.dev_auth import router as dev_auth_router

    app.include_router(dev_auth_router)

logger = get_logger(__name__)

# Loud warning when the built-in demo JWT secret is in force. The
# `Settings._refuse_demo_defaults_outside_dev` validator means we can
# only get here in `dev`, but we still want it on stdout for any
# operator who tails the log.
if _settings.is_using_demo_jwt_secret():
    logger.warning(
        "DEMO_BOOT: using built-in demo JWT_SECRET_KEY. "
        "Fine for local demo — DO NOT promote this build to any non-dev environment."
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP exceptions pass through with their declared status + detail.

    Propagates custom headers (e.g. `X-Auth-Reason` for 403s from
    `/api/auth/callback` per AC7-D9). Kept explicit so the generic
    `Exception` handler below does not accidentally re-wrap a 4xx as a 500.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers or None,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Per FUNCTIONAL_DESIGN.md §10 + NFR-12: never leak stack traces.

    Server logs still record the full trace via `logger.exception`. The
    browser-facing body is a single user-friendly message.
    """
    logger.exception("unhandled.exception path=%s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Something went wrong. Please try again."},
    )
