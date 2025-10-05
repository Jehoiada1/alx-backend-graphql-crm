import json
import logging
from datetime import datetime

import requests
from celery import shared_task


GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"
LOG_PATH = "/tmp/crm_report_log.txt"


def _fetch_counts():
    query = {
        "query": (
            "query {\n"
            "  customers: allCustomers { totalCount }\n"
            "  orders: allOrders { totalCount }\n"
            "  revenue: allOrders { edges { node { totalAmount } } }\n"
            "}"
        )
    }
    headers = {"Content-Type": "application/json"}
    resp = requests.post(GRAPHQL_ENDPOINT, data=json.dumps(query), headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json().get("data", {})

    customers_total = (data.get("customers") or {}).get("totalCount", 0)
    orders_total = (data.get("orders") or {}).get("totalCount", 0)
    # Sum revenue from edges
    revenue_edges = (data.get("revenue") or {}).get("edges", [])
    revenue_sum = 0
    for edge in revenue_edges:
        node = edge.get("node") or {}
        amt = node.get("totalAmount")
        try:
            revenue_sum += float(amt)
        except (TypeError, ValueError):
            continue
    return int(customers_total), int(orders_total), revenue_sum


@shared_task(name="crm.tasks.generate_crm_report")
def generate_crm_report():
    customers, orders, revenue = _fetch_counts()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} - Report: {customers} customers, {orders} orders, {revenue} revenue"
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        logging.exception("Failed to write CRM report log: %s", e)
    return line
