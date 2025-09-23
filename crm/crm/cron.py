import datetime
from django.utils import timezone


def _timestamp():
    return timezone.now().strftime('%d/%m/%Y-%H:%M:%S')


def log_crm_heartbeat():
    ts = _timestamp()
    with open('/tmp/crm_heartbeat_log.txt', 'a') as f:
        f.write(f"{ts} CRM is alive\n")


def update_low_stock():
    # This function will be wired to call the GraphQL mutation via HTTP
    import requests
    import json

    query = '''
    mutation UpdateLowStock($inc: Int, $th: Int){
      updateLowStockProducts(incrementBy: $inc, threshold: $th){
        ok
        message
        updatedProducts{ id name stock }
      }
    }
    '''
    variables = {"inc": 10, "th": 10}

    try:
        resp = requests.post('http://localhost:8000/graphql', json={'query': query, 'variables': variables})
        data = resp.json()
    except Exception as e:
        data = {"error": str(e)}

    ts = _timestamp()
    with open('/tmp/low_stock_updates_log.txt', 'a') as f:
        f.write(f"{ts} {data}\n")
