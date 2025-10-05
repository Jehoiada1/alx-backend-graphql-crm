import re
from decimal import Decimal, InvalidOperation
from typing import List

import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.db import transaction
from django.utils import timezone

from .models import Customer, Product, Order
from .filters import CustomerFilter as CustomerFilterSet, ProductFilter as ProductFilterSet, OrderFilter as OrderFilterSet


# GraphQL Types (Relay Nodes)
class CustomerNode(DjangoObjectType):
    createdAt = graphene.DateTime(source='created_at')

    class Meta:
        model = Customer
        interfaces = (relay.Node,)
        fields = ('id', 'name', 'email', 'phone', 'created_at')


class ProductNode(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (relay.Node,)
        fields = ('id', 'name', 'price', 'stock', 'created_at')


class OrderNode(DjangoObjectType):
    totalAmount = graphene.Decimal(source='total_amount')
    orderDate = graphene.DateTime(source='order_date')
    # expose a single product for sample query parity
    product = graphene.Field(lambda: ProductNode)

    class Meta:
        model = Order
        interfaces = (relay.Node,)
        fields = ('id', 'customer', 'products', 'total_amount', 'order_date', 'created_at')

    def resolve_product(self, info):
        return self.products.first()


# Inputs
class CreateCustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


class CreateProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int()


class CreateOrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.NonNull(graphene.ID), required=True)
    order_date = graphene.DateTime()


# Validation helpers
PHONE_RE = re.compile(r"^(\+?\d{10,15}|\d{3}-\d{3}-\d{4})$")


def validate_phone(phone: str) -> bool:
    if not phone:
        return True
    return bool(PHONE_RE.match(phone))


def parse_positive_decimal(value) -> Decimal:
    try:
        d = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Invalid decimal value")
    if d <= 0:
        raise ValueError("Price must be positive")
    return d


def parse_non_negative_int(value) -> int:
    try:
        i = int(value)
    except (TypeError, ValueError):
        raise ValueError("Stock must be an integer")
    if i < 0:
        raise ValueError("Stock cannot be negative")
    return i


