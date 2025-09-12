from django import forms
from .models import Product, Category, Material, ProductImage, Discount
from django.forms.widgets import ClearableFileInput
from cms.models import MenuItem

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name','category','material','sku','description','price','stock','is_active']
        widgets = {'description': forms.Textarea(attrs={'rows':4})}

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image','alt','is_primary']
        widgets = {
            'image': ClearableFileInput(attrs={'class': 'form-control'})
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del material'}),
        }

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['title','url','order','is_active','parent','open_in_new_tab','staff_only']
        widgets = {
            'title': forms.TextInput(attrs={'class':'form-control'}),
            'url': forms.TextInput(attrs={'class':'form-control', 'placeholder':'/ruta o https://...'}),
            'order': forms.NumberInput(attrs={'class':'form-control','min':0}),
            'parent': forms.Select(attrs={'class':'form-select'}),
        }

class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = ['name','code','dtype','value','scope','product','category','min_subtotal','start_at','end_at','usage_limit','is_active','stackable']
        widgets = {
            'dtype': forms.Select(attrs={'class':'form-select'}),
            'scope': forms.Select(attrs={'class':'form-select'}),
            'product': forms.Select(attrs={'class':'form-select'}),
            'category': forms.Select(attrs={'class':'form-select'}),
            'start_at': forms.DateTimeInput(attrs={'type':'datetime-local','class':'form-control'}),
            'end_at': forms.DateTimeInput(attrs={'type':'datetime-local','class':'form-control'}),
        }