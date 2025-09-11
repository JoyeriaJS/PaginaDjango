from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from .models import Banner
from .forms import BannerForm

@login_required
def banner_list(request):
    qs = Banner.objects.order_by('position','order','-updated_at')
    position = request.GET.get('position')
    if position:
        qs = qs.filter(position=position)
    paginator = Paginator(qs, 20)
    banners = paginator.get_page(request.GET.get('page'))
    return render(request, 'cms/banner_list.html', {'banners': banners, 'position': position or ''})

@login_required
def banner_create(request):
    if request.method == 'POST':
        form = BannerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Banner creado.')
            return redirect('cms:banner_list')
    else:
        form = BannerForm()
    return render(request, 'cms/banner_form.html', {'form': form, 'title': 'Crear banner'})

@login_required
def banner_edit(request, pk):
    obj = get_object_or_404(Banner, pk=pk)
    if request.method == 'POST':
        form = BannerForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Banner actualizado.')
            return redirect('cms:banner_list')
    else:
        form = BannerForm(instance=obj)
    return render(request, 'cms/banner_form.html', {'form': form, 'title': 'Editar banner', 'banner': obj})

@login_required
def banner_delete(request, pk):
    obj = get_object_or_404(Banner, pk=pk)
    if request.method == 'POST':
        name = obj.title or obj.image.name
        obj.delete()
        messages.success(request, f"Banner '{name}' eliminado.")
        return redirect('cms:banner_list')
    return render(request, 'catalog/confirm_delete.html', {'object': obj, 'name': obj.title or obj.image.name})
