"""Entrypoint — mirrors the Go backend's router/routing.go.

Serves on SERVER_ADDRESS (0.0.0.0:8090, same port as the Go service) so the
Angular dev proxy (/api/report -> 8090) works for this prototype unchanged.
Run:  python main.py
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import config
from routes import router

app = FastAPI(title="X2 Report Python Backend")

# CORS (dev): allow the Angular dev server / proxy — same headers as the Go service.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Origin", "Content-Type", "Authorization", "X-Tenant-ID"],
)

# Everything under ROUTER_PATH (/api), so /api/health and /api/report/*.
app.include_router(router, prefix=config.router_path)


if __name__ == "__main__":
    host, _, port = config.server_address.partition(":")
    uvicorn.run("main:app", host=host or "0.0.0.0", port=int(port or 8090), reload=True)
