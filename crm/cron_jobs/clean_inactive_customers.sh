#!/bin/bash
# Deletes customers with no orders in the past year and logs the count
set -e

PYTHON_BIN=${PYTHON_BIN:-python}
PROJECT_DIR="$(cd "$(dirname "$0")"/../.. && pwd)"
cd "$PROJECT_DIR"

$PYTHON_BIN manage.py shell <<'PYCODE'
import sys
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from crm.customers.models import Customer
from crm.orders.models import Order

cutoff = timezone.now() - timedelta(days=365)
# Customers with any recent order
active_ids = Order.objects.filter(order_date__gte=cutoff).values_list('customer_id', flat=True).distinct()
# Inactive customers are those NOT in active_ids
inactive_qs = Customer.objects.exclude(id__in=list(active_ids))
deleted_count = inactive_qs.count()
inactive_qs.delete()

with open('/tmp/customer_cleanup_log.txt', 'a') as f:
    f.write(f"{timezone.now().strftime('%d/%m/%Y-%H:%M:%S')} Deleted customers: {deleted_count}\n")

print(deleted_count)
PYCODE

exit 0#!/bin/bash
# Deletes customers with no orders since a year ago and logs the count

set -e

PROJECT_DIR="$(cd "$(dirname "$0")"/../.. && pwd)"
LOG_FILE="/tmp/customer_cleanup_log.txt"

cd "$PROJECT_DIR"

COUNT=$(DJANGO_SETTINGS_MODULE=crm.settings python manage.py shell -c "from django.utils import timezone; from datetime import timedelta; from customers.models import Customer; from orders.models import Order; cutoff=timezone.now()-timedelta(days=365); ids=Customer.objects.exclude(order__order_date__gte=cutoff).values_list('id', flat=True); deleted=Customer.objects.filter(id__in=list(ids)).delete(); print(deleted[0])")

echo "$(date +'%d/%m/%Y-%H:%M:%S') Deleted customers: $COUNT" >> "$LOG_FILE"
