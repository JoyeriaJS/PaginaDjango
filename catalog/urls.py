from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.panel_home, name='panel_home'),  # /panel/
    path('productos/', views.product_list, name='product_list'),
    path('productos/crear/', views.product_create, name='product_create'),
    path('productos/<int:pk>/editar/', views.product_edit, name='product_edit'),
    path('productos/<int:pk>/eliminar/', views.product_delete, name='product_delete'),
    path('productos/<int:pk>/imagenes/', views.product_images, name='product_images'),
    path('imagenes/<int:image_id>/principal/', views.image_set_primary, name='image_set_primary'),
    path('imagenes/<int:image_id>/eliminar/', views.image_delete, name='image_delete'),
    path('categorias/', views.category_list, name='category_list'),
    path('categorias/crear/', views.category_create, name='category_create'),
    path('categorias/<int:pk>/editar/', views.category_edit, name='category_edit'),
    path('categorias/<int:pk>/eliminar/', views.category_delete, name='category_delete'),
    path('materiales/', views.material_list, name='material_list'),
    path('materiales/crear/', views.material_create, name='material_create'),
    path('materiales/<int:pk>/editar/', views.material_edit, name='material_edit'),
    path('materiales/<int:pk>/eliminar/', views.material_delete, name='material_delete'),
    path('menu/', views.menu_list, name='menu_list'),
    path('menu/nuevo/', views.menu_create, name='menu_create'),
    path('menu/<int:pk>/editar/', views.menu_edit, name='menu_edit'),
    path('menu/<int:pk>/eliminar/', views.menu_delete, name='menu_delete'),
    path('menu/ping/', views.menu_ping, name='menu_ping'),
    path('descuentos/', views.discount_list, name='discount_list'),
    path('descuentos/nuevo/', views.discount_create, name='discount_create'),
    path('descuentos/<int:pk>/editar/', views.discount_edit, name='discount_edit'),
    path('descuentos/<int:pk>/eliminar/', views.discount_delete, name='discount_delete'),

]
