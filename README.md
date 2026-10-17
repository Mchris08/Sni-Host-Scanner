# Zim Host Scanner

Daily re-verification of publicly-published proxy/VPN hosts, Zimbabwe-prioritized,
with admin-only moderation before distribution.

## Scope
- Fetches publicly-published configs (ProxyScrape ZW, public GitHub config repos)
- Filters to Zimbabwean IP ranges (Econet, NetOne, ZOL, Liquid, TelOne, + more)
- Bulk-scans TCP → TLS/SNI → protocol detection → latency → stability
- Working Zim hosts go to an admin moderation queue; only approved hosts are shown to users

## Out of scope (by design)
- Does not scan IPs it does not own without authorization
- Does not scan zero-rated / SNI bug hosts
- Does not auto-approve — admin-only

## Local run
    python -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env      # edit: SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD, SMTP
    python -c "import app.bootstrap; app.bootstrap.ensure_admin()"
    uvicorn app.main:app --reload --port 8000

## Manual scan
    python -m jobs.daily_zim

## Deploy
- Render/Railway: connect repo, set env vars, Procfile is auto-detected
- Cron: `0 3 * * * cd /opt/scanner && venv/bin/python -m jobs.daily_zim >> logs/zim.log 2>&1`

## Legal
Only scan hosts you own or have written authorization for. Public feed
re-verification is limited to configs explicitly published for public use.
