from django.db.models import Prefetch
from cms.models import MenuItem

def cart_badge(request):
    cart = request.session.get("cart", {})
    count = sum(cart.values()) if isinstance(cart, dict) else 0
    return {"cart_count": count}

def main_menu(request):
    # Filtra raíz (sin padre) y solo activos
    roots_qs = MenuItem.objects.filter(is_active=True, parent__isnull=True).order_by('order','id')

    # Si no es staff, no mostrar items solo para staff
    if not request.user.is_staff:
        roots_qs = roots_qs.filter(staff_only=False)

    # Prefetch de hijos también filtrados por activo y staff
    children_qs = MenuItem.objects.filter(is_active=True).order_by('order','id')
    if not request.user.is_staff:
        children_qs = children_qs.filter(staff_only=False)

    roots_qs = roots_qs.prefetch_related(Prefetch('children', queryset=children_qs))

    # Retorna un queryset de MenuItem (objetos) con .children ya filtrados
    return {"main_menu": roots_qs}