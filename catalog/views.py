from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProductForm, ProductImageForm, CategoryForm, MaterialForm
from .models import Product, Category, Material, ProductImage

@login_required
def product_list(request):
    qs = Product.objects.select_related('category','material').order_by('-updated_at')
    q = request.GET.get('q')
    cat = request.GET.get('cat')
    active = request.GET.get('active')
    if q:
        qs = qs.filter(name__icontains=q) | qs.filter(sku__icontains=q)
    if cat:
        qs = qs.filter(category_id=cat)
    if active in ('1','0'):
        qs = qs.filter(is_active=(active=='1'))
    products = Paginator(qs, 20).get_page(request.GET.get('page'))
    return render(request, 'catalog/product_list.html', {
        'products': products,
        'categories': Category.objects.all(),
        'q': q or '', 'cat': int(cat) if cat else None, 'active': active
    })

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Producto creado correctamente.')
            return redirect('catalog:product_edit', pk=product.pk)
    else:
        form = ProductForm()
    return render(request, 'catalog/product_form.html', {'form': form, 'title': 'Crear producto'})

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado.')
            return redirect('catalog:product_edit', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    images = product.images.all()
    return render(request, 'catalog/product_form.html', {'form': form, 'title': 'Editar producto', 'product': product, 'images': images})

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
            if img.is_primary:
                ProductImage.objects.filter(product=product, is_primary=True).update(is_primary=False)
            img.save()
            messages.success(request, 'Imagen agregada.')
            return redirect('catalog:product_edit', pk=product.pk)
    else:
        form = ProductImageForm()
    return render(request, 'catalog/product_images.html', {'product': product, 'form': form})

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
    return render(request, 'catalog/material_list.html', {'items': Material.objects.order_by('name')})

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
    return render(request, 'catalog/simple_form.html', {'form': form, 'title': 'Crear material'})

@login_required
def material_edit(request, pk):
    obj = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        form = MaterialForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Material actualizado.')
            return redirect('catalog:material_list')
    else:
        form = MaterialForm(instance=obj)
    return render(request, 'catalog/simple_form.html', {'form': form, 'title': 'Editar material'})

@login_required
def material_delete(request, pk):
    obj = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Material eliminado.')
        return redirect('catalog:material_list')
    return render(request, 'catalog/confirm_delete.html', {'object': obj, 'name': obj.name})
