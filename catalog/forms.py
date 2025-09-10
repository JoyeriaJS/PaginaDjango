from django import forms
from .models import Product, Category, Material, ProductImage

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name','category','material','sku','description','price','stock','is_active']
        widgets = {'description': forms.Textarea(attrs={'rows':4})}

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image','alt','is_primary']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['name']
