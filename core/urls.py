from django.urls import path
from .views import home
from . import views

app_name = "core"
urlpatterns = [
    path("", home, name="home"),
     path('producto/<int:pk>/', views.product_detail, name='product_detail'),
     path("categoria/<int:pk>/", views.category_list, name="category_list")
     path("buscar/", views.search, name="search"),


    # Carrito
    path('carrito/', views.cart_detail, name='cart_detail'),
    path('carrito/agregar/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('carrito/quitar/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('carrito/actualizar/', views.update_cart, name='update_cart'),
    path('carrito/vaciar/', views.clear_cart, name='clear_cart'),
    path('categoria/<int:pk>/', views.category_products, name='category_products'),
    path('carrito/cupon/aplicar/', views.apply_coupon, name='apply_coupon'),
    path('carrito/cupon/quitar/', views.remove_coupon, name='remove_coupon'),
]
