# core/forms.py
from django import forms
import re
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

# --------------------------------------
# VALIDACIÓN RUT (SE MANTIENE TU FUNCIÓN)
# --------------------------------------
def validar_rut_chileno(rut):
    if not rut:
        raise forms.ValidationError("RUT requerido.")
    rut = rut.replace(".", "").replace(" ", "").lower()

    if "-" in rut:
        num, dv = rut.split("-", 1)
    else:
        num, dv = rut[:-1], rut[-1]

    if not num.isdigit() or not re.match(r"^[\dk]$", dv):
        raise forms.ValidationError("RUT inválido.")

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


# --------------------------------------
#        FORMULARIO CHECKOUT
# --------------------------------------
class CheckoutForm(forms.Form):

    first_name = forms.CharField(label="Nombre", max_length=60)
    last_name  = forms.CharField(label="Apellido", max_length=60)
    rut        = forms.CharField(label="RUT", max_length=20)
    email      = forms.EmailField(label="Email", max_length=120)
    phone      = forms.CharField(label="Teléfono", max_length=30)

    # Dirección
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

    SHIPPING_CHOICES = (
        ("seleccionar", "Selecciona método..."),
        ("retiro", "Retiro en tienda"),
        ("envio", "Envío a domicilio"),
    )
    shipping_method = forms.ChoiceField(
        label="Envío", choices=SHIPPING_CHOICES, initial="envio"
    )

    # --------------------------------------
    # VALIDACIONES PERSONALIZADAS
    # --------------------------------------

    def clean_rut(self):
        return validar_rut_chileno(self.cleaned_data["rut"])

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        phone = re.sub(r"\s+", "", phone)

        if not re.match(r"^\+?56?\d{8,10}$", phone):
            raise ValidationError("Ingresa un teléfono válido (solo números).")

        return phone

    def clean_first_name(self):
        name = self.cleaned_data["first_name"].strip()
        if len(name) < 2:
            raise ValidationError("El nombre es demasiado corto.")
        return name

    def clean_last_name(self):
        last = self.cleaned_data["last_name"].strip()
        if len(last) < 2:
            raise ValidationError("El apellido es demasiado corto.")
        return last

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        try:
            validate_email(email)
        except:
            raise ValidationError("Correo inválido.")
        return email

    def clean_address_line(self):
        addr = self.cleaned_data["address_line"].strip()
        if len(addr) < 5:
            raise ValidationError("La dirección es muy corta.")
        return addr

    def clean_shipping_method(self):
        method = self.cleaned_data["shipping_method"]
        if method not in ["retiro", "envio"]:
            raise ValidationError("Selecciona un método de envío válido.")
        return method

    def clean_comuna(self):
        val = self.cleaned_data["comuna"].strip()
        if len(val) < 3:
            raise ValidationError("Comuna inválida.")
        return val

    def clean_ciudad(self):
        val = self.cleaned_data["ciudad"].strip()
        if len(val) < 3:
            raise ValidationError("Ciudad inválida.")
        return val

    def clean_region(self):
        val = self.cleaned_data["region"].strip()
        if len(val) < 3:
            raise ValidationError("Región inválida.")
        return val
