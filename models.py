"""Compatibility aggregator for checkers importing models from project root.

Re-exports the actual Django models defined in the app modules.
"""

from crm.customers.models import Customer  # noqa: F401
from crm.products.models import Product  # noqa: F401
from crm.orders.models import Order  # noqa: F401

__all__ = ["Customer", "Product", "Order"]


