from django.shortcuts import render
from django.db.models import Count
from catalog.models import Product, Category
from cms.models import Banner
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from decimal import Decimal
from django.core.paginator import Paginator
from django.http import JsonResponse

def home(request):
    categories = Category.objects.annotate(n=Count('products')).order_by('-n','name')[:8]
    latest_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    return render(request, "core/home.html", {
        "categories": categories,
        "latest_products": latest_products,
        "banners_hero": Banner.objects.filter(is_active=True, position=Banner.HOME_HERO).order_by('order','-updated_at')[:6],
        "banners_strip": Banner.objects.filter(is_active=True, position=Banner.HOME_STRIP).order_by('order','-updated_at')[:6],
    })

# ---------- PRODUCTO (página pública de detalle) ----------
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related('category'), pk=pk, is_active=True)
    images = product.images.all()  # la primera es principal por el ordering
    related = Product.objects.filter(is_active=True, category=product.category).exclude(pk=product.pk).order_by('-created_at')[:8]
    return render(request, "core/product_detail.html", {
        "product": product,
        "images": images,
        "related": related,
    })

def category_products(request, pk):
    category = get_object_or_404(Category, pk=pk)
    qs = Product.objects.filter(is_active=True, category=category).order_by('-created_at')
    products = Paginator(qs, 24).get_page(request.GET.get('page'))
    return render(request, "core/category_products.html", {
        "category": category,
        "products": products,
    })


# ---------- CARRITO (basado en sesión) ----------
CART_SESSION_KEY = "cart"

def _get_cart(session):
    return session.get(CART_SESSION_KEY, {})

def _save_cart(session, cart):
    session[CART_SESSION_KEY] = cart
    session.modified = True

def _cart_summary(cart):
    pids = [int(pid) for pid in cart.keys()] or []
    products = Product.objects.filter(pk__in=pids, is_active=True).select_related('category')
    pmap = {p.pk: p for p in products}
    items = []
    subtotal = Decimal("0.00")
    for pid_str, qty in cart.items():
        pid = int(pid_str)
        product = pmap.get(pid)
        if not product:
            continue
        price = Decimal(str(product.price))
        total = price * qty
        items.append({
            "id": pid,
            "name": product.name,
            "category": product.category.name if product.category_id else "",
            "qty": qty,
            "price": price,
            "total": total,
            "image_url": getattr(product.images.first(), "image", None).url if product.images.first() else None,
        })
        subtotal += total
    shipping = Decimal("0.00")
    tax = Decimal("0.00")
    grand_total = subtotal + shipping + tax
    count = sum(cart.values())
    return items, subtotal, tax, shipping, grand_total, count

def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    if request.method == "POST":
        try:
            qty = int(request.POST.get("qty", "1"))
        except ValueError:
            qty = 1
        qty = max(1, min(qty, 999))
        cart = _get_cart(request.session)
        pid = str(product.pk)
        cart[pid] = cart.get(pid, 0) + qty
        _save_cart(request.session, cart)
        items, subtotal, tax, shipping, grand_total, count = _cart_summary(cart)

        # AJAX -> JSON
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "ok": True,
                "message": f"Agregado {qty}× “{product.name}”",
                "cart_count": count,
                "subtotal": str(subtotal),
                "grand_total": str(grand_total),
            })

        messages.success(request, f"Agregado {qty}× “{product.name}”.")
        return redirect('core:cart_detail')

    return redirect('core:product_detail', pk=pk)

def remove_from_cart(request, pk):
    if request.method != "POST":
        return redirect('core:cart_detail')
    cart = _get_cart(request.session)
    pid = str(pk)
    if pid in cart:
        del cart[pid]
        _save_cart(request.session, cart)
    items, subtotal, tax, shipping, grand_total, count = _cart_summary(cart)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "ok": True,
            "cart_count": count,
            "subtotal": str(subtotal),
            "grand_total": str(grand_total),
            "empty": count == 0,
        })

    messages.success(request, "Producto eliminado del carrito.")
    return redirect('core:cart_detail')

def update_cart(request):
    if request.method != "POST":
        return redirect('core:cart_detail')

    cart = {}
    for key, value in request.POST.items():
        if key.startswith("qty_"):
            pid = key.replace("qty_", "")
            try:
                qty = int(value)
            except ValueError:
                qty = 1
            if qty > 0:
                cart[pid] = min(qty, 999)

    _save_cart(request.session, cart)
    items, subtotal, tax, shipping, grand_total, count = _cart_summary(cart)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        # devolvemos totales y el listado mínimo para que el front actualice
        return JsonResponse({
            "ok": True,
            "cart_count": count,
            "subtotal": str(subtotal),
            "grand_total": str(grand_total),
            "lines": [
                {"id": it["id"], "qty": it["qty"], "line_total": str(it["total"])}
                for it in items
            ],
            "empty": count == 0,
        })

    messages.success(request, "Carrito actualizado.")
    return redirect('core:cart_detail')

def clear_cart(request):
    if request.method != "POST":
        return redirect('core:cart_detail')
    request.session[CART_SESSION_KEY] = {}
    request.session.modified = True
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "cart_count": 0, "empty": True})
    messages.success(request, "Carrito vaciado.")
    return redirect('core:cart_detail')

def cart_detail(request):
    cart = _get_cart(request.session)
    items, subtotal, tax, shipping, grand_total, count = _cart_summary(cart)
    return render(request, "core/cart.html", {
        "items": items,
        "subtotal": subtotal,
        "shipping": shipping,
        "tax": tax,
        "grand_total": grand_total,
    })