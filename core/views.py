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
import mercadopago
from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest
from catalog.models import Product, FeaturedProduct, CatalogSection, Material
from .forms import CheckoutForm
from catalog.models import Order, OrderItem
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from accounts.models import Address
from django.db.models import Q
from django.db import models
from catalog.models import Category
from django.http import JsonResponse
import uuid



try:
    from weasyprint import HTML
except Exception:
    HTML = None




def home(request):
    categories = Category.objects.annotate(n=Count('products')).order_by('-n','name')[:8]
    latest_products = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    featured_products = FeaturedProduct.objects.filter(is_active=True).select_related('product')
    catalog_sections = CatalogSection.objects.filter(is_active=True)

    # ⭐ REVIEWS APROBADAS PARA TESTIMONIOS
    testimonials = Review.objects.filter(approved=True).order_by('-created_at')[:10]

    return render(request, "core/home.html", {
        "categories": categories,
        "latest_products": latest_products,
        "banners_hero": Banner.objects.filter(is_active=True, position=Banner.HOME_HERO).order_by('order','-updated_at')[:6],
        "banners_strip": Banner.objects.filter(is_active=True, position=Banner.HOME_STRIP).order_by('order','-updated_at')[:6],
        "featured_products": featured_products,
        "catalog_sections": catalog_sections,
        "testimonials": testimonials,   # 👈 AGREGADO AQUÍ
    })




# ---------- PRODUCTO (página pública de detalle) ----------
def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images'),
        pk=pk,
        is_active=True
    )

    related = (
        Product.objects.filter(is_active=True, category=product.category)
        .exclude(pk=product.pk)
        .prefetch_related('images')[:8]
    )

    # 🔥 Filtrar reseñas aprobadas (nuevo)
    approved_reviews = product.reviews.filter(approved=True).order_by('-created_at')

    return render(request, "core/product_detail.html", {
        "product": product,
        "related": related,
        "approved_reviews": approved_reviews,  # <<— agregado sin romper nada
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
    category = get_object_or_404(Category, pk=pk)

    qs = Product.objects.filter(is_active=True, category=category)

    # ---------------------------
    # Filtro por búsqueda interna
    # ---------------------------
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))

    # ---------------------------
    # Filtro por precio
    # ---------------------------
    min_price = request.GET.get("min")
    max_price = request.GET.get("max")

    if min_price and min_price.isdigit():
        qs = qs.filter(price__gte=int(min_price))

    if max_price and max_price.isdigit():
        qs = qs.filter(price__lte=int(max_price))

    # ---------------------------
    # Filtro por material
    # ---------------------------
    material = request.GET.get("material")
    if material and material != "all":
        qs = qs.filter(material_id=material)

    # ---------------------------
    # Filtro por stock
    # ---------------------------
    stock = request.GET.get("stock")
    if stock == "available":
        qs = qs.filter(stock__gt=3)
    elif stock == "low":
        qs = qs.filter(stock__gt=0, stock__lte=3)
    elif stock == "out":
        qs = qs.filter(stock=0)

    # ---------------------------
    # Orden
    # ---------------------------
    sort = request.GET.get("sort")

    if sort == "price_asc":
        qs = qs.order_by("price")
    elif sort == "price_desc":
        qs = qs.order_by("-price")
    elif sort == "new":
        qs = qs.order_by("-created_at")
    else:
        qs = qs.order_by("-created_at")  # default

    # ---------------------------
    # Paginación
    # ---------------------------
    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    # MATERIALES disponibles en esa categoría (para el filtro)
    materials = Material.objects.filter(product__category=category).distinct()

    return render(request, "core/category_products.html", {
        "category": category,
        "products": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "materials": materials,  # ← importante
    })



# ---------- CARRITO (basado en sesión) ----------
CART_SESSION_KEY = "cart"

def _get_cart(session):
    cart = session.get("cart", {})
    # cart = { "product_id_str": {"qty": int} }
    if not isinstance(cart, dict):
        cart = {}
    return cart

def _save_cart(session, cart):
    session[CART_SESSION_KEY] = cart
    session.modified = True

