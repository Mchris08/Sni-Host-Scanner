import json
from app.db import SessionLocal, HostSubmission

def submit_zim_hosts_for_review(results, job_id=None):
    db = SessionLocal()
    try:
        inserted = 0
        for r in results:
            if not (r.get("is_zimbabwe") and r.get("status") == "working"):
                continue
            existing = db.query(HostSubmission).filter_by(
                host=r["host"], port=r["port"]).first()
            if existing:
                existing.score = r["score"]
                existing.grade = r["grade"]
                existing.latency_ms = r.get("latency_ms")
                existing.stability = r.get("stability", 0.0)
                existing.tunnel_ready = r.get("tunnel_ready", False)
                existing.best_protocol = r.get("best_protocol")
                existing.sni_working = r.get("sni_working")
                existing.raw_json = json.dumps(r)
                continue
            db.add(HostSubmission(
                scan_job_id=job_id,
                host=r["host"], port=r["port"],
                sni_working=r.get("sni_working"),
                best_protocol=r.get("best_protocol"),
                score=r["score"], grade=r["grade"],
                latency_ms=r.get("latency_ms"),
                stability=r.get("stability", 0.0),
                tunnel_ready=r.get("tunnel_ready", False),
                is_zimbabwe=True,
                raw_json=json.dumps(r),
                payload_json="{}",
                status="pending",
            ))
            inserted += 1
        db.commit()
        print(f"[queue] {inserted} new Zim hosts pending review")
    finally:
        db.close()
