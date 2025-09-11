from django import template
from urllib.parse import urlparse

register = template.Library()

@register.simple_tag
def cl_transform(url, w=None, h=None, mode='fill'):
    """
    Inserta /upload/w_...,h_...,c_.../ en URLs de Cloudinary.
    Si no es Cloudinary, devuelve la URL tal cual.
    """
    if not url:
        return url
    try:
        parsed = urlparse(url)
        if 'res.cloudinary.com' not in parsed.netloc:
            return url
        # url: https://res.cloudinary.com/<cloud>/image/upload/v.../path.jpg
        parts = url.split('/upload/')
        if len(parts) != 2:
            return url
        # map fit mode -> Cloudinary c_*
        c = {
            'fill': 'c_fill',
            'fit': 'c_fit',
            'pad': 'c_pad',
            'scale': 'c_scale',
        }.get(mode, 'c_fill')
        t = []
        if w: t.append(f"w_{int(w)}")
        if h: t.append(f"h_{int(h)}")
        t.append(c)
        transform = "/upload/" + ",".join(t) + "/"
        return parts[0] + transform + parts[1]
    except Exception:
        return url