# core/views.py
from decimal import Decimal, ROUND_HALF_UP

def _cart_summary(cart):
    """
    Calcula resumen del carrito usando el PRECIO FINAL guardado en la sesión.
    Compatible con Mercado Pago.
    Devuelve:
      items, subtotal, tax, shipping, grand_total, count
    """
    items = []
    subtotal = Decimal("0")
    tax = Decimal("0")
    shipping = Decimal("0")

    for pid, data in cart.items():
        # ------------------------------
        # 1) CANTIDAD
        # ------------------------------
        qty = 0
        if isinstance(data, dict):
            raw_q = data.get("qty", 0)
            if isinstance(raw_q, dict):
                raw_q = raw_q.get("qty", 0)
            try:
                qty = int(raw_q or 0)
            except Exception:
                qty = 0
        else:
            try:
                qty = int(data or 0)
            except Exception:
                qty = 0

        if qty <= 0:
            continue

        # ------------------------------
        # 2) PRODUCTO
        # ------------------------------
        try:
            p = Product.objects.select_related("category").prefetch_related("images").get(pk=pid)
        except Product.DoesNotExist:
            continue

        # ------------------------------
        # 3) PRECIO CORRECTO (!!!)
        # ------------------------------
        # Primero intentamos leer el PRECIO FINAL EN EL CARRITO
        price = data.get("price")

        if price is None:
            # Si por alguna razón no está en el carrito,
            # usar precio final con descuento
            price = p.get_final_price()

        price = Decimal(str(price))

        # ------------------------------
        # 4) TOTAL POR LÍNEA
        # ------------------------------
        line_total = (price * qty).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        # Imagen
        img_url = None
        if hasattr(p, "images") and p.images.exists():
            img_url = p.images.first().image.url

        # ------------------------------
        # 5) AGREGAR AL LISTADO
        # ------------------------------
        items.append({
            "id": p.pk,
            "name": p.name,
            "qty": qty,
            "price": int(price),        # PRECIO FINAL usado por MP
            "total": int(line_total),   # TOTAL por producto
            "image_url": img_url,
            "category": getattr(p.category, "name", ""),
        })

        subtotal += line_total

    # ------------------------------
    # 6) TOTALES
    # ------------------------------
    subtotal = subtotal.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    grand_total = subtotal + tax + shipping
    grand_total = grand_total.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    count = sum(i["qty"] for i in items)

    # ------------------------------
    # 7) DEVOLVER ENTEROS
    # ------------------------------
    return (
        items,
        int(subtotal),
        int(tax),
        int(shipping),
        int(grand_total),
        int(count),
    )





def add_to_cart(request, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")

    product = get_object_or_404(Product, pk=pk)

    try:
        qty = int(request.POST.get("qty", "1"))
    except ValueError:
        qty = 1

    qty = max(1, qty)

    stock = product.stock
    cart = _get_cart(request.session)
    pid = str(product.pk)
    current_qty = int(cart.get(pid, {}).get("qty", 0))

    if stock is not None:
        remaining = max(0, stock - current_qty)
        if remaining <= 0:
            msg = f"“{product.name}” está agotado y no se puede agregar."
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "error": msg}, status=400)
            messages.error(request, msg)
            return redirect("core:cart_detail")

        if qty > remaining:
            qty = remaining
            if qty <= 0:
                msg = f"“{product.name}” está agotado y no se puede agregar."
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({"ok": False, "error": msg}, status=400)
                messages.error(request, msg)
                return redirect("core:cart_detail")

    # --------------------------------------------
    # 🔥 APLICAR PRECIO FINAL SEGÚN DESCUENTO
    # --------------------------------------------
    final_price = float(product.get_final_price())
    new_qty = current_qty + qty

    cart[pid] = {
        "qty": new_qty,
        "price": final_price
    }

    request.session["cart"] = cart
    request.session.modified = True

    msg_ok = f"Agregaste “{product.name}” ({qty} ud)."

    # ======================================================
    # 🔥 RESPUESTA AJAX PARA MOSTRAR POPUP (Shopify-style)
    # ======================================================
    if request.headers.get("x-requested-with") == "XMLHttpRequest":

        # <<--- agregado para popup
        items, subtotal, tax, shipping, grand_total, count = _cart_summary(cart)

        # <<--- agregado para popup
        return JsonResponse({
            "ok": True,
            "message": msg_ok,
            "name": product.name,          # <<--- agregado
            "subtotal": subtotal,          # <<--- agregado
            "cart_count": count            # tu variable original
        })

    messages.success(request, msg_ok)
    return redirect("core:cart_detail")

