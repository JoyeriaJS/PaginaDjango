from django.db import models
from django.utils.text import slugify

# --- compat para migraciones antiguas (déjala aunque no la uses) ---
def product_image_path(instance, filename):
    return f"products/{getattr(instance, 'product_id', 'unknown')}/{filename}"
# -------------------------------------------------------------------


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    class Meta:
        ordering = ['name']
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

class Material(models.Model):
    name = models.CharField(max_length=120, unique=True)
    class Meta:
        ordering = ['name']
        verbose_name = 'Material'
        verbose_name_plural = 'Materiales'
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True)
    sku = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
    def __str__(self):
        return f"{self.name} ({self.sku})"
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.sku}")
        return super().save(*args, **kwargs)


class ProductImage(models.Model):
    product = models.ForeignKey('Product', related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/%Y/%m/')
    alt = models.CharField(max_length=120, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', '-created_at']

    def __str__(self):
        return f"{self.product_id} - {self.alt or self.image.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_primary:
            ProductImage.objects.filter(product=self.product).exclude(pk=self.pk).update(is_primary=False)


class Discount(models.Model):
    PERCENT = 'P'
    FIXED = 'F'
    TYPE_CHOICES = [(PERCENT,'Porcentaje'), (FIXED,'Monto fijo')]

    SCOPE_ALL = 'ALL'
    SCOPE_PRODUCT = 'PROD'
    SCOPE_CATEGORY = 'CAT'
    SCOPE_CHOICES = [(SCOPE_ALL,'Todos los productos'), (SCOPE_PRODUCT,'Un producto'), (SCOPE_CATEGORY,'Una categoría')]

    name = models.CharField('Nombre interno', max_length=120)
    code = models.CharField('Código (cupón)', max_length=40, unique=True, null=True, blank=True)
    dtype = models.CharField('Tipo', max_length=1, choices=TYPE_CHOICES, default=PERCENT)
    value = models.DecimalField('Valor', max_digits=12, decimal_places=2, help_text='Si %: 10 = 10%; si fijo: 5000 = $5.000')
    scope = models.CharField('Ámbito', max_length=4, choices=SCOPE_CHOICES, default=SCOPE_ALL)
    product = models.ForeignKey('catalog.Product', null=True, blank=True, on_delete=models.CASCADE)
    category = models.ForeignKey('catalog.Category', null=True, blank=True, on_delete=models.CASCADE)
    min_subtotal = models.DecimalField('Mínimo compra', max_digits=12, decimal_places=2, default=0)
    start_at = models.DateTimeField('Desde', null=True, blank=True)
    end_at = models.DateTimeField('Hasta', null=True, blank=True)
    usage_limit = models.PositiveIntegerField('Límite de usos', null=True, blank=True)
    times_used = models.PositiveIntegerField('Usos', default=0)
    is_active = models.BooleanField('Activo', default=True)
    stackable = models.BooleanField('Acumulable', default=False)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.name or (self.code or f"Descuento {self.id}")