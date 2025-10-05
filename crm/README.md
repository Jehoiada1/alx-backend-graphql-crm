# CRM Celery Setup

## Prerequisites
- Redis running locally on port 6379
- Python dependencies installed:
  - `pip install -r requirements.txt`

## Migrations
- Apply database migrations:
  - `python manage.py migrate`

## Start services
- Start Celery worker:
  - `celery -A crm worker -l info`
- Start Celery Beat scheduler:
  - `celery -A crm beat -l info`

## Verify
- After the scheduled time (Monday 06:00 UTC), check the log file:
  - `/tmp/crm_report_log.txt`

If you want to run the task immediately:
- Open Django shell and trigger the task:
  - `from crm.tasks import generate_crm_report; generate_crm_report.delay()`