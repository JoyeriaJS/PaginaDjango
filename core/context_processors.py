def cart_badge(request):
    cart = request.session.get("cart", {})
    count = sum(cart.values()) if isinstance(cart, dict) else 0
    return {"cart_count": count}
