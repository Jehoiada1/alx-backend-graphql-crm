from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "products_list", "order_date", "status", "total_amount")
    search_fields = ("customer__email", "customer__name")
    list_filter = ("status",)
    autocomplete_fields = ("customer", "products")

    def products_list(self, obj):  # pragma: no cover - admin display helper
        return ", ".join(p.name for p in obj.products.all()[:5]) + ("..." if obj.products.count() > 5 else "")
    products_list.short_description = "Products"
