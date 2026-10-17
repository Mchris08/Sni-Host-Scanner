from sqlalchemy import (create_engine, Column, Integer, String, Boolean,
                        DateTime, ForeignKey, Text, Float, CheckConstraint)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

engine = create_engine("sqlite:///./app.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ScanJob(Base):
    __tablename__ = "scan_jobs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    region = Column(String, default="zim")
    status = Column(String, default="pending")
    summary_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

class HostSubmission(Base):
    __tablename__ = "host_submissions"
    __table_args__ = (
        CheckConstraint("is_zimbabwe = 0 OR status IN ('pending','approved','rejected')",
                        name="zim_status_valid"),
        CheckConstraint("status != 'approved' OR reviewed_by IS NOT NULL",
                        name="approved_requires_reviewer"),
        CheckConstraint("status != 'rejected' OR reviewed_by IS NOT NULL",
                        name="rejected_requires_reviewer"),
    )
    id = Column(Integer, primary_key=True)
    scan_job_id = Column(Integer, ForeignKey("scan_jobs.id"), nullable=True)
    host = Column(String, nullable=False, index=True)
    port = Column(Integer, nullable=False)
    sni_working = Column(String)
    best_protocol = Column(String)
    score = Column(Integer, default=0)
    grade = Column(String, default="F")
    latency_ms = Column(Float)
    stability = Column(Float, default=0.0)
    tunnel_ready = Column(Boolean, default=False)
    is_zimbabwe = Column(Boolean, default=True)
    raw_json = Column(Text, default="{}")
    payload_json = Column(Text, default="{}")
    status = Column(String, default="pending")
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ModerationLog(Base):
    __tablename__ = "moderation_log"
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String)
    target_type = Column(String)
    target_id = Column(Integer)
    detail = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)
