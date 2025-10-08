# cms/admin.py
from django.contrib import admin
from cms.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("name", "rating", "is_approved", "created_at")
    list_filter = ("is_approved", "rating", "created_at")
    search_fields = ("name", "comment")
    list_editable = ("is_approved",)
    ordering = ("-created_at",)