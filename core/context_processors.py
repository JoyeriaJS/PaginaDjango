from django.db.models import Prefetch
from cms.models import MenuItem

def cart_badge(request):
    cart = request.session.get("cart", {})
    count = sum(cart.values()) if isinstance(cart, dict) else 0
    return {"cart_count": count}

def main_menu(request):
    qs = MenuItem.objects.filter(is_active=True, parent__isnull=True).order_by('order','id')
    # Filtrado por staff
    if not request.user.is_staff:
        qs = qs.filter(staff_only=False)

    # prefetch de hijos visibles
    children = MenuItem.objects.filter(is_active=True, parent__in=qs).order_by('order','id')
    if not request.user.is_staff:
        children = children.filter(staff_only=False)

    child_map = {}
    for c in children:
        child_map.setdefault(c.parent_id, []).append(c)

    items = []
    for m in qs:
        items.append({
            "title": m.title, "url": m.url, "new": m.open_in_new_tab,
            "children": child_map.get(m.id, [])
        })
    return {"main_menu": items}

    # core/context_processors.py  (ya existe; agrega esto)
def site_settings(request):
    from cms.models import SiteSettings
    # Trae el único registro; si no existe, lo crea con valores por defecto.
    ss, _ = SiteSettings.objects.get_or_create(id=1)
    return {"site_settings": ss}
