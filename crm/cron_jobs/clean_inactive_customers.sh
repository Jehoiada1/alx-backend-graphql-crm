#!/bin/bash
set -euo pipefail

# Resolve project root (this script is expected in crm/cron_jobs)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# Run a Django shell snippet that removes customers with no orders since a year ago
DELETED_COUNT=$(python manage.py shell <<'PY'
from django.utils import timezone
from datetime import timedelta
from django.db.models import Exists, OuterRef
from crm.models import Customer, Order

cutoff = timezone.now() - timedelta(days=365)
recent_orders = Order.objects.filter(customer=OuterRef('pk'), order_date__gte=cutoff)
inactive_customers = Customer.objects.annotate(has_recent=Exists(recent_orders)).filter(has_recent=False)
count = inactive_customers.count()
inactive_customers.delete()
print(count)
PY
)

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "$TIMESTAMP Deleted inactive customers: $DELETED_COUNT" >> /tmp/customer_cleanup_log.txt
