# Celery + Celery Beat for CRM Reports

This app configures a Celery task scheduled by Celery Beat to generate a weekly CRM report.

## Requirements
- Redis running locally (broker and backend): `redis://localhost:6379/0`
- Dependencies from `requirements.txt`

## Install
```powershell
# from repo root
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
```

## Run Redis
- Windows: install Redis via WSL/Docker or native port.
- Linux/macOS:
```bash
redis-server
```

## Start Celery worker
```powershell
celery -A crm worker -l info
```

## Start Celery Beat
```powershell
celery -A crm beat -l info
```

The schedule is defined in `crm/settings.py` using `CELERY_BEAT_SCHEDULE`:
- Task: `crm.tasks.generate_crm_report`
- When: Mondays at 06:00 (server local time)

## Task behavior
- GraphQL query fields: `customersCount`, `ordersCount`, `ordersRevenue`
- Log destination: `/tmp/crm_report_log.txt`
- Log format: `YYYY-MM-DD HH:MM:SS - Report: X customers, Y orders, Z revenue`

## Troubleshooting
- Ensure Django server is running at `http://localhost:8000/graphql` for the GraphQL query.
- Verify Redis is reachable at `redis://localhost:6379/0`.
- Check logs: `/tmp/crm_report_log.txt`
