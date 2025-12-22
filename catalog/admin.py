from .models import Review
from django.contrib import admin

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["product", "name", "rating", "approved", "created_at"]
    list_filter = ["approved", "rating", "product"]
    list_editable = ["approved"]
    search_fields = ["name", "comment", "product__name"]


