from django.db import models
from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r"^(\+\d{7,15}|\d{3}-\d{3}-\d{4})$",
    message="Phone must be international format +<digits> or XXX-XXX-XXXX",
)


class Customer(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=32, blank=True, null=True, validators=[phone_validator])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):  # pragma: no cover - trivial
        return self.email
