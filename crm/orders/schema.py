import graphene
from graphene_django import DjangoObjectType
from django.utils import timezone
from datetime import timedelta
from .models import Order

class CustomerType(graphene.ObjectType):
    email = graphene.String()

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "order_date", "status")

    customer = graphene.Field(CustomerType)

    def resolve_customer(self, info):
        return CustomerType(email=self.customer.email)

class Query(graphene.ObjectType):
    pending_orders_last_week = graphene.List(OrderType, name='pendingOrdersLastWeek')

    def resolve_pending_orders_last_week(root, info):
        cutoff = timezone.now() - timedelta(days=7)
        return Order.objects.filter(status='pending', order_date__gte=cutoff)
