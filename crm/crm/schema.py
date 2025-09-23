import graphene
from graphene_django import DjangoObjectType
from django.utils import timezone
from products.models import Product
from orders.schema import Query as OrdersQuery

class HelloType(graphene.ObjectType):
    message = graphene.String()

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "stock")

class RootQuery(OrdersQuery, graphene.ObjectType):
    hello = graphene.String(description="Simple hello field")

    def resolve_hello(root, info):
        return "Hello from CRM!"

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

schema = graphene.Schema(query=RootQuery, mutation=Mutation)
