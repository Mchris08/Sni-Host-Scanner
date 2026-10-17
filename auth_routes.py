from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeTimedSerializer
from app.db import SessionLocal, User
from app.auth import hash_password, verify_password, create_session_token, SECRET_KEY
from app.email import send_verification, send_reset

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
email_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="email")

@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@router.post("/signup")
def signup(request: Request, email: str = Form(...),
           password: str = Form(...), password2: str = Form(...)):
    if password != password2:
        return templates.TemplateResponse("signup.html",
            {"request": request, "error": "Passwords do not match"})
    if len(password) < 8:
        return templates.TemplateResponse("signup.html",
            {"request": request, "error": "Password must be at least 8 characters"})
    db = SessionLocal()
    try:
        if db.query(User).filter_by(email=email.lower()).first():
            return templates.TemplateResponse("signup.html",
                {"request": request, "error": "Email already registered"})
        u = User(email=email.lower(), password_hash=hash_password(password))
        db.add(u); db.commit(); db.refresh(u)
        token = email_serializer.dumps({"uid": u.id, "email": u.email})
        send_verification(u.email, token)
        return templates.TemplateResponse("verify.html",
            {"request": request, "email": u.email})
    finally:
        db.close()

@router.get("/verify")
def verify(token: str):
    try:
        data = email_serializer.loads(token, max_age=60*60*24)
    except Exception:
        raise HTTPException(400, "Invalid or expired token")
    db = SessionLocal()
    try:
        u = db.query(User).get(data["uid"])
        if not u: raise HTTPException(404, "User not found")
        u.is_verified = True; db.commit()
    finally:
        db.close()
    return RedirectResponse("/login?verified=1", status_code=303)

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, verified: int = 0):
    return templates.TemplateResponse("login.html",
        {"request": request, "verified": verified})

@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    try:
        u = db.query(User).filter_by(email=email.lower()).first()
    finally:
        db.close()
    if not u or not verify_password(password, u.password_hash):
        return templates.TemplateResponse("login.html",
            {"request": request, "error": "Invalid credentials"})
    if not u.is_verified:
        return templates.TemplateResponse("login.html",
            {"request": request, "error": "Please verify your email first"})
    token = create_session_token(u.id)
    resp = RedirectResponse("/dashboard", status_code=303)
    resp.set_cookie("session", token, httponly=True, samesite="lax",
                    secure=False, max_age=60*60*24*7)
    return resp

@router.post("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie("session")
    return resp

@router.get("/reset", response_class=HTMLResponse)
def reset_page(request: Request, token: str = ""):
    return templates.TemplateResponse("reset.html",
        {"request": request, "token": token})

@router.post("/reset")
def reset_submit(token: str = Form(...), password: str = Form(...)):
    try:
        data = email_serializer.loads(token, max_age=60*60)
    except Exception:
        raise HTTPException(400, "Invalid or expired token")
    if len(password) < 8:
        raise HTTPException(400, "Password too short")
    db = SessionLocal()
    try:
        u = db.query(User).get(data["uid"])
        if not u: raise HTTPException(404, "User not found")
        u.password_hash = hash_password(password); db.commit()
    finally:
        db.close()
    return RedirectResponse("/login", status_code=303)

@router.post("/forgot")
def forgot(email: str = Form(...)):
    db = SessionLocal()
    try:
        u = db.query(User).filter_by(email=email.lower()).first()
    finally:
        db.close()
    if u:
        token = email_serializer.dumps({"uid": u.id, "email": u.email})
        send_reset(u.email, token)
    return RedirectResponse("/login", status_code=303)
