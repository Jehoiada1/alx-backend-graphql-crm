from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=200)
    stock = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["name"]

    def __str__(self):  # pragma: no cover - trivial
        return self.name
