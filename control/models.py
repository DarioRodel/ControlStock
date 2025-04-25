from typing import Any

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import MinValueValidator
import qrcode
from io import BytesIO
from django.core.files import File


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    total_stock = models.IntegerField(default=0)
    color = models.CharField(max_length=7, default='#4e73df')  # Código de color HEX

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Ubicacion(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Ubicación'
        verbose_name_plural = 'Ubicaciones'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class Producto(models.Model):
    ESTADO_STOCK = (
        ('OK', 'Stock Normal'),
        ('BAJO', 'Stock Bajo'),
        ('AGOTADO', 'Stock Agotado'),
    )

    codigo = models.CharField(max_length=50, unique=True, verbose_name='Código')
    codigo_barras = models.CharField(max_length=100, blank=True, null=True)
    nombre = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.TextField(blank=True)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_actual = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    stock_minimo = models.IntegerField(default=5, validators=[MinValueValidator(0)])
    estado = models.CharField(max_length=10, choices=ESTADO_STOCK, default='OK')
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    qr_code = models.ImageField(upload_to='productos_qr/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['nombre']),
            models.Index(fields=['codigo']),
            models.Index(fields=['categoria']),
            models.Index(fields=['estado']),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    def generate_qrcode(self):
        # Asegúrate de que el producto tiene un ID antes de generar el código QR
        if not self.id:
            self.save()  # Guardar para asignar el id, si aún no lo tiene

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(f"PROD:{self.id}:{self.codigo}")
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer)
        filename = f'qr_{self.codigo}.png'
        self.qr_code.save(filename, File(buffer), save=False)

    def save(self, *args, **kwargs):
        # Primero guarda el objeto para que se le asigne un id
        super().save(*args, **kwargs)

        # Ahora que el producto tiene un id, generamos el código QR si no existe
        if not self.qr_code:
            self.generate_qrcode()
            # Guardamos de nuevo el objeto solo si el código QR fue generado
            super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('detalle_producto', kwargs={'pk': self.pk})

    @property
    def valor_inventario(self):
        return self.stock_actual * self.precio_compra


class MovimientoStock(models.Model):
    TIPO_MOVIMIENTO = (
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
        ('AJUSTE', 'Ajuste'),
        ('TRASPASO', 'Traspaso'),
    )

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])
    ubicacion_origen = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='movimientos_salida')
    ubicacion_destino = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='movimientos_entrada')
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    observaciones = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimiento de Stock'
        verbose_name_plural = 'Movimientos de Stock'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} de {self.cantidad} {self.producto} - {self.fecha}"

    def save(self, *args, **kwargs):
        # Actualizar stock del producto
        if not self.pk:  # Solo para nuevos movimientos
            if self.tipo == 'ENTRADA':
                self.producto.stock_actual += self.cantidad
            elif self.tipo == 'SALIDA':
                self.producto.stock_actual -= self.cantidad
            self.producto.save()

        super().save(*args, **kwargs)
