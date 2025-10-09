# core/forms.py
from django import forms
import re

def validar_rut_chileno(rut):
    """
    Valida RUT chileno (formato flexible). Acepta con o sin puntos y guion.
    Cálculo según módulo 11.
    """
    if not rut:
        raise forms.ValidationError("RUT requerido.")
    # Normaliza: quita puntos y espacios, deja guion si viene
    rut = rut.replace(".", "").replace(" ", "").lower()

    # Permitir ambas variantes: con o sin guion
    if "-" in rut:
        num, dv = rut.split("-", 1)
    else:
        num, dv = rut[:-1], rut[-1]

    if not num.isdigit() or not re.match(r"^[\dk]$", dv):
        raise forms.ValidationError("RUT inválido.")

    # cálculo
    reversed_digits = map(int, reversed(num))
    factors = [2, 3, 4, 5, 6, 7]
    s = 0
    f_i = 0
    for d in reversed_digits:
        s += d * factors[f_i]
        f_i = (f_i + 1) % len(factors)
    mod = 11 - (s % 11)
    dv_calc = "0" if mod == 11 else "k" if mod == 10 else str(mod)

    if dv != dv_calc:
        raise forms.ValidationError("RUT inválido.")

    return f"{int(num):,}-{dv}".replace(",", ".")

class CheckoutForm(forms.Form):
    # Datos de contacto
    first_name = forms.CharField(label="Nombre", max_length=60)
    last_name  = forms.CharField(label="Apellido", max_length=60)
    rut        = forms.CharField(label="RUT", max_length=20)
    email      = forms.EmailField(label="Email", max_length=120)
    phone      = forms.CharField(label="Teléfono", max_length=30)

    # Dirección (Chile)
    address_line = forms.CharField(label="Dirección", max_length=200)
    comuna       = forms.CharField(label="Comuna", max_length=80)
    ciudad       = forms.CharField(label="Ciudad", max_length=80)
    region       = forms.CharField(label="Región", max_length=80)
    postal_code  = forms.CharField(label="Código Postal", max_length=15, required=False)

    notes = forms.CharField(
        label="Notas del pedido (opcional)",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False
    )

    # (Opcional) Método de envío
    SHIPPING_CHOICES = (
        ("retiro", "Retiro en tienda"),
        ("envio", "Envío a domicilio"),
    )
    shipping_method = forms.ChoiceField(
        label="Envío",
        choices=SHIPPING_CHOICES,
        initial="envio"
    )

    def clean_rut(self):
        return validar_rut_chileno(self.cleaned_data["rut"])

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        # Limpiar espacios. Puedes hacer validación adicional si quieres.
        phone = re.sub(r"\s+", "", phone)
        return phone
