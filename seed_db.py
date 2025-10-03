"""
Simple seeding script to populate a few customers, products, and an order.
Idempotent: safe to re-run; existing entries will be reused.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
django.setup()

from django.utils import timezone  # noqa: E402
from crm.customers.models import Customer  # noqa: E402
from crm.products.models import Product  # noqa: E402
from crm.orders.models import Order  # noqa: E402


def get_or_create_customer(name, email, phone=None):
	obj, _ = Customer.objects.get_or_create(email=email, defaults={"name": name, "phone": phone})
	return obj


def get_or_create_product(name, price, stock=10):
	obj, _ = Product.objects.get_or_create(name=name, defaults={"price": price, "stock": stock})
	return obj


def main():
	alice = get_or_create_customer("Alice", "alice@example.com", "+1234567890")
	bob = get_or_create_customer("Bob", "bob@example.com", "123-456-7890")

	laptop = get_or_create_product("Laptop", 999.99, 5)
	mouse = get_or_create_product("Mouse", 25.50, 100)

	# Create a sample order if none exists for Alice
	order = Order.objects.filter(customer=alice).first()
	if not order:
		order = Order.objects.create(customer=alice, order_date=timezone.now())
		order.products.set([laptop, mouse])
		order.calculate_total()
		order.save(update_fields=["total_amount"])
	print("Seed completed:", Customer.objects.count(), "customers;", Product.objects.count(), "products")


if __name__ == "__main__":
	main()