def get_normalized_cart(session):
    """
    Normaliza el carrito a formato:
      {"<product_id_str>": {"qty": int}}
    Acepta formatos viejos (lista de dicts) o valores raros y sanea.
    """
    cart = session.get("cart") or {}

    # Lista antigua: [{"id": 123, "qty": 2}, ...]
    if isinstance(cart, list):
        new = {}
        for it in cart:
            if not isinstance(it, dict):
                continue
            pid = it.get("id") or it.get("pk")
            if pid is None:
                continue
            raw_q = it.get("qty", 0)
            if isinstance(raw_q, dict):
                raw_q = raw_q.get("qty", 0)
            try:
                qty = int(raw_q or 0)
            except Exception:
                qty = 0
            if qty > 0:
                new[str(pid)] = {"qty": qty}
        session["cart"] = new
        session.modified = True
        return new

    # Si no es dict, resetea
    if not isinstance(cart, dict):
        session["cart"] = {}
        session.modified = True
        return {}

    # Es dict: asegurar que todos tengan {"qty": int}
    changed = False
    keys = list(cart.keys())
    for k in keys:
        v = cart.get(k)
        # soportar número suelto
        if not isinstance(v, dict):
            try:
                q = int(v or 0)
            except Exception:
                q = 0
            if q > 0:
                cart[k] = {"qty": q}
            else:
                cart.pop(k, None)
            changed = True
            continue

        # v es dict, pero qty podría ser otro dict
        raw_q = v.get("qty", 0)
        if isinstance(raw_q, dict):
            raw_q = raw_q.get("qty", 0)
        try:
            q = int(raw_q or 0)
        except Exception:
            q = 0

        if q > 0:
            v["qty"] = q
        else:
            cart.pop(k, None)
        changed = True

    if changed:
        session["cart"] = cart
        session.modified = True

    return cart



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
        return HttpResponseBadRequest("Invalid method")

    cart = _get_cart(request.session)
    changed_msgs = []

    for pid, item in list(cart.items()):
        field = f"qty_{pid}"
        if field not in request.POST:
            continue

        try:
            new_qty = int(request.POST[field])
        except ValueError:
            new_qty = 1

        new_qty = max(0, new_qty)

        # Producto real
        product = Product.objects.filter(pk=pid).first()
        if not product:
            cart.pop(pid, None)
            continue

        # Validar stock
        stock = product.stock
        if stock is not None and new_qty > stock:
            new_qty = stock
            changed_msgs.append(
                f"La cantidad de “{product.name}” se ajustó al stock disponible ({stock})."
            )

        if new_qty <= 0:
            cart.pop(pid, None)
        else:
            # 🔥 Mantener precio con descuento
            old_price = cart.get(pid, {}).get("price")
            if old_price is None:
                old_price = float(product.get_final_price())

            cart[pid] = {
                "qty": new_qty,
                "price": old_price
            }

    request.session["cart"] = cart
    request.session.modified = True

    # AJAX response
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        items, subtotal, tax, shipping, grand_total, count = _cart_summary(cart)

        return JsonResponse({
            "ok": True,
            "cart_count": count,
            "subtotal": subtotal,
            "grand_total": grand_total,
            "messages": changed_msgs,
            "empty": (count == 0),
        })

    return redirect("core:cart_detail")



   
    

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
    cart = get_normalized_cart(request.session)
    items, subtotal, tax, shipping, grand_total, count = _cart_summary(cart)

    # -------------------------
    # 🔥 APLICAR DESCUENTO AQUÍ
    # -------------------------
    coupon_code = request.session.get("coupon")
    discount_amount = Decimal("0")

    if coupon_code:
        d = _find_discount_by_code(coupon_code)
        if d:
            discount_amount = _discount_amount_for_cart(d, items, Decimal(subtotal))
        else:
            # Cupón inválido → limpiarlo
            request.session.pop("coupon", None)

    grand_total = Decimal(subtotal) - discount_amount
    if grand_total < 0:
        grand_total = Decimal("0")

    context = {
        "items": items,
        "subtotal": subtotal,
        "discount_code": coupon_code,
        "discount_amount": int(discount_amount),
        "grand_total": int(grand_total),
        "tax": tax,
        "shipping": shipping,
    }

    return render(request, "core/cart.html", context)

    
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


