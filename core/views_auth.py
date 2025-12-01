from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User


# ============================
# REGISTER
# ============================
def register_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")

        if password != password2:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect("core:register")

        if User.objects.filter(username=email).exists():
            messages.error(request, "Este correo ya está registrado.")
            return redirect("core:register")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name
        )
        user.save()
        messages.success(request, "Cuenta creada correctamente. Inicia sesión.")
        return redirect("core:login")

    return render(request, "auth/register.html")


# ============================
# LOGIN
# ============================
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            messages.success(request, "Bienvenido de vuelta.")
            return redirect("core:home")  # puedes cambiarlo
        else:
            messages.error(request, "Credenciales incorrectas.")

    return render(request, "auth/login.html")


# ============================
# LOGOUT
# ============================
def logout_view(request):
    logout(request)
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect("core:home")
