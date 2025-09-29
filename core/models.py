from django.db import models
from django.utils import timezone
from catalog.models import Product

class Order(models.Model):
    # Datos mínimos de la orden
    email = models.EmailField(blank=True, null=True)
    total_amount = models.PositiveIntegerField(default=0)

    # Mercado Pago
    mp_preference_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    mp_payment_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    mp_status = models.CharField(max_length=50, blank=True, null=True)  # approved, rejected, pending, etc.

    # Auditoría
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # Estado interno
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Order #{self.pk} - ${self.total_amount} ({self.mp_status or 'new'})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=200)
    price = models.PositiveIntegerField(default=0)
    qty = models.PositiveIntegerField(default=1)
    line_total = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.name} x{self.qty}"
