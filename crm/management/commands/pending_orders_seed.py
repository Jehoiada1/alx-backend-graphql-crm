from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from customers.models import Customer
from products.models import Product
from orders.models import Order

class Command(BaseCommand):
    help = 'Seed some pending orders for testing'

    def handle(self, *args, **options):
        c, _ = Customer.objects.get_or_create(email='test@example.com')
        p, _ = Product.objects.get_or_create(name='Widget', defaults={'stock': 5})
        Order.objects.get_or_create(customer=c, product=p, order_date=timezone.now() - timedelta(days=3), defaults={'status': 'pending'})
        self.stdout.write(self.style.SUCCESS('Seeded test pending order'))
