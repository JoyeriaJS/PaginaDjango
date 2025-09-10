from django import forms
from django.forms.widgets import ClearableFileInput
from .models import Product, ProductImage, Category, Material

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name","slug","sku","category","material","description","price","stock","is_active"]

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ["image","alt","is_primary"]
        widgets = {
            "image": ClearableFileInput(attrs={"class":"form-control"}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name","slug"]

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ["name"]
