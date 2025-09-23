import sys
from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


def main():
    transport = RequestsHTTPTransport(url="http://localhost:8000/graphql", verify=False)
    client = Client(transport=transport, fetch_schema_from_transport=False)

    query = gql(
        """
        query Recent($days: Int){
          ordersRecent(days: $days){
            id
            customer { email }
          }
        }
        """
    )

    result = client.execute(query, variable_values={"days": 7})
    orders = result.get("ordersRecent", [])
    ts = datetime.utcnow().strftime('%d/%m/%Y-%H:%M:%S')
    with open('/tmp/order_reminders_log.txt', 'a') as f:
        for o in orders:
            f.write(f"{ts} Reminder -> order {o['id']} to {o['customer']['email']}\n")

    print("Order reminders processed!")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import sys
from datetime import timedelta
from datetime import datetime, timezone as dt_timezone
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

LOG_FILE = "/tmp/order_reminders_log.txt"
ENDPOINT = "http://localhost:8000/graphql"

def timestamp():
    return datetime.now(dt_timezone.utc).strftime('%d/%m/%Y-%H:%M:%S')


def main():
    transport = RequestsHTTPTransport(url=ENDPOINT, verify=True, retries=3)
    client = Client(transport=transport, fetch_schema_from_transport=False)

    query = gql(
        """
        query PendingOrdersLastWeek {
          pendingOrdersLastWeek {
            id
            customer { email }
          }
        }
        """
    )

    try:
        result = client.execute(query)
        items = result.get("pendingOrdersLastWeek", [])
    except Exception as e:
        items = []
        with open(LOG_FILE, 'a') as f:
            f.write(f"{timestamp()} Error fetching orders: {e}\n")

    with open(LOG_FILE, 'a') as f:
        for o in items:
            cid = o.get('id')
            email = (o.get('customer') or {}).get('email')
            f.write(f"{timestamp()} Reminder -> order_id={cid}, customer_email={email}\n")

    print("Order reminders processed!")


if __name__ == "__main__":
    main()
