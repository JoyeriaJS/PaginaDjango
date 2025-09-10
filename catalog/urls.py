from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("productos/", views.product_list, name="product_list"),
    path("productos/nuevo/", views.product_create, name="product_create"),
    path("productos/<int:pk>/", views.product_edit, name="product_edit"),
    path("productos/<int:pk>/eliminar/", views.product_delete, name="product_delete"),
    path("productos/<int:pk>/imagenes/", views.product_images, name="product_images"),
    path("imagenes/<int:image_id>/principal/", views.image_set_primary, name="image_set_primary"),
    path("imagenes/<int:image_id>/eliminar/", views.image_delete, name="image_delete"),

    path("categorias/", views.category_list, name="category_list"),
    path("categorias/nueva/", views.category_create, name="category_create"),
    path("categorias/<int:pk>/", views.category_edit, name="category_edit"),
    path("categorias/<int:pk>/eliminar/", views.category_delete, name="category_delete"),

    path("materiales/", views.material_list, name="material_list"),
    path("materiales/nuevo/", views.material_create, name="material_create"),
    path("materiales/<int:pk>/", views.material_edit, name="material_edit"),
    path("materiales/<int:pk>/eliminar/", views.material_delete, name="material_delete"),
]
