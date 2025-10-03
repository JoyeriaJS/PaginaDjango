from django import forms
from django.forms.widgets import ClearableFileInput
from .models import Banner

class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ['title','subtitle','image','link_url','link_label','position','order','is_active']
        widgets = {'image': ClearableFileInput(attrs={'class': 'form-control'})}

class ReviewForm(forms.Form):
    name = forms.CharField(label="Tu nombre", max_length=120)
    email = forms.EmailField(label="Email", required=False)
    rating = forms.IntegerField(label="Puntuación", min_value=1, max_value=5, initial=5)
    comment = forms.CharField(label="Comentario", widget=forms.Textarea, max_length=1500)
    # Honeypot anti-bots (debe quedar oculto en el template)
    website = forms.CharField(required=False, widget=forms.HiddenInput)