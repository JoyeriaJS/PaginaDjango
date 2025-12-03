from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User

from .models import Address
from catalog.models import Order
from .forms import AddressForm

# PANEL GENERAL
@login_required
def dashboard(request):
    latest_order = Order.objects.filter(email=request.user.email).order_by("-created_at").first()
    addresses = request.user.addresses.all()

    return render(request, "accounts/dashboard.html", {
        "latest_order": latest_order,
        "addresses": addresses[:1],
    })


# PERFIL
@login_required
def profile(request):
    return render(request, "accounts/profile.html")

@login_required
def profile_edit(request):
    if request.method == "POST":
        request.user.first_name = request.POST.get("first_name")
        request.user.last_name = request.POST.get("last_name")
        request.user.email = request.POST.get("email")
        request.user.save()
        messages.success(request, "Perfil actualizado correctamente.")
        return redirect("accounts:profile")

    return render(request, "accounts/profile_edit.html")

# DIRECCIONES
@login_required
def address_list(request):
    addresses = request.user.addresses.all()
    return render(request, "accounts/address_list.html", {"addresses": addresses})

@login_required
def address_create(request):
    if request.method == "POST":
        Address.objects.create(
            user=request.user,
            name=request.POST["name"],
            address_line=request.POST["address_line"],
            comuna=request.POST["comuna"],
            ciudad=request.POST["ciudad"],
            region=request.POST["region"],
            extra=request.POST.get("extra", "")
        )
        messages.success(request, "Dirección agregada correctamente.")
        return redirect("accounts:address_list")

    return render(request, "accounts/address_create.html")

@login_required
def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)

    if request.method == "POST":
        address.name = request.POST["name"]
        address.address_line = request.POST["address_line"]
        address.comuna = request.POST["comuna"]
        address.ciudad = request.POST["ciudad"]
        address.region = request.POST["region"]
        address.extra = request.POST.get("extra", "")
        address.save()

        messages.success(request, "Dirección actualizada.")
        return redirect("accounts:address_list")

    return render(request, "accounts/address_edit.html", {"address": address})

@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    messages.success(request, "Dirección eliminada.")
    return redirect("accounts:address_list")


@login_required
def address_set_default(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)

    # quitar default anterior
    request.user.addresses.update(is_default=False)
    address.is_default = True
    address.save()

    messages.success(request, "Dirección marcada como predeterminada.")
    return redirect("accounts:address_list")


# HISTORIAL
@login_required
def orders_list(request):
    orders = Order.objects.filter(email=request.user.email).order_by("-created_at")
    return render(request, "accounts/orders_list.html", {"orders": orders})

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, email=request.user.email)
    return render(request, "accounts/order_detail.html", {"order": order})




def address_create(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            direccion = form.save(commit=False)
            direccion.user = request.user
            direccion.save()
            return redirect("accounts:address_list")
    else:
        form = AddressForm()

    return render(request, "accounts/address_create.html", {"form": form})
