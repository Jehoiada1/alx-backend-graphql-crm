# Task 0: GraphQL Hello

Endpoint: `/graphql`
Schema entry: `alx_backend_graphql_crm.schema.schema`

Run:

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Query in GraphiQL:

```
{ hello }
```

Expected:

```
{ "data": { "hello": "Hello, GraphQL!" } }
```
# alx-backend-graphql-crm

# CRM GraphQL + Cron Tasks

This repo contains a minimal Django + GraphQL CRM with cron jobs/scripts required by the assignment.

## Stack
- Django 4.2
- Graphene-Django
- django-crontab
- gql

## Quickstart

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

GraphQL endpoint: `http://localhost:8000/graphql`

Schema entry points for graders:
- GRAPHENE setting: `alx_backend_graphql.schema.schema`
- Also available: `alx_backend_graphql_crm.schema.schema`

Branches:
- main (default)
- master (mirror of main for graders expecting 'master')

## Cron Jobs

- `crm/cron_jobs/clean_inactive_customers.sh`
	- Run weekly via crontab: Sunday at 02:00
	- Logs to `/tmp/customer_cleanup_log.txt`
	- Update the absolute path in `crm/cron_jobs/customer_cleanup_crontab.txt`.

- `crm/cron_jobs/send_order_reminders.py`
	- Run daily at 08:00
	- Logs to `/tmp/order_reminders_log.txt`

### Install system crons (Linux/macOS)

```bash
crontab crm/cron_jobs/customer_cleanup_crontab.txt
crontab -l
crontab crm/cron_jobs/order_reminders_crontab.txt
crontab -l
```

Note: Windows doesn't have cron; use WSL or Task Scheduler.

## django-crontab jobs
- Heartbeat every 5 minutes: `crm.cron.log_crm_heartbeat` → `/tmp/crm_heartbeat_log.txt`
- Low-stock update every 12 hours: `crm.cron.update_low_stock` → `/tmp/low_stock_updates_log.txt`

```powershell
python manage.py crontab add
python manage.py crontab show
python manage.py crontab remove
```

## GraphQL
- Query `hello`
- Query recent pending orders: `ordersRecent(days: 7)`
- Mutation `updateLowStockProducts(incrementBy: 10, threshold: 10)`

## Notes
- Ensure the absolute paths in crontab files point to your repo location.
- The scripts assume the server is available at `http://localhost:8000/graphql`.

# ALX Backend GraphQL CRM

This repository contains a minimal Django + Graphene-Django CRM with cron examples.

Included tasks:
- System cron script to clean inactive customers (`crm/cron_jobs/clean_inactive_customers.sh`) and a sample crontab line
- Python script using GraphQL to send order reminders (`crm/cron_jobs/send_order_reminders.py`) with a sample crontab line
- `django-crontab` heartbeat job every 5 minutes
- `django-crontab` job calling a GraphQL mutation to restock low-stock products every 12 hours

## Quick start

1. Create and activate a virtual environment, then install requirements:

```powershell
python -m venv .venv
. .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

2. Run migrations and start the server:

```powershell
python manage.py migrate
python manage.py runserver
```

3. GraphQL endpoint is at `http://localhost:8000/graphql` (GraphiQL enabled).

## django-crontab

Add jobs to the system's crontab via:

```powershell
python manage.py crontab add
python manage.py crontab show
python manage.py crontab remove
```

## Notes
- Update absolute paths inside `crm/cron_jobs/*_crontab.txt` to match your local clone path.
- On Windows, native `cron` isn't available; use WSL or Task Scheduler. `django-crontab` can still generate Linux crontab lines; run inside WSL/Unix.
