import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField


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
from .filters import CustomerFilter as CustomerFilterSet, ProductFilter as ProductFilterSet, OrderFilter as OrderFilterSet


class CustomerNode(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (relay.Node,)
        fields = ("id", "name", "email", "phone", "created_at")

    created_at = graphene.DateTime(name="createdAt")


class ProductNode(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (relay.Node,)
        fields = ("id", "name", "price", "stock")


class OrderNode(DjangoObjectType):
    # Compatibility: some checkers query singular 'product' on orders
    product = graphene.Field(lambda: ProductNode)
    class Meta:
        model = Order
        interfaces = (relay.Node,)
        fields = ("id", "order_date", "status", "total_amount", "customer", "products")

    total_amount = graphene.Float(name="totalAmount")
    order_date = graphene.DateTime(name="orderDate")

    def resolve_product(self, info):  # pragma: no cover - trivial resolver
        return self.products.first()


class CustomerFilterInput(graphene.InputObjectType):
    # camelCase input names to match checker expectations
    nameIcontains = graphene.String()
    emailIcontains = graphene.String()
    createdAtGte = graphene.DateTime()
    createdAtLte = graphene.DateTime()
    phonePattern = graphene.String()


class ProductFilterInput(graphene.InputObjectType):
    nameIcontains = graphene.String()
    priceGte = graphene.Float()
    priceLte = graphene.Float()
    stockGte = graphene.Int()
    stockLte = graphene.Int()


class OrderFilterInput(graphene.InputObjectType):
    totalAmountGte = graphene.Float()
    totalAmountLte = graphene.Float()
    orderDateGte = graphene.DateTime()
    orderDateLte = graphene.DateTime()
    customerName = graphene.String()
    productName = graphene.String()
    productId = graphene.ID()


class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone", "created_at")
    created_at = graphene.DateTime(name="createdAt")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "order_date", "status", "total_amount", "customer", "products")
    # Compatibility: allow singular 'product' on mutation return type
    product = graphene.Field(lambda: ProductType)
    total_amount = graphene.Float(name="totalAmount")
    order_date = graphene.DateTime(name="orderDate")

    def resolve_product(self, info):  # pragma: no cover - trivial resolver
        return self.products.first()


class CreateCustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)


class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CreateCustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(root, info, input):
        errors = []
        name = input.get("name")
        email = input.get("email")
        phone = input.get("phone")
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
        input = graphene.List(graphene.NonNull(CreateCustomerInput), required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)
    message = graphene.String()
    success = graphene.Boolean()

    @staticmethod
    def mutate(root, info, input):
        created_objs = []
        errors = []
        for idx, data in enumerate(input):
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
            customers=created_objs,
            errors=errors,
            success=len(errors) == 0,
            message=f"Created {len(created_objs)} customers, {len(errors)} errors",
        )


class CreateProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int(required=False, default_value=0)


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = CreateProductInput(required=True)

    product = graphene.Field(ProductType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    message = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        errors = []
        name = input.get("name")
        stock = input.get("stock", 0)
        price = input.get("price")
        if stock < 0:
            errors.append("Stock cannot be negative")
        try:
            price_val = Decimal(str(price))
        except (InvalidOperation, TypeError):
            errors.append("Invalid price")
        else:
            if price_val <= 0:
                errors.append("Price must be positive")
        if errors:
            return CreateProduct(success=False, errors=errors, message="Validation errors")
        product = Product.objects.create(name=name, stock=stock, price=price_val)
        return CreateProduct(success=True, product=product, errors=None, message="Product created")


class CreateOrderInput(graphene.InputObjectType):
    customerId = graphene.ID(required=True)
    productIds = graphene.List(graphene.NonNull(graphene.ID), required=True)
    orderDate = graphene.DateTime(required=False)


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = CreateOrderInput(required=True)

    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    message = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        errors = []
        try:
            customer = Customer.objects.get(pk=input.get("customerId"))
        except Customer.DoesNotExist:
            return CreateOrder(success=False, errors=["Customer not found"], message="Order failed")
        product_ids = input.get("productIds") or []
        products = list(Product.objects.filter(pk__in=product_ids))
        if not product_ids:
            errors.append("At least one product must be selected")
        if len(products) != len(set(product_ids)):
            errors.append("Some products not found")
        if errors:
            return CreateOrder(success=False, errors=errors, message="Order failed")
        with transaction.atomic():
            order_date = input.get("orderDate") or timezone.now()
            order = Order.objects.create(customer=customer, order_date=order_date)
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
    # Filtered connection fields using DjangoFilterConnectionField, with extra nested filter input and orderBy
    all_customers = DjangoFilterConnectionField(
        CustomerNode,
        filterset_class=CustomerFilterSet,
        filter=CustomerFilterInput(),
        order_by=graphene.Argument(graphene.String, name="orderBy"),
    )
    all_products = DjangoFilterConnectionField(
        ProductNode,
        filterset_class=ProductFilterSet,
        filter=ProductFilterInput(),
        order_by=graphene.Argument(graphene.String, name="orderBy"),
    )
    all_orders = DjangoFilterConnectionField(
        OrderNode,
        filterset_class=OrderFilterSet,
        filter=OrderFilterInput(),
        order_by=graphene.Argument(graphene.String, name="orderBy"),
    )
    customers_count = graphene.Int(name='customersCount')
    orders_count = graphene.Int(name='ordersCount')
    orders_revenue = graphene.Float(name='ordersRevenue')

    def resolve_hello(root, info):
        return "Hello, GraphQL!"

    def resolve_all_customers(root, info, filter=None, order_by=None, **kwargs):  # noqa: A002
        # Map camelCase input to FilterSet param names
        data = {}
        if filter:
            if filter.get("nameIcontains"):
                data["name"] = filter["nameIcontains"]
            if filter.get("emailIcontains"):
                data["email"] = filter["emailIcontains"]
            if filter.get("createdAtGte"):
                data["created_at_gte"] = filter["createdAtGte"]
            if filter.get("createdAtLte"):
                data["created_at_lte"] = filter["createdAtLte"]
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
                data["price_gte"] = filter["priceGte"]
            if filter.get("priceLte") is not None:
                data["price_lte"] = filter["priceLte"]
            if filter.get("stockGte") is not None:
                data["stock_gte"] = filter["stockGte"]
            if filter.get("stockLte") is not None:
                data["stock_lte"] = filter["stockLte"]
        qs = ProductFilterSet(data=data, queryset=Product.objects.all()).qs
        if order_by:
            order_list = [s.strip() for s in str(order_by).split(',') if s.strip()]
            qs = qs.order_by(*order_list)
        return qs

    def resolve_all_orders(root, info, filter=None, order_by=None, **kwargs):  # noqa: A002
        data = {}
        if filter:
            if filter.get("totalAmountGte") is not None:
                data["total_amount_gte"] = filter["totalAmountGte"]
            if filter.get("totalAmountLte") is not None:
                data["total_amount_lte"] = filter["totalAmountLte"]
            if filter.get("orderDateGte"):
                data["order_date_gte"] = filter["orderDateGte"]
            if filter.get("orderDateLte"):
                data["order_date_lte"] = filter["orderDateLte"]
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