#Mercado Pago views
def _cart_lines_from_session(request):
    """
    Convierte el carrito de sesión en items compatibles con Mercado Pago,
    usando SIEMPRE el precio final guardado en la sesión.
    """

    raw_cart = request.session.get("cart") or {}
    if not isinstance(raw_cart, dict):
        return []

    items = []
    product_ids = []

    # Normalizar IDs
    for pid, data in raw_cart.items():
        try:
            product_ids.append(int(pid))
        except:
            continue

    products = Product.objects.filter(id__in=product_ids, is_active=True)

    for p in products:
        raw = raw_cart.get(str(p.id))

        # ================================
        # NORMALIZAR QTY
        # ================================
        qty = 0
        if isinstance(raw, dict):
            q = raw.get("qty", 0)
            if isinstance(q, dict):
                q = q.get("qty", 0)
            try:
                qty = int(q)
            except:
                qty = 0
        else:
            try:
                qty = int(raw)
            except:
                qty = 0

        if qty < 1:
            continue

        # ================================
        # 🔥 PRECIO FINAL DESDE SESIÓN
        # ================================
        final_price = raw.get("price")
        if final_price is None:
            final_price = float(p.get_final_price())  # fallback

        # ================================
        # IMAGEN
        # ================================
        img_url = None
        try:
            img = p.images.first()
            if img:
                img_url = img.image.url
        except:
            img_url = None

        # ================================
        # 🔥 ENVIAR A MERCADOPAGO
        # ================================
        items.append({
            "id": str(p.id),
            "title": p.name,
            "quantity": qty,
            "currency_id": "CLP",
            "unit_price": float(final_price),  # <<🔥 FIX OFICIAL AQUÍ
            "picture_url": img_url,
        })

    return items



