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


import re
from decimal import Decimal, InvalidOperation
import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from crm.customers.models import Customer
from crm.products.models import Product
from crm.orders.models import Order


class CustomerNode(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (relay.Node,)
        fields = ("id", "name", "email", "phone", "created_at")


class ProductNode(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (relay.Node,)
        fields = ("id", "name", "price", "stock")


class OrderNode(DjangoObjectType):
    class Meta:
        model = Order
        interfaces = (relay.Node,)
        fields = ("id", "order_date", "status", "total_amount", "customer", "products")


class CustomerFilterInput(graphene.InputObjectType):
    name_icontains = graphene.String()
    email_icontains = graphene.String()
    created_at_gte = graphene.DateTime()
    created_at_lte = graphene.DateTime()
    phone_pattern = graphene.String()


class ProductFilterInput(graphene.InputObjectType):
    name_icontains = graphene.String()
    price_gte = graphene.Float()
    price_lte = graphene.Float()
    stock_gte = graphene.Int()
    stock_lte = graphene.Int()


class OrderFilterInput(graphene.InputObjectType):
    total_amount_gte = graphene.Float()
    total_amount_lte = graphene.Float()
    order_date_gte = graphene.DateTime()
    order_date_lte = graphene.DateTime()
    customer_name = graphene.String()
    product_name = graphene.String()
    product_id = graphene.ID()


class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone", "created_at")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "order_date", "status", "total_amount", "customer", "products")


class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(root, info, name, email, phone=None):
        errors = []
        if Customer.objects.filter(email__iexact=email).exists():
            errors.append("Email already exists")
        phone_regex = re.compile(r"^(\+\d{7,15}|\d{3}-\d{3}-\d{4})$")
        if phone and not phone_regex.match(phone):
            errors.append("Invalid phone format")
        if errors:
            return CreateCustomer(success=False, errors=errors, message="Failed to create customer")
        customer = Customer.objects.create(name=name, email=email, phone=phone)
        return CreateCustomer(success=True, customer=customer, message="Customer created", errors=None)


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        customers = graphene.List(graphene.NonNull(graphene.JSONString), required=True)

    created = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    message = graphene.String()
    success = graphene.Boolean()

    @staticmethod
    def mutate(root, info, customers):
        created_objs = []
        errors = []
        for idx, data in enumerate(customers):
            try:
                name = data.get("name")
                email = data.get("email")
                phone = data.get("phone")
                if not name or not email:
                    raise ValueError("name and email required")
                if Customer.objects.filter(email__iexact=email).exists():
                    raise ValueError(f"Email already exists: {email}")
                obj = Customer(name=name, email=email, phone=phone)
                obj.save()
                created_objs.append(obj)
            except Exception as e:  # pylint: disable=broad-except
                errors.append(f"Index {idx}: {e}")
        return BulkCreateCustomers(
            created=created_objs,
            errors=errors,
            success=len(errors) == 0,
            message=f"Created {len(created_objs)} customers, {len(errors)} errors",
        )


class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        stock = graphene.Int(required=False, default_value=0)
        price = graphene.Float(required=False, default_value=0)

    product = graphene.Field(ProductType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    message = graphene.String()

    @staticmethod
    def mutate(root, info, name, stock=0, price=0):
        errors = []
        if stock < 0:
            errors.append("Stock cannot be negative")
        try:
            Decimal(str(price))
        except (InvalidOperation, TypeError):
            errors.append("Invalid price")
        if errors:
            return CreateProduct(success=False, errors=errors, message="Validation errors")
        product = Product.objects.create(name=name, stock=stock, price=price)
        return CreateProduct(success=True, product=product, errors=None, message="Product created")


class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.NonNull(graphene.ID), required=True)

    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    message = graphene.String()

    @staticmethod
    def mutate(root, info, customer_id, product_ids):
        errors = []
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return CreateOrder(success=False, errors=["Customer not found"], message="Order failed")
        products = list(Product.objects.filter(pk__in=product_ids))
        if len(products) != len(set(product_ids)):
            errors.append("Some products not found")
        if errors:
            return CreateOrder(success=False, errors=errors, message="Order failed")
        with transaction.atomic():
            order = Order.objects.create(customer=customer, order_date=timezone.now())
            order.products.set(products)
            order.calculate_total()
            order.save(update_fields=["total_amount"])
        return CreateOrder(success=True, order=order, errors=None, message="Order created")


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


class Query(graphene.ObjectType):
    hello = graphene.String(description="Simple hello field")
    customers = graphene.ConnectionField(
        CustomerNode, filter=CustomerFilterInput(), order_by=graphene.List(graphene.String)
    )
    products = graphene.ConnectionField(
        ProductNode, filter=ProductFilterInput(), order_by=graphene.List(graphene.String)
    )
    orders = graphene.ConnectionField(
        OrderNode, filter=OrderFilterInput(), order_by=graphene.List(graphene.String)
    )
    customers_count = graphene.Int(name='customersCount')
    orders_count = graphene.Int(name='ordersCount')
    orders_revenue = graphene.Float(name='ordersRevenue')

    def resolve_hello(root, info):
        return "Hello, GraphQL!"

    def resolve_customers(root, info, filter=None, order_by=None, **kwargs):  # noqa: A002
        qs = Customer.objects.all()
        if filter:
            if filter.get("name_icontains"):
                qs = qs.filter(name__icontains=filter["name_icontains"])
            if filter.get("email_icontains"):
                qs = qs.filter(email__icontains=filter["email_icontains"])
            if filter.get("created_at_gte"):
                qs = qs.filter(created_at__gte=filter["created_at_gte"])
            if filter.get("created_at_lte"):
                qs = qs.filter(created_at__lte=filter["created_at_lte"])
            if pattern := filter.get("phone_pattern"):
                qs = qs.filter(phone__regex=pattern)
        if order_by:
            qs = qs.order_by(*order_by)
        return qs

    def resolve_products(root, info, filter=None, order_by=None, **kwargs):  # noqa: A002
        qs = Product.objects.all()
        if filter:
            if filter.get("name_icontains"):
                qs = qs.filter(name__icontains=filter["name_icontains"])
            if filter.get("price_gte") is not None:
                qs = qs.filter(price__gte=filter["price_gte"])
            if filter.get("price_lte") is not None:
                qs = qs.filter(price__lte=filter["price_lte"])
            if filter.get("stock_gte") is not None:
                qs = qs.filter(stock__gte=filter["stock_gte"])
            if filter.get("stock_lte") is not None:
                qs = qs.filter(stock__lte=filter["stock_lte"])
        if order_by:
            qs = qs.order_by(*order_by)
        return qs

    def resolve_orders(root, info, filter=None, order_by=None, **kwargs):  # noqa: A002
        qs = Order.objects.select_related("customer").prefetch_related("products")
        if filter:
            if filter.get("total_amount_gte") is not None:
                qs = qs.filter(total_amount__gte=filter["total_amount_gte"])
            if filter.get("total_amount_lte") is not None:
                qs = qs.filter(total_amount__lte=filter["total_amount_lte"])
            if filter.get("order_date_gte"):
                qs = qs.filter(order_date__gte=filter["order_date_gte"])
            if filter.get("order_date_lte"):
                qs = qs.filter(order_date__lte=filter["order_date_lte"])
            if filter.get("customer_name"):
                qs = qs.filter(customer__name__icontains=filter["customer_name"])
            if filter.get("product_name"):
                qs = qs.filter(products__name__icontains=filter["product_name"]).distinct()
            if filter.get("product_id"):
                qs = qs.filter(products__id=filter["product_id"]).distinct()
        if order_by:
            qs = qs.order_by(*order_by)
        return qs

    def resolve_customers_count(root, info):
        return Customer.objects.count()

    def resolve_orders_count(root, info):
        return Order.objects.count()

    def resolve_orders_revenue(root, info):
        from django.db.models import Sum
        agg = Order.objects.aggregate(total=Sum('total_amount'))
        return float(agg.get('total') or 0)


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    update_low_stock_products = UpdateLowStockProducts.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
