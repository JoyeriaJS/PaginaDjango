from .models import Review
from django.contrib import admin
from .models import HomeSection

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["product", "name", "rating", "approved", "created_at"]
    list_filter = ["approved", "rating", "product"]
    list_editable = ["approved"]
    search_fields = ["name", "comment", "product__name"]


@admin.register(HomeSection)
class HomeSectionAdmin(admin.ModelAdmin):
    list_display = ("order", "key", "title", "is_active")
    list_editable = ("order", "is_active")
