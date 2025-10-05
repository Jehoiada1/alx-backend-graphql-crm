import os
import sys
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm.settings")
import django  # noqa: E402

django.setup()

from crm.models import Customer, Product, Order  # noqa: E402


def main():
    # Customers
    alice, _ = Customer.objects.get_or_create(name="Alice", email="alice@example.com", phone="+1234567890")
    bob, _ = Customer.objects.get_or_create(name="Bob", email="bob@example.com")

    # Products
    laptop, _ = Product.objects.get_or_create(name="Laptop", defaults={"price": Decimal("999.99"), "stock": 10})
    mouse, _ = Product.objects.get_or_create(name="Mouse", defaults={"price": Decimal("19.99"), "stock": 100})

    # Order
    order = Order.objects.create(customer=alice)
    order.products.set([laptop, mouse])
    order.total_amount = laptop.price + mouse.price
    order.save()
    print("Seeded sample data.")


if __name__ == "__main__":
    main()
