from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.bootstrap import ensure_admin
from app.routes.auth_routes import router as auth_router
from app.routes.scan_routes import router as scan_router
from app.routes.admin_routes import router as admin_router

@asynccontextmanager
async def lifespan(app):
    ensure_admin()
    yield

app = FastAPI(title="Zim Host Scanner", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(auth_router)
app.include_router(scan_router)
app.include_router(admin_router)
