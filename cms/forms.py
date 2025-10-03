from django import forms
from django.forms.widgets import ClearableFileInput
from .models import Banner

class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ['title','subtitle','image','link_url','link_label','position','order','is_active']
        widgets = {'image': ClearableFileInput(attrs={'class': 'form-control'})}

