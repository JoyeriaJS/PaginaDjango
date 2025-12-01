from django.db import models
from django.utils.text import slugify
from django.utils import timezone
#from catalog.models import Product
#from .models import Order, OrderItem
from django.contrib import admin

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
    
class Order(models.Model):
    payment_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=50)
    merchant_order_id = models.CharField(max_length=100, blank=True, null=True)

    # Totales
    total = models.PositiveIntegerField(default=0)

    # Datos del comprador
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=100, blank=True, null=True)

    # Dirección
    address_line = models.CharField(max_length=255, blank=True, null=True)
    comuna = models.CharField(max_length=100, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Orden #{self.payment_id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.PositiveIntegerField(default=0)  # precio unitario

    def total(self):
        return self.quantity * self.price
    
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("payment_id", "email", "status", "total", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("payment_id", "email")
    inlines = [OrderItemInline]


# ============================
#  Featured Products
# ============================
class FeaturedProduct(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="featured_entries",
        verbose_name="Producto"
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["order", "-updated_at"]
        verbose_name = "Producto destacado"
        verbose_name_plural = "Productos destacados"

    def __str__(self):
        return f"{self.order} — {self.product.name}"


from django.contrib import admin
from .models import FeaturedProduct, Product

@admin.register(FeaturedProduct)
class FeaturedProductAdmin(admin.ModelAdmin):
    list_display = ["product", "order", "is_active", "updated_at"]
    list_display_links = ["product"]   # ← IMPORTANTE
    list_editable = ["order", "is_active"]
    search_fields = ["product__name"]
    list_filter = ["is_active"]
    ordering = ["order"]
