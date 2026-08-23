# ============================================================
# main.py — the ENTRY POINT of the backend.
#
# When you run `uvicorn app.main:app`, uvicorn looks in this file
# for a variable named `app`. That's the FastAPI application. Here
# we create it, configure CORS, and plug in all route files.
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import upload, analyze, report, history, exercises

# Create the application. The title/description show up in the
# auto-generated docs at http://localhost:8000/docs.
app = FastAPI(
    title="VALT API",
    description="Measures biomechanical patterns from jump-landing videos. Not a diagnostic tool.",
    version="0.1.0",
)

# ---- CORS: Cross-Origin Resource Sharing ----
# Browsers block a website from calling a server on a DIFFERENT origin
# (different domain/port) unless that server explicitly allows it. Our
# frontend (localhost:3000) and backend (localhost:8000) are different
# origins, so we must list the frontend here or the browser will refuse.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list(),  # e.g. ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],   # allow GET, POST, etc.
    allow_headers=["*"],
)

# ---- Wire in the route files ----
# Each router adds its endpoints to the app.
app.include_router(upload.router)
app.include_router(analyze.router)
app.include_router(report.router)
app.include_router(history.router)
app.include_router(exercises.router)


# A simple health-check endpoint. Hosts like Render ping this to see
# if the server is alive. Also handy to test the server is up.
@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "valt"}


# A friendly root message so visiting the base URL isn't a 404.
@app.get("/", tags=["system"])
async def root():
    return {
        "message": "VALT API is running.",
        "docs": "/docs",
    }
