from django.shortcuts import render
from django.db.models import Count
from catalog.models import Product, Category
from cms.models import Banner

def home(request):
    categories = Category.objects.annotate(n=Count('products')).order_by('-n','name')[:8]
    latest_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    return render(request, "core/home.html", {
        "categories": categories,
        "latest_products": latest_products,
        "banners_hero": Banner.objects.filter(is_active=True, position=Banner.HOME_HERO).order_by('order','-updated_at')[:6],
        "banners_strip": Banner.objects.filter(is_active=True, position=Banner.HOME_STRIP).order_by('order','-updated_at')[:6],
    })
