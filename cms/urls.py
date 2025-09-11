from django.urls import path
from . import views

app_name = 'cms'
urlpatterns = [
    path('banners/', views.banner_list, name='banner_list'),
    path('banners/nuevo/', views.banner_create, name='banner_create'),
    path('banners/<int:pk>/', views.banner_edit, name='banner_edit'),
    path('banners/<int:pk>/eliminar/', views.banner_delete, name='banner_delete'),
]
