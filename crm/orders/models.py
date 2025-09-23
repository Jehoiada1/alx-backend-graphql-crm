from django.db import models
from crm.customers.models import Customer
from crm.products.models import Product

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order_date = models.DateTimeField()
    status = models.CharField(max_length=50, default='pending')

    def __str__(self):
        return f"Order {self.id} - {self.customer.email}"
