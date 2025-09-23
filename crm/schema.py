import graphene
from graphene_django import DjangoObjectType
from crm.models import Product
from crm.customers.models import Customer
from crm.orders.models import Order


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "stock")


class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "email", "created_at")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "order_date", "status", "customer")


class Query(graphene.ObjectType):
    hello = graphene.String(description="Simple hello field")
    orders_recent = graphene.List(OrderType, days=graphene.Int(default_value=7), description="Pending orders within last N days")
    customers_count = graphene.Int(name='customersCount')
    orders_count = graphene.Int(name='ordersCount')
    orders_revenue = graphene.Float(name='ordersRevenue')

    def resolve_hello(root, info):
        return "Hello from CRM!"

    def resolve_orders_recent(root, info, days=7):
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=days)
        return Order.objects.select_related('customer').filter(status='pending', order_date__gte=cutoff).order_by('-order_date')

    def resolve_customers_count(root, info):
        from django.db.models import Count
        return Customer.objects.count()

    def resolve_orders_count(root, info):
        return Order.objects.count()

    def resolve_orders_revenue(root, info):
        from django.db.models import Sum
        # Assume Order has a field total_amount; if not, sum 0
        if hasattr(Order, 'total_amount'):
            agg = Order.objects.aggregate(total=Sum('total_amount'))
            return float(agg.get('total') or 0)
        return 0.0


class UpdateLowStockProducts(graphene.Mutation):
    class Arguments:
        increment_by = graphene.Int(required=False, default_value=10)
        threshold = graphene.Int(required=False, default_value=10)

    ok = graphene.Boolean()
    message = graphene.String()
    updated_products = graphene.List(ProductType)

    @classmethod
    def mutate(cls, root, info, increment_by=10, threshold=10):
        to_update = Product.objects.filter(stock__lt=threshold)
        updated = []
        for p in to_update:
            p.stock = (p.stock or 0) + increment_by
            p.save(update_fields=["stock"])
            updated.append(p)
        msg = f"Updated {len(updated)} low-stock products"
        return UpdateLowStockProducts(ok=True, message=msg, updated_products=updated)


class Mutation(graphene.ObjectType):
    update_low_stock_products = UpdateLowStockProducts.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
