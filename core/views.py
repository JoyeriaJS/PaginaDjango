from django.shortcuts import render
from django.db.models import Count
from catalog.models import Product, Category, Discount
from cms.models import Banner
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from decimal import Decimal
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from decimal import Decimal, ROUND_HALF_UP
from .models import Order, OrderItem


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
    product = get_object_or_404(Product.objects.select_related('category').prefetch_related('images'), pk=pk, is_active=True)
    related = (Product.objects.filter(is_active=True, category=product.category)
               .exclude(pk=product.pk).prefetch_related('images')[:8])
    return render(request, "core/product_detail.html", {
        "product": product,
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

# -------------Search -------------------
def search(request):
    q = request.GET.get("q", "").strip()
    results = Product.objects.filter(is_active=True)
    if q:
        results = results.filter(name__icontains=q)
    results = results.order_by("-created_at")[:48]
    return render(request, "core/search.html", {"q": q, "results": results})

def category_list(request, pk):
    category = Category.objects.get(pk=pk)

    qs = Product.objects.filter(is_active=True, category=category)

    # --- filtros ---
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))

    try:
        min_price = int(request.GET.get("min", "") or 0)
    except ValueError:
        min_price = 0
    try:
        max_price = int(request.GET.get("max", "") or 0)
    except ValueError:
        max_price = 0

    if min_price > 0:
        qs = qs.filter(price__gte=min_price)
    if max_price > 0:
        qs = qs.filter(price__lte=max_price)

    # --- orden ---
    sort = request.GET.get("sort") or ""
    if sort == "price_asc":
        qs = qs.order_by("price", "-created_at")
    elif sort == "price_desc":
        qs = qs.order_by("-price", "-created_at")
    else:
        # "new" u vacío -> más nuevos primero
        qs = qs.order_by("-created_at")

    # --- paginación ---
    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "core/category_products.html", {
        "category": category,
        "products": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
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

    discount_code = request.session.get("coupon")
    discount_amount = Decimal("0.00")
    if discount_code:
        d = _find_discount_by_code(discount_code)
        if d:
            discount_amount = _discount_amount_for_cart(d, items, subtotal)

    # aplicar descuento al total
    grand_total = max(Decimal("0.00"), grand_total - discount_amount)

    return render(request, "core/cart.html", {
        "items": items,
        "subtotal": subtotal,
        "shipping": shipping,
        "tax": tax,
        "discount_amount": discount_amount,
        "discount_code": discount_code if discount_amount > 0 else None,
        "grand_total": grand_total,
    })
    
#DESCUENTOS
def _find_discount_by_code(code):
    now = timezone.now()
    try:
        d = Discount.objects.get(code__iexact=code.strip(), is_active=True)
    except Discount.DoesNotExist:
        return None
    if d.start_at and d.start_at > now: return None
    if d.end_at and d.end_at < now: return None
    if d.usage_limit and d.times_used >= d.usage_limit: return None
    return d

def _money(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def _discount_amount_for_cart(d, items, subtotal):
    """
    Calcula el monto de descuento aplicable.
    - d: instancia de Discount
    - items: lista de dicts del carrito (id, qty, price, total, category)
    - subtotal: total bruto del carrito
    """
    # Validar mínimo de compra
    if subtotal < (d.min_subtotal or Decimal("0")):
        return Decimal("0.00")

    base = Decimal("0.00")

    if d.scope == Discount.SCOPE_ALL:
        base = subtotal
    elif d.scope == Discount.SCOPE_PRODUCT and d.product_id:
        base = sum((it["total"] for it in items if it["id"] == d.product_id), Decimal("0.00"))
    elif d.scope == Discount.SCOPE_CATEGORY and d.category_id:
        # Aquí comparamos contra el nombre de la categoría del item
        base = sum((it["total"] for it in items if it.get("category") == d.category.name), Decimal("0.00"))

    if base <= 0:
        return Decimal("0.00")

    if d.dtype == Discount.PERCENT:
        amt = (base * (Decimal(d.value) / Decimal("100")))
    else:  # d.dtype == FIXED
        amt = min(base, Decimal(d.value))

    return _money(amt)
@require_POST
def apply_coupon(request):
    code = (request.POST.get('coupon') or '').strip()
    d = _find_discount_by_code(code)
    if not d:
        messages.error(request, "Código inválido o no vigente.")
        return redirect('core:cart_detail')
    request.session['coupon'] = d.code
    request.session.modified = True
    messages.success(request, f"Cupón “{d.code}” aplicado.")
    return redirect('core:cart_detail')

@require_POST
def remove_coupon(request):
    if request.session.get('coupon'):
        del request.session['coupon']
        request.session.modified = True
        messages.success(request, "Cupón quitado.")
    return redirect('core:cart_detail')