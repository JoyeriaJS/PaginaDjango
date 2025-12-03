from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # Dashboard principal al entrar a /cuenta/
    path("", views.dashboard, name="dashboard"),

    # (Opcional: seguir manteniendo /cuenta/panel/)
    path("panel/", views.dashboard, name="dashboard_alt"),

    # Perfil
    path("perfil/", views.profile, name="profile"),
    path("perfil/editar/", views.profile_edit, name="profile_edit"),

    # Direcciones
    path("direcciones/", views.address_list, name="address_list"),
    path("direcciones/nueva/", views.address_create, name="address_create"),
    path("direcciones/<int:pk>/editar/", views.address_edit, name="address_edit"),
    path("direcciones/<int:pk>/eliminar/", views.address_delete, name="address_delete"),
    path("direcciones/<int:pk>/default/", views.address_set_default, name="address_default"),

    # Historial de compras
    path("compras/", views.orders_list, name="orders_list"),
    path("compras/<int:pk>/", views.order_detail, name="order_detail"),
]
