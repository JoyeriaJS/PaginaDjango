# cms/admin.py
from django.contrib import admin
from .models import SiteSettings
from .models import Review

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("brand_name", "updated_at")
    fieldsets = (
        (None, {"fields": ("brand_name", "logo", "logo_width")}),
    )

    # opcional: permitir solo un registro
    def has_add_permission(self, request):
        if SiteSettings.objects.exists():
            return False
        return super().has_add_permission(request)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("name", "rating", "is_approved", "created_at")
    list_filter = ("is_approved", "rating", "created_at")
    search_fields = ("name", "comment", "email")
    ordering = ("-created_at",)