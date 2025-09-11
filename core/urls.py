from django.urls import path
from .views import home
from . import views

app_name = "core"
urlpatterns = [
    path("", home, name="home"),
     path('producto/<int:pk>/', views.product_detail, name='product_detail'),

    # Carrito
    path('carrito/', views.cart_detail, name='cart_detail'),
    path('carrito/agregar/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('carrito/quitar/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('carrito/actualizar/', views.update_cart, name='update_cart'),
]