def mp_checkout(request):
    if request.method not in ("GET", "POST"):
        return redirect("core:cart_detail")

    if not settings.MP_ACCESS_TOKEN:
        messages.error(request, "Falta configurar MP_ACCESS_TOKEN en el servidor.")
        return redirect("core:cart_detail")

    # --------------------------------------------
    # 🔥 OBTENER CARRITO
    # --------------------------------------------
    cart = request.session.get("cart") or {}
    items = _cart_lines_from_session(request)

    if not items:
        messages.error(request, "Tu carrito está vacío.")
        return redirect("core:cart_detail")

    # --------------------------------------------
    # 🔥 OBTENER DATOS DEL CHECKOUT
    # --------------------------------------------
    checkout_data = request.session.get("checkout_data")
    if not checkout_data:
        messages.warning(request, "Completa tus datos de envío y contacto.")
        return redirect("core:checkout")

    # =====================================================
    # 🔥 VALIDACIÓN DE STOCK (ANTI DOBLE COMPRA)
    # =====================================================
    for pid, line in cart.items():
        try:
            product = Product.objects.get(pk=pid, is_active=True)
        except Product.DoesNotExist:
            messages.error(request, "Uno de los productos ya no existe.")
            return redirect("core:cart_detail")

        qty = int(line.get("qty", 1))

        if product.stock < qty:
            messages.error(
                request,
                f"😓 {product.name} solo tiene {product.stock} unidades disponibles."
            )
            return redirect("core:cart_detail")

    # =====================================================
    # 🔥 CÁLCULO DE DESCUENTOS
    # =====================================================
    items_summary, subtotal, tax, shipping, grand_total, count = _cart_summary(cart)

    coupon_code = request.session.get("coupon")
    discount_amount = Decimal("0")

    if coupon_code:
        d = _find_discount_by_code(coupon_code)
        if d:
            discount_amount = _discount_amount_for_cart(
                d, items_summary, Decimal(subtotal)
            )

    # añadir descuento como item negativo
    if discount_amount > 0:
        items.append({
            "id": "DESCUENTO",
            "title": f"Descuento {coupon_code}",
            "quantity": 1,
            "currency_id": "CLP",
            "unit_price": float(-discount_amount),
        })

    # =====================================================
    # 🔥 ARMAR OBJETO PAYER
    # =====================================================
    payer = {
        "name": checkout_data.get("first_name", ""),
        "surname": checkout_data.get("last_name", ""),
        "email": checkout_data.get("email", ""),
        "phone": {"number": checkout_data.get("phone", "")},
        "identification": {"type": "RUT", "number": checkout_data.get("rut", "")},
        "address": {
            "zip_code": checkout_data.get("postal_code") or "",
            "street_name": checkout_data.get("address_line") or "",
        },
    }

    metadata = {
        "shipping_method": checkout_data.get("shipping_method"),
        "address_line": checkout_data.get("address_line"),
        "comuna": checkout_data.get("comuna"),
        "ciudad": checkout_data.get("ciudad"),
        "region": checkout_data.get("region"),
        "notes": checkout_data.get("notes"),
    }

    sdk = mercadopago.SDK(settings.MP_ACCESS_TOKEN)

    success_url = request.build_absolute_uri(reverse("core:mp_success"))
    failure_url = request.build_absolute_uri(reverse("core:mp_failure"))
    pending_url = request.build_absolute_uri(reverse("core:mp_pending"))
    notif_url   = request.build_absolute_uri(reverse("core:mp_webhook"))

    preference = {
        "items": items,
        "payer": payer,
        "metadata": metadata,
        "back_urls": {
            "success": success_url,
            "failure": failure_url,
            "pending": pending_url,
        },
        "auto_return": "approved",
        "binary_mode": True,
        "statement_descriptor": "CASTEABLE",
        "notification_url": notif_url,
    }

    # =====================================================
    # 🔥 CREAR PREFERENCIA EN MERCADOPAGO (SEGURO)
    # =====================================================
    try:
        pref_res = sdk.preference().create(preference)

        # debug opcional
        print("MP PREFERENCE RESPONSE:", pref_res)

        data = pref_res.get("response", {})
        init_point = data.get("init_point") or data.get("sandbox_init_point")

        if not init_point:
            messages.error(request,
                "No se pudo iniciar el pago en MercadoPago. Intenta nuevamente."
            )
            return redirect("core:checkout")

        return redirect(init_point)

    except Exception as e:
        print("⚠ ERROR MERCADOPAGO:", str(e))
        messages.error(request,
            "Hubo un error al conectar con MercadoPago. Por favor intenta nuevamente."
        )
        return redirect("core:checkout")




def _clear_cart(request):
    if "cart" in request.session:
        del request.session["cart"]
        request.session.modified = True

#def mp_success(request):
#    """
#    Vuelta de éxito. Aún sin guardar en BD.
#    Limpia carrito y muestra mensaje.
#    """
#    _clear_cart(request)
#    messages.success(request, "¡Pago aprobado! Gracias por tu compra.")
#    return redirect("/")

#def mp_failure(request):
 #   messages.error(request, "El pago fue rechazado o cancelado. Puedes intentar nuevamente.")
  #  return redirect("core:cart_detail")

#def mp_pending(request):
#    messages.info(request, "Tu pago quedó en estado pendiente. Te avisaremos al confirmarse.")
 #   return redirect("/")


