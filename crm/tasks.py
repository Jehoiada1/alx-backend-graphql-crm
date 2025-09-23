from datetime import datetime
from celery import shared_task
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport


@shared_task(name='crm.tasks.generate_crm_report')
def generate_crm_report():
    transport = RequestsHTTPTransport(url="http://localhost:8000/graphql", verify=False)
    client = Client(transport=transport, fetch_schema_from_transport=False)

    query = gql(
        """
        query CRMReport {
          customersCount
          ordersCount
          ordersRevenue
        }
        """
    )

    try:
        data = client.execute(query)
        customers_count = data.get('customersCount', 0)
        orders_count = data.get('ordersCount', 0)
        revenue = data.get('ordersRevenue', 0)
    except Exception as e:
        customers_count = orders_count = revenue = f"error: {e}"

    ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    with open('/tmp/crm_report_log.txt', 'a') as f:
        f.write(f"{ts} - Report: {customers_count} customers, {orders_count} orders, {revenue} revenue\n")
