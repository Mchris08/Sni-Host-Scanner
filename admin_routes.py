from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
import json, os
from app.admin import require_admin
from app.db import SessionLocal, HostSubmission, User, ModerationLog
from payloads.generators import generate_payload

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")

def _log(db, aid, action, ttype, tid, detail=""):
    db.add(ModerationLog(admin_id=aid, action=action,
                         target_type=ttype, target_id=tid, detail=detail))

@router.get("/queue", response_class=HTMLResponse)
def queue(request: Request, admin=Depends(require_admin), status: str = "pending"):
    if status not in ("pending", "approved", "rejected"): status = "pending"
    db = SessionLocal()
    try:
        q = db.query(HostSubmission).filter_by(status=status, is_zimbabwe=True)\
              .order_by(HostSubmission.score.desc()).all()
        counts = {s: db.query(HostSubmission).filter_by(status=s, is_zimbabwe=True).count()
                  for s in ("pending", "approved", "rejected")}
    finally:
        db.close()
    return templates.TemplateResponse("admin_queue.html",
        {"request": request, "admin": admin, "hosts": q,
         "counts": counts, "current": status})

@router.post("/queue/approve/{hid}")
def approve(hid: int, admin=Depends(require_admin)):
    db = SessionLocal()
    try:
        h = db.query(HostSubmission).get(hid)
        if not h or not h.is_zimbabwe: raise HTTPException(404)
        raw = json.loads(h.raw_json or "{}")
        h.payload_json = json.dumps(generate_payload(raw, {}))
        h.status = "approved"; h.reviewed_by = admin.id
        h.reviewed_at = datetime.utcnow(); h.rejection_reason = None
        _log(db, admin.id, "approve", "host", hid, f'{h.host}:{h.port}')
        db.commit()
    finally:
        db.close()
    _rebuild(); return RedirectResponse("/admin/queue", status_code=303)

@router.post("/queue/reject/{hid}")
def reject(hid: int, reason: str = Form(""), admin=Depends(require_admin)):
    db = SessionLocal()
    try:
        h = db.query(HostSubmission).get(hid)
        if not h or not h.is_zimbabwe: raise HTTPException(404)
        h.status = "rejected"; h.rejection_reason = reason or "rejected"
        h.reviewed_by = admin.id; h.reviewed_at = datetime.utcnow()
        h.payload_json = "{}"
        _log(db, admin.id, "reject", "host", hid, f'{h.host}:{h.port} {reason}')
        db.commit()
    finally:
        db.close()
    _rebuild(); return RedirectResponse("/admin/queue", status_code=303)

@router.post("/queue/bulk")
def bulk(action: str = Form(...), min_score: int = Form(0), admin=Depends(require_admin)):
    if action not in ("approve", "reject"): raise HTTPException(400)
    db = SessionLocal()
    try:
        q = db.query(HostSubmission).filter_by(status="pending", is_zimbabwe=True)\
              .filter(HostSubmission.score >= min_score)
        for h in q:
            if action == "approve":
                raw = json.loads(h.raw_json or "{}")
                h.payload_json = json.dumps(generate_payload(raw, {}))
                h.status = "approved"
            else:
                h.status = "rejected"; h.payload_json = "{}"
            h.reviewed_by = admin.id; h.reviewed_at = datetime.utcnow()
            _log(db, admin.id, f"bulk_{action}", "host", h.id, f'{h.host}:{h.port}')
        db.commit()
    finally:
        db.close()
    _rebuild(); return RedirectResponse("/admin/queue", status_code=303)

def _rebuild():
    db = SessionLocal()
    try:
        approved = db.query(HostSubmission).filter_by(
            status="approved", is_zimbabwe=True)\
            .order_by(HostSubmission.score.desc()).all()
        out = []
        for h in approved:
            raw = json.loads(h.raw_json or "{}")
            p = json.loads(h.payload_json or "{}")
            raw.update({"approved_by": h.reviewed_by,
                        "approved_at": h.reviewed_at.isoformat() if h.reviewed_at else None,
                        "payloads": p.get("payloads", {})})
            out.append(raw)
        os.makedirs("output/public", exist_ok=True)
        json.dump(out, open("output/public/working.json", "w"), indent=2)
        json.dump(out, open("output/public/working_zim.json", "w"), indent=2)
    finally:
        db.close()

@router.get("/users", response_class=HTMLResponse)
def users(request: Request, admin=Depends(require_admin)):
    db = SessionLocal()
    try:
        us = db.query(User).order_by(User.created_at.desc()).all()
    finally:
        db.close()
    return templates.TemplateResponse("admin_users.html",
        {"request": request, "admin": admin, "users": us})

@router.post("/users/toggle/{uid}")
def toggle(uid: int, admin=Depends(require_admin)):
    if uid == admin.id: return RedirectResponse("/admin/users", status_code=303)
    db = SessionLocal()
    try:
        u = db.query(User).get(uid)
        if u:
            u.is_active = not u.is_active
            _log(db, admin.id, "toggle_user", "user", uid, u.email)
            db.commit()
    finally:
        db.close()
    return RedirectResponse("/admin/users", status_code=303)

@router.get("/log", response_class=HTMLResponse)
def log_view(request: Request, admin=Depends(require_admin)):
    db = SessionLocal()
    try:
        logs = db.query(ModerationLog).order_by(ModerationLog.created_at.desc()).limit(500).all()
    finally:
        db.close()
    return templates.TemplateResponse("admin_log.html",
        {"request": request, "admin": admin, "logs": logs})
