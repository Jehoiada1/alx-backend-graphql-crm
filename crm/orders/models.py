from django.db import models
from crm.customers.models import Customer
from crm.products.models import Product
from decimal import Decimal


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, related_name="orders")
    order_date = models.DateTimeField()
    status = models.CharField(max_length=50, default='pending')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["-order_date"]

    def calculate_total(self):
        total = Decimal("0")
        for p in self.products.all():
            total += p.price or 0
        self.total_amount = total
        return total

    def __str__(self):  # pragma: no cover - trivial
        return f"Order {self.id} - {self.customer.email}"
