from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("name", "price", "qty", "line_total", "product")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "total_amount", "mp_status", "is_paid", "created_at")
    list_filter = ("mp_status", "is_paid", "created_at")
    search_fields = ("id", "email", "mp_payment_id", "mp_preference_id")
    inlines = [OrderItemInline]
