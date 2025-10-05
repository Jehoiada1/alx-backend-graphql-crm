import django_filters as df
import django_filters
from .models import Customer, Product, Order


class CustomerFilter(django_filters.FilterSet):
    name = df.CharFilter(field_name='name', lookup_expr='icontains')
    email = df.CharFilter(field_name='email', lookup_expr='icontains')
    created_at__gte = df.IsoDateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at__lte = df.IsoDateTimeFilter(field_name='created_at', lookup_expr='lte')
    phone_pattern = df.CharFilter(method='filter_phone_pattern')

    def filter_phone_pattern(self, queryset, name, value):
        if not value:
            return queryset
        # basic startswith pattern match; can be enhanced to regex if needed
        return queryset.filter(phone__startswith=value)

    class Meta:
        model = Customer
        fields = []


class ProductFilter(df.FilterSet):
    name = df.CharFilter(field_name='name', lookup_expr='icontains')
    price__gte = df.NumberFilter(field_name='price', lookup_expr='gte')
    price__lte = df.NumberFilter(field_name='price', lookup_expr='lte')
    stock__gte = df.NumberFilter(field_name='stock', lookup_expr='gte')
    stock__lte = df.NumberFilter(field_name='stock', lookup_expr='lte')

    class Meta:
        model = Product
        fields = []


class OrderFilter(df.FilterSet):
    total_amount__gte = df.NumberFilter(field_name='total_amount', lookup_expr='gte')
    total_amount__lte = df.NumberFilter(field_name='total_amount', lookup_expr='lte')
    order_date__gte = df.IsoDateTimeFilter(field_name='order_date', lookup_expr='gte')
    order_date__lte = df.IsoDateTimeFilter(field_name='order_date', lookup_expr='lte')
    customer_name = df.CharFilter(field_name='customer__name', lookup_expr='icontains')
    product_name = df.CharFilter(field_name='products__name', lookup_expr='icontains')
    product_id = df.CharFilter(method='filter_product_id')

    def filter_product_id(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(products__id=value)

    @property
    def qs(self):
        # ensure distinct for m2m lookups
        return super().qs.distinct()

    class Meta:
        model = Order
        fields = []
