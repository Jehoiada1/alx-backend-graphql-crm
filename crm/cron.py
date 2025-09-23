from django.utils import timezone
from gql.transport.requests import RequestsHTTPTransport
from gql import gql, Client


def _timestamp():
    return timezone.now().strftime('%d/%m/%Y-%H:%M:%S')


def log_crm_heartbeat():
    ts = _timestamp()
    # Optionally query GraphQL hello to verify endpoint responsiveness
    try:
        transport = RequestsHTTPTransport(url="http://localhost:8000/graphql", verify=False)
        client = Client(transport=transport, fetch_schema_from_transport=False)
        result = client.execute(gql("query { hello }"))
        hello = result.get('hello', 'unknown')
    except Exception:
        hello = 'unavailable'
    with open('/tmp/crm_heartbeat_log.txt', 'a') as f:
        f.write(f"{ts} CRM is alive ({hello})\n")


def update_low_stock():
    import requests
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
