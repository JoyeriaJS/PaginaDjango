from django.db import models

def banner_upload_path(instance, filename):
    return f"banners/{instance.position}/{filename}"

class Banner(models.Model):
    HOME_HERO = 'home_hero'
    HOME_STRIP = 'home_strip'
    POSITIONS = [
        (HOME_HERO, 'Home — Hero (principal)'),
        (HOME_STRIP, 'Home — Tira (debajo del hero)'),
    ]

    title = models.CharField('Título', max_length=150, blank=True)
    subtitle = models.CharField('Subtítulo', max_length=200, blank=True)
    image = models.ImageField('Imagen', upload_to=banner_upload_path)
    link_url = models.URLField('URL del botón', blank=True)
    link_label = models.CharField('Texto del botón', max_length=40, blank=True, default='Ver más')
    position = models.CharField('Ubicación', max_length=40, choices=POSITIONS, default=HOME_HERO)
    order = models.PositiveIntegerField('Orden', default=0)
    is_active = models.BooleanField('Activo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', 'order', '-updated_at']

    def __str__(self):
        return f"{self.get_position_display()} · {self.title or self.image.name}"
