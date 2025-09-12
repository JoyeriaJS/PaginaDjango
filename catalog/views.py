from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q


from .forms import ProductForm, ProductImageForm, CategoryForm, MaterialForm
from .models import Product, Category, Material, ProductImage


@login_required
@user_passes_test(lambda u: u.is_staff)
def panel_home(request):
    return render(request, 'catalog/panel_home.html')

@login_required
def product_list(request):
    qs = Product.objects.select_related("category", "material").order_by("-updated_at", "-created_at")

    q = (request.GET.get("q") or "").strip()
    cat = (request.GET.get("cat") or "").strip()
    active = (request.GET.get("active") or "").strip()  # "1" | "0" | ""

    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(sku__icontains=q) |
            Q(description__icontains=q)
        )

    if cat.isdigit():
        qs = qs.filter(category_id=int(cat))

    # Solo filtra por activo si el parámetro viene explícito
    if active in ("1", "0"):
        qs = qs.filter(is_active=(active == "1"))

    paginator = Paginator(qs, 20)
    products = paginator.get_page(request.GET.get("page"))

    return render(request, "catalog/product_list.html", {
        "products": products,
        "categories": Category.objects.all(),
        "q": q,
        "cat": int(cat) if cat.isdigit() else None,
        "active": active,
        # métricas de diagnóstico (te ayudan a verificar)
        "total_count": Product.objects.count(),
        "shown_count": products.paginator.count,
    })

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f"Producto '{obj.name}' creado.")
            return redirect('catalog:product_list')
    else:
        form = ProductForm()
    return render(request, 'catalog/product_form.html', {'form': form, 'title': 'Crear producto'})


@login_required
def product_edit(request, pk):
    obj = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto actualizado.")
            return redirect('catalog:product_edit', pk=obj.pk)
    else:
        form = ProductForm(instance=obj)
    images = obj.images.all()
    return render(request, 'catalog/product_form.html', {'form': form, 'title': 'Editar producto', 'product': obj, 'images': images})

@login_required
@transaction.atomic
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Producto eliminado.')
        return redirect('catalog:product_list')
    return render(request, 'catalog/confirm_delete.html', {'object': product, 'name': product.name})

@login_required
def product_images(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductImageForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.save(commit=False)
            img.product = product
            img.save()
            messages.success(request, "Imagen subida.")
            return redirect('catalog:product_edit', pk=product.pk)
    else:
        form = ProductImageForm()
    return render(request, 'catalog/product_images.html', {'product': product, 'form': form})

@login_required
def image_set_primary(request, image_id):
    img = get_object_or_404(ProductImage, pk=image_id)
    ProductImage.objects.filter(product=img.product, is_primary=True).update(is_primary=False)
    img.is_primary = True
    img.save(update_fields=['is_primary'])
    messages.success(request, "Imagen marcada como principal.")
    return redirect('catalog:product_edit', pk=img.product_id)

@login_required
@transaction.atomic
def image_delete(request, image_id):
    img = get_object_or_404(ProductImage, pk=image_id)
    pid = img.product_id
    if request.method == 'POST':
        img.delete()
        messages.success(request, "Imagen eliminada.")
        return redirect('catalog:product_edit', pk=pid)
    return render(request, 'catalog/confirm_delete.html', {'object': img, 'name': img.alt or img.image.name})
@login_required
def category_list(request):
    return render(request, 'catalog/category_list.html', {'categories': Category.objects.order_by('name')})

@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada.')
            return redirect('catalog:category_list')
    else:
        form = CategoryForm()
    return render(request, 'catalog/simple_form.html', {'form': form, 'title': 'Crear categoría'})

@login_required
def category_edit(request, pk):
    obj = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría actualizada.')
            return redirect('catalog:category_list')
    else:
        form = CategoryForm(instance=obj)
    return render(request, 'catalog/simple_form.html', {'form': form, 'title': 'Editar categoría'})

@login_required
def category_delete(request, pk):
    obj = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Categoría eliminada.')
        return redirect('catalog:category_list')
    return render(request, 'catalog/confirm_delete.html', {'object': obj, 'name': obj.name})

@login_required
def material_list(request):
    q = (request.GET.get('q') or '').strip()
    qs = Material.objects.all().order_by('name')
    if q:
        qs = qs.filter(Q(name__icontains=q))

    items = Paginator(qs, 20).get_page(request.GET.get('page'))
    return render(request, 'catalog/material_list.html', {'items': items, 'q': q})

@login_required
def material_create(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Material creado.')
            return redirect('catalog:material_list')
    else:
        form = MaterialForm()
    return render(request, 'catalog/material_form.html', {'form': form, 'title': 'Nuevo material'})

@login_required
def material_edit(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, 'Material actualizado.')
            return redirect('catalog:material_list')
    else:
        form = MaterialForm(instance=material)
    return render(request, 'catalog/material_form.html', {'form': form, 'title': 'Editar material'})

@login_required
def material_delete(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        material.delete()
        messages.success(request, 'Material eliminado.')
        return redirect('catalog:material_list')
    # Si llegara por GET, muestra confirmación simple
    return render(request, 'catalog/confirm_delete.html', {'obj': material, 'type': 'material'})
