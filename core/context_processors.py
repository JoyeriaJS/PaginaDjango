from django.db.models import Prefetch
from cms.models import MenuItem

def cart_badge(request):
    """
    Devuelve cart_count robusto, sin romper aunque el carrito tenga
    distintos formatos (dict nuevo, lista antigua, o valores raros).
    """
    cart = request.session.get("cart", {})
    count = 0

    # Formato nuevo: {"123": {"qty": 2}, "456": {"qty": 1}}
    if isinstance(cart, dict):
        for v in cart.values():
            if isinstance(v, dict):
                try:
                    count += int(v.get("qty", 0) or 0)
                except Exception:
                    pass
            else:
                # por si alguien guardó directamente un número
                try:
                    count += int(v or 0)
                except Exception:
                    pass

    # Formato antiguo: [{"id": 123, "qty": 2}, ...]
    elif isinstance(cart, list):
        for it in cart:
            if isinstance(it, dict):
                try:
                    count += int(it.get("qty", 0) or 0)
                except Exception:
                    pass

    else:
        # Cualquier otro formato extraño: intentar castear
        try:
            count = int(cart or 0)
        except Exception:
            count = 0

    return {"cart_count": count}


def main_menu(request):
    """
    Deja este como lo tengas. Ejemplo mínimo:
    """
    return {
        "main_menu": [
            # {"title": "Inicio", "url": "/"},
            # ...
        ]
    }

    