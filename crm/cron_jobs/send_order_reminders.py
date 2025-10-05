#!/usr/bin/env python3
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport


GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"
LOG_PATH = "/tmp/order_reminders_log.txt"


async def fetch_recent_orders():
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)

    # Convert to ISO 8601 strings with Zulu timezone
    now_iso = now.isoformat().replace("+00:00", "Z")
    gte_iso = seven_days_ago.isoformat().replace("+00:00", "Z")

    transport = AIOHTTPTransport(url=GRAPHQL_ENDPOINT)
    async with Client(transport=transport, fetch_schema_from_transport=False) as session:
        query = gql(
            """
            query ($filters: OrderFilterInput) {
              allOrders(filter: $filters) {
                edges {
                  node {
                    id
                    orderDate
                    customer { email }
                  }
                }
              }
            }
            """
        )
        variables = {
            "filters": {
                "orderDateGte": gte_iso,
                "orderDateLte": now_iso,
            }
        }
        result = await session.execute(query, variable_values=variables)
        return result


def log_reminders(result):
    edges = (
        result.get("allOrders", {})
        .get("edges", [])
    )
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = []
    for edge in edges:
        node = edge.get("node", {})
        order_id = node.get("id")
        email = (node.get("customer") or {}).get("email")
        lines.append(f"{timestamp} Reminder for order {order_id} -> {email}")

    if lines:
        # Ensure directory exists (typically /tmp exists by default)
        Path(LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")


async def main():
    result = await fetch_recent_orders()
    log_reminders(result)
    print("Order reminders processed!")


if __name__ == "__main__":
    asyncio.run(main())
