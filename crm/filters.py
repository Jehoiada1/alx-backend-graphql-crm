import django_filters as filters
from crm.customers.models import Customer
from crm.products.models import Product
from crm.orders.models import Order


class CustomerFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    email = filters.CharFilter(field_name="email", lookup_expr="icontains")
    created_at_gte = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_at_lte = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    phone_pattern = filters.CharFilter(method="filter_phone_pattern")
    order_by = filters.OrderingFilter(
        fields=(
            ("name", "name"),
            ("email", "email"),
            ("created_at", "created_at"),
        )
    )

    def filter_phone_pattern(self, queryset, name, value):  # noqa: ARG002
        if value:
            return queryset.filter(phone__regex=value)
        return queryset

    class Meta:
        model = Customer
    fields = ["name", "email", "created_at_gte", "created_at_lte", "phone_pattern"]


class ProductFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    price_gte = filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_lte = filters.NumberFilter(field_name="price", lookup_expr="lte")
    stock_gte = filters.NumberFilter(field_name="stock", lookup_expr="gte")
    stock_lte = filters.NumberFilter(field_name="stock", lookup_expr="lte")
    order_by = filters.OrderingFilter(
        fields=(
            ("name", "name"),
            ("price", "price"),
            ("stock", "stock"),
        )
    )

    class Meta:
        model = Product
    fields = ["name", "price_gte", "price_lte", "stock_gte", "stock_lte"]


class OrderFilter(filters.FilterSet):
    total_amount_gte = filters.NumberFilter(field_name="total_amount", lookup_expr="gte")
    total_amount_lte = filters.NumberFilter(field_name="total_amount", lookup_expr="lte")
    order_date_gte = filters.DateTimeFilter(field_name="order_date", lookup_expr="gte")
    order_date_lte = filters.DateTimeFilter(field_name="order_date", lookup_expr="lte")
    customer_name = filters.CharFilter(field_name="customer__name", lookup_expr="icontains")
    product_name = filters.CharFilter(field_name="products__name", lookup_expr="icontains")
    product_id = filters.NumberFilter(field_name="products__id")
    order_by = filters.OrderingFilter(
        fields=(
            ("order_date", "order_date"),
            ("total_amount", "total_amount"),
            ("status", "status"),
        )
    )

    class Meta:
        model = Order
        fields = [
            "total_amount_gte",
            "total_amount_lte",
            "order_date_gte",
            "order_date_lte",
            "customer_name",
            "product_name",
            "product_id",
        ]
