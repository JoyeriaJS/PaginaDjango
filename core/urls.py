from django.urls import path
from .views import home
from . import views
from . import views_auth
from django.urls import path, include


app_name = "core"
urlpatterns = [
    path("", home, name="home"),
     path('producto/<int:pk>/', views.product_detail, name='product_detail'),
     path("categoria/<int:pk>/", views.category_list, name="category_list"),  # ← usa pk
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

    #Mercado Pago
    path("checkout/mercadopago/", views.mp_checkout, name="mp_checkout"),
    path("pago/exito/", views.mp_success, name="mp_success"),
    path("pago/fallo/", views.mp_failure, name="mp_failure"),
    path("pago/pendiente/", views.mp_pending, name="mp_pending"),
    # opcional webhook (lo podemos activar después):
    path("mp/webhook/", views.mp_webhook, name="mp_webhook"),
    path("orden/<str:payment_id>/pdf/", views.order_pdf, name="order_pdf"),


   #CHECKOUT
   path("checkout/", views.checkout, name="checkout"),

   #LOGIN
    path("login/", views_auth.login_view, name="login"),
    path("register/", views_auth.register_view, name="register"),
    path("logout/", views_auth.logout_view, name="logout"),
   
    #path("cuenta/", include("accounts.urls")),
    
    #CATEGORIES
    path("categorias/", views.category_all, name="category_all"),
    path("categoria/<int:pk>/", views.category_list, name="category_list"),

    
]
