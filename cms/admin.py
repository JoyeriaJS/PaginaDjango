# cms/admin.py
from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "rating", "is_approved", "created")
    list_filter  = ("is_approved", "rating", "created")
    search_fields = ("name", "city", "comment")
    actions = ["aprobar_reseñas", "desaprobar_reseñas"]

    @admin.action(description="Aprobar reseñas seleccionadas")
    def aprobar_reseñas(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="Desaprobar reseñas seleccionadas")
    def desaprobar_reseñas(self, request, queryset):
        queryset.update(is_approved=False)