# --- Webhook (opcional por ahora) --------------------------------------------
@csrf_exempt
def mp_webhook(request):
    """
    Punto de entrada para notificaciones de MP.
    Hoy solo responde 200 OK.
    Cuando quieras persistir la orden, validamos y guardamos aquí.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    # Si definiste un secreto, puedes validarlo con un header propio (ej: X-Webhook-Token)
    # token = request.headers.get("X-Webhook-Token")
    # if settings.MP_WEBHOOK_SECRET and token != settings.MP_WEBHOOK_SECRET:
    #     return HttpResponse(status=401)
    return HttpResponse(status=200)



#checkout form
@login_required(login_url="core:login")
def checkout(request, token):

    session_token = request.session.get("checkout_token")
    if not session_token or session_token != str(token):
        messages.error(request, "Tu sesión de checkout no es válida.")
        return redirect("core:start_checkout")

    # Protección: si el carrito está vacío
    cart = request.session.get("cart") or {}
    items, subtotal, tax, shipping, grand_total, count = _cart_summary(cart)

    if count <= 0:
        messages.info(request, "Tu carrito está vacío.")
        return redirect("core:cart_detail")

    # -----------------------------
    # 🔥 APLICAR DESCUENTO
    # -----------------------------
    coupon_code = request.session.get("coupon")
    discount_amount = Decimal("0")

    if coupon_code:
        d = _find_discount_by_code(coupon_code)
        if d:
            discount_amount = _discount_amount_for_cart(d, items, Decimal(subtotal))

    grand_total = Decimal(subtotal) - discount_amount
    if grand_total < 0:
        grand_total = Decimal("0")

    # ============================================================
    # 🔥 AUTOCOMPLETAR SOLO SI ES LA PRIMERA VEZ (NO PISA LO EXISTENTE)
    # ============================================================
    initial = request.session.get("checkout_data") or {}

    if not initial:
        default_addr = Address.objects.filter(user=request.user, is_default=True).first()
        if default_addr:
            initial = {
                "first_name": request.user.first_name or "",
                "last_name": request.user.last_name or "",
                "email": request.user.email or "",
                "address_line": default_addr.address_line,
                "comuna": default_addr.comuna,
                "ciudad": default_addr.ciudad,
                "region": default_addr.region,
                "notes": default_addr.extra or "",
            }

    # ============================================================

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():

            # Guardamos los datos completos
            request.session["checkout_data"] = form.cleaned_data
            request.session.modified = True

            # si hace clic en Pagar → MercadoPago
            if "pay" in request.POST:
                return redirect("core:mp_checkout")

            messages.success(request, "Datos guardados.")
            return redirect("core:checkout")

    else:
        form = CheckoutForm(initial=initial)

    # ============================================================
    # 🔥 PASAMOS REGIONES Y COMUNAS AL TEMPLATE
    # ============================================================
    ctx = {
        "form": form,
        "items": items,
        "subtotal": subtotal,
        "discount_code": coupon_code,
        "discount_amount": int(discount_amount),
        "grand_total": int(grand_total),
        "tax": tax,
        "shipping": shipping,
        "count": count,
        "regiones_json": json.dumps(cargar_regiones_comunas(), ensure_ascii=False),
    }

    return render(request, "core/checkout.html", ctx)

#token checkout

def start_checkout(request):
    token = uuid.uuid4()
    request.session["checkout_token"] = str(token)
    return redirect("core:checkout", token=token)



def mp_success(request):
    payment_id = request.GET.get("payment_id")
    status = request.GET.get("status")
    merchant_order_id = request.GET.get("merchant_order_id")

    checkout_data = request.session.get("checkout_data", {}).copy()

    # Totales antes de borrar carrito
    cart = request.session.get("cart") or {}
    items, subtotal, tax, shipping, grand_total, count = _cart_summary(cart)

    # 1) CREAR ORDEN
    order = Order.objects.create(
        payment_id=payment_id,
        status=status,
        merchant_order_id=merchant_order_id,
        total=grand_total,
        first_name=checkout_data.get("first_name"),
        last_name=checkout_data.get("last_name"),
        email=checkout_data.get("email"),
        phone=checkout_data.get("phone"),
        address_line=checkout_data.get("address_line"),
        comuna=checkout_data.get("comuna"),
        ciudad=checkout_data.get("ciudad"),
        region=checkout_data.get("region"),
    )

    # GUARDAR ITEMS
    for item in items:
        OrderItem.objects.create(
            order=order,
            product_id=item["id"],
            quantity=item["qty"],
            price=item["price"]
        )

    # 2) Limpiar carrito
    if "cart" in request.session:
        del request.session["cart"]
    request.session.modified = True

    # 3) Preparar PDF
    html_string = render_to_string("core/pdf_invoice.html", {
        "order": order,
        "items": items,
    })

    pdf_file = HTML(string=html_string).write_pdf()

    # 4) Enviar correo al cliente
    email = EmailMessage(
        subject="Comprobante de tu compra — Artesanías Pachy",
        body="Adjuntamos tu comprobante de compra.",
        to=[order.email]
    )
    email.attach(f"Comprobante-{order.payment_id}.pdf", pdf_file, "application/pdf")
    email.send(fail_silently=True)

    # 5) Render página
    return render(request, "core/payment_success.html", {
        "order": order,
        "items": items,
        "grand_total": grand_total,
    })


def mp_failure(request):
    return render(request, "core/payment_failure.html", {
        "payment_id": request.GET.get("payment_id"),
        "status": request.GET.get("status")
    })


def mp_pending(request):
    return render(request, "core/payment_pending.html", {
        "payment_id": request.GET.get("payment_id"),
        "status": request.GET.get("status")
    })

def order_pdf(request, payment_id):
    order = get_object_or_404(Order, payment_id=payment_id)
    items = order.items.all()

    html_string = render_to_string("core/pdf_invoice.html", {
        "order": order,
        "items": items,
    })

    pdf = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename=Comprobante-{payment_id}.pdf"
    return response


#CATEGORIES
def category_all(request):
    categories = Category.objects.all().order_by("name")
    return render(request, "core/category_all.html", {"categories": categories})


def politica_privacidad(request):
    return render(request, "core/politica_privacidad.html")

def terminos_condiciones(request):
    return render(request, "core/terminos_condiciones.html")

def politica_reembolsos(request):
    return render(request, "core/politica_reembolsos.html")

def politica_cookies(request):
    return render(request, "core/politica_cookies.html")

def search_ajax(request):
    q = request.GET.get("q", "").strip()

    # Si la caja está vacía → no mostrar nada
    if not q:
        return JsonResponse({"results": []})

    # Buscar productos
    products = (
        Product.objects.filter(is_active=True, name__icontains=q)
        .order_by("-created_at")[:8]
    )

    results = []

    for p in products:
        # Obtener imagen principal SI EXISTE
        image_url = None
        if p.images.exists():
            image_url = p.images.first().image.url

        results.append({
            "name": p.name,
            "price": f"${p.price:,.0f}".replace(",", "."),
            "url": p.get_absolute_url(),
            "image": image_url,
        })

    return JsonResponse({"results": results})



def category_all(request):
    categories = Category.objects.all().order_by("name")
    return render(request, "core/category_all.html", {"categories": categories})


from django.views.decorators.http import require_POST
from catalog.models import Review


@require_POST
def add_review(request):
    product_id = request.POST.get("product_id")
    name = request.POST.get("name", "").strip()
    rating = int(request.POST.get("rating", 5))
    comment = request.POST.get("comment", "").strip()

    if not product_id or not name or not comment:
        return JsonResponse({"ok": False, "error": "Faltan campos."}, status=400)

    product = get_object_or_404(Product, pk=product_id)

    # ✔ Crear reseña como pendiente
    review = Review.objects.create(
        product=product,
        name=name,
        rating=max(1, min(5, rating)),
        comment=comment,
        approved=False  # 🔥 NO se publica automáticamente
    )

    return JsonResponse({
        "ok": True,
        "message": "Reseña enviada y pendiente de aprobación."
    })

from django.http import JsonResponse
from catalog.models import NewsletterSubscriber

def subscribe_newsletter(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"})

    email = request.POST.get("email", "").strip().lower()

    if not email:
        return JsonResponse({"ok": False, "error": "Email vacío"})

    # Evitar duplicados
    if NewsletterSubscriber.objects.filter(email=email).exists():
        return JsonResponse({"ok": True, "msg": "Ya estabas suscrito"})

    NewsletterSubscriber.objects.create(email=email)

    return JsonResponse({"ok": True, "msg": "¡Gracias por suscribirte!"})