# Mutations
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CreateCustomerInput(required=True)

    customer = graphene.Field(lambda: CustomerNode)
    message = graphene.String()

    @staticmethod
    def mutate(root, info, input: CreateCustomerInput):
        name = (input.get("name") or "").strip()
        email = (input.get("email") or "").strip().lower()
        phone = (input.get("phone") or "").strip() or None

        if not name:
            raise graphene.GraphQLError("Name is required")
        if not email:
            raise graphene.GraphQLError("Email is required")
        if Customer.objects.filter(email=email).exists():
            raise graphene.GraphQLError("Email already exists")
        if phone and not validate_phone(phone):
            raise graphene.GraphQLError("Invalid phone format")

        customer = Customer.objects.create(name=name, email=email, phone=phone)
        return CreateCustomer(customer=customer, message="Customer created successfully")


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(graphene.NonNull(CreateCustomerInput), required=True)

    customers = graphene.List(lambda: CustomerNode)
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(root, info, input: List[CreateCustomerInput]):
        created = []
        errors = []
        # Use a transaction for the batch, still allow partial success by not raising
        with transaction.atomic():
            for idx, item in enumerate(input):
                try:
                    name = (item.get("name") or "").strip()
                    email = (item.get("email") or "").strip().lower()
                    phone = (item.get("phone") or "").strip() or None

                    if not name:
                        raise ValueError("Name is required")
                    if not email:
                        raise ValueError("Email is required")
                    if Customer.objects.filter(email=email).exists():
                        raise ValueError("Email already exists")
                    if phone and not validate_phone(phone):
                        raise ValueError("Invalid phone format")
                    cust = Customer.objects.create(name=name, email=email, phone=phone)
                    created.append(cust)
                except Exception as e:
                    errors.append(f"Record {idx}: {e}")
        return BulkCreateCustomers(customers=created, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = CreateProductInput(required=True)

    product = graphene.Field(lambda: ProductNode)

    @staticmethod
    def mutate(root, info, input: CreateProductInput):
        name = (input.get("name") or "").strip()
        if not name:
            raise graphene.GraphQLError("Name is required")
        price = parse_positive_decimal(input.get("price"))
        stock = parse_non_negative_int(input.get("stock") or 0)
        product = Product.objects.create(name=name, price=price, stock=stock)
        return CreateProduct(product=product)


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = CreateOrderInput(required=True)

    order = graphene.Field(lambda: OrderNode)

    @staticmethod
    def mutate(root, info, input: CreateOrderInput):
        # Validate customer
        try:
            customer = Customer.objects.get(pk=input.get("customer_id"))
        except Customer.DoesNotExist:
            raise graphene.GraphQLError("Invalid customer ID")

        product_ids = input.get("product_ids") or []
        if not product_ids:
            raise graphene.GraphQLError("At least one product must be selected")

        products = list(Product.objects.filter(pk__in=product_ids))
        missing = set(map(str, product_ids)) - set(map(lambda p: str(p.pk), products))
        if missing:
            raise graphene.GraphQLError(f"Invalid product ID(s): {', '.join(sorted(missing))}")

        order_date = input.get("order_date") or timezone.now()
        with transaction.atomic():
            order = Order.objects.create(customer=customer, order_date=order_date)
            order.products.set(products)
            total = sum((p.price for p in products), start=Decimal("0"))
            order.total_amount = total
            order.save()
        return CreateOrder(order=order)


# Filter inputs for GraphQL
class CustomerFilterInput(graphene.InputObjectType):
    nameIcontains = graphene.String()
    emailIcontains = graphene.String()
    createdAtGte = graphene.DateTime()
    createdAtLte = graphene.DateTime()
    phonePattern = graphene.String()


class ProductFilterInput(graphene.InputObjectType):
    nameIcontains = graphene.String()
    priceGte = graphene.Decimal()
    priceLte = graphene.Decimal()
    stockGte = graphene.Int()
    stockLte = graphene.Int()


class OrderFilterInput(graphene.InputObjectType):
    totalAmountGte = graphene.Decimal()
    totalAmountLte = graphene.Decimal()
    orderDateGte = graphene.DateTime()
    orderDateLte = graphene.DateTime()
    customerName = graphene.String()
    productName = graphene.String()
    productId = graphene.ID()


class CRMQuery:
    # Filtered Relay connections with custom filter and orderBy args
    all_customers = DjangoFilterConnectionField(
        CustomerNode,
        filterset_class=CustomerFilterSet,
        filter=graphene.Argument(CustomerFilterInput, name="filter"),
        order_by=graphene.Argument(graphene.String, name="orderBy"),
    )
    all_products = DjangoFilterConnectionField(
        ProductNode,
        filterset_class=ProductFilterSet,
        filter=graphene.Argument(ProductFilterInput, name="filter"),
        order_by=graphene.Argument(graphene.String, name="orderBy"),
    )
    all_orders = DjangoFilterConnectionField(
        OrderNode,
        filterset_class=OrderFilterSet,
        filter=graphene.Argument(OrderFilterInput, name="filter"),
        order_by=graphene.Argument(graphene.String, name="orderBy"),
    )

    # Resolvers mapping camelCase inputs to FilterSet params and applying ordering
    def resolve_all_customers(root, info, filter=None, order_by=None, **kwargs):  # noqa: A002
        data = {}
        if filter:
            if filter.get("nameIcontains"):
                data["name"] = filter["nameIcontains"]
            if filter.get("emailIcontains"):
                data["email"] = filter["emailIcontains"]
            if filter.get("createdAtGte"):
                data["created_at__gte"] = filter["createdAtGte"]
            if filter.get("createdAtLte"):
                data["created_at__lte"] = filter["createdAtLte"]
            if filter.get("phonePattern"):
                data["phone_pattern"] = filter["phonePattern"]
        qs = CustomerFilterSet(data=data, queryset=Customer.objects.all()).qs
        if order_by:
            order_list = [s.strip() for s in str(order_by).split(',') if s.strip()]
            qs = qs.order_by(*order_list)
        return qs

    def resolve_all_products(root, info, filter=None, order_by=None, **kwargs):  # noqa: A002
        data = {}
        if filter:
            if filter.get("nameIcontains"):
                data["name"] = filter["nameIcontains"]
            if filter.get("priceGte") is not None:
                data["price__gte"] = filter["priceGte"]
            if filter.get("priceLte") is not None:
                data["price__lte"] = filter["priceLte"]
            if filter.get("stockGte") is not None:
                data["stock__gte"] = filter["stockGte"]
            if filter.get("stockLte") is not None:
                data["stock__lte"] = filter["stockLte"]
        qs = ProductFilterSet(data=data, queryset=Product.objects.all()).qs
        if order_by:
            order_list = [s.strip() for s in str(order_by).split(',') if s.strip()]
            qs = qs.order_by(*order_list)
        return qs

    def resolve_all_orders(root, info, filter=None, order_by=None, **kwargs):  # noqa: A002
        data = {}
        if filter:
            if filter.get("totalAmountGte") is not None:
                data["total_amount__gte"] = filter["totalAmountGte"]
            if filter.get("totalAmountLte") is not None:
                data["total_amount__lte"] = filter["totalAmountLte"]
            if filter.get("orderDateGte"):
                data["order_date__gte"] = filter["orderDateGte"]
            if filter.get("orderDateLte"):
                data["order_date__lte"] = filter["orderDateLte"]
            if filter.get("customerName"):
                data["customer_name"] = filter["customerName"]
            if filter.get("productName"):
                data["product_name"] = filter["productName"]
            if filter.get("productId"):
                data["product_id"] = filter["productId"]
        qs = OrderFilterSet(data=data, queryset=Order.objects.select_related("customer").prefetch_related("products")).qs
        if order_by:
            order_list = [s.strip() for s in str(order_by).split(',') if s.strip()]
            qs = qs.order_by(*order_list)
        return qs


class Query(CRMQuery, graphene.ObjectType):
    # keep a simple hello for quick checks
    hello = graphene.String()

    def resolve_hello(root, info):
        return "Hello, GraphQL!"


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
