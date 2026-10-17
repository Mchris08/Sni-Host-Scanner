from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.auth import require_user
from app.db import SessionLocal, ScanJob
import json, os, asyncio, subprocess

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return RedirectResponse("/dashboard" if request.cookies.get("session") else "/login")

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user=Depends(require_user)):
    db = SessionLocal()
    try:
        jobs = db.query(ScanJob).order_by(ScanJob.created_at.desc()).limit(20).all()
    finally:
        db.close()
    working = []
    if os.path.exists("output/public/working.json"):
        working = json.load(open("output/public/working.json"))
    summary = {}
    if os.path.exists("output/summary.json"):
        summary = json.load(open("output/summary.json"))
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "user": user, "jobs": jobs, "summary": summary,
        "zim_hosts": [h for h in working if h.get("is_zimbabwe")],
        "glob_hosts": [h for h in working if not h.get("is_zimbabwe")],
    })

@router.post("/scan/run")
async def run_scan(request: Request, user=Depends(require_user)):
    db = SessionLocal()
    try:
        job = ScanJob(user_id=user.id, status="running")
        db.add(job); db.commit(); db.refresh(job)
        job_id = job.id
    finally:
        db.close()
    asyncio.create_task(_run_bg(job_id))
    return RedirectResponse("/dashboard", status_code=303)

async def _run_bg(job_id):
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, lambda: subprocess.run(
            ["python", "-m", "jobs.daily_zim"], capture_output=True, timeout=3600))
        status = "done"
    except Exception:
        status = "failed"
    db = SessionLocal()
    try:
        j = db.query(ScanJob).get(job_id)
        if j: j.status = status; db.commit()
    finally:
        db.close()
