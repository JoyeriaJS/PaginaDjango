# cms/admin.py
from django.contrib import admin
from .models import SiteSettings

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
