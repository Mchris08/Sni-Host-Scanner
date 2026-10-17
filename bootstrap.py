import os, secrets
from app.db import SessionLocal, User
from app.auth import hash_password

def ensure_admin():
    email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    pw = os.environ.get("ADMIN_PASSWORD", "")
    if not email:
        print("[bootstrap] ADMIN_EMAIL not set — skipping admin creation")
        return
    db = SessionLocal()
    try:
        existing = db.query(User).filter_by(email=email).first()
        if existing:
            if existing.role != "admin":
                existing.role = "admin"; db.commit()
            return
        if not pw:
            pw = secrets.token_urlsafe(16)
            print("=" * 60)
            print("[bootstrap] FIRST-RUN ADMIN CREATED")
            print(f"  email:    {email}")
            print(f"  password: {pw}")
            print("  Save this now. Change it after first login.")
            print("=" * 60)
        db.add(User(email=email, password_hash=hash_password(pw),
                    role="admin", is_verified=True, is_active=True))
        db.commit()
        print(f"[bootstrap] admin '{email}' created")
    finally:
        db.close()
