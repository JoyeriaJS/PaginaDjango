from django.db import models
from django.utils.text import slugify

def banner_upload_path(instance, filename):
    return f"banners/{instance.position}/{filename}"

FIT_CHOICES = [
    ('fill', 'Recortar para llenar (c_fill)'),
    ('fit', 'Ajustar sin recortar (c_fit)'),
    ('pad', 'Ajustar con bordes (c_pad)'),
    ('scale', 'Escalar (c_scale)'),
]

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
    target_width  = models.PositiveIntegerField('Ancho deseado (px)', default=1200)
    target_height = models.PositiveIntegerField('Alto deseado (px)', default=400)
    fit_mode      = models.CharField('Modo de ajuste', max_length=10, choices=FIT_CHOICES, default='fill')

    class Meta:
        ordering = ['position', 'order', '-updated_at']

    def __str__(self):
        return f"{self.get_position_display()} · {self.title or self.image.name}"

class MenuItem(models.Model):
    title = models.CharField('Título', max_length=80)
    url = models.CharField('URL', max_length=255, help_text='Ej: /#categorias, /panel/, /categoria/12/')
    order = models.PositiveIntegerField('Orden', default=0)
    is_active = models.BooleanField('Activo', default=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    open_in_new_tab = models.BooleanField('Abrir en nueva pestaña', default=False)
    staff_only = models.BooleanField('Solo staff', default=False)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Elemento de menú'
        verbose_name_plural = 'Menú superior'

    def __str__(self):
        return self.title
