from typing import Any  # Importa Any para tipado genérico.

from django.db import models  # Importa el módulo de modelos de Django.
from django.contrib.auth.models import User  # Importa el modelo User para la autenticación de usuarios.
from django.urls import reverse  # Importa la función reverse para generar URLs a partir de nombres de vistas.
from django.core.validators import MinValueValidator  # Importa el validador para asegurar valores mínimos.
import qrcode  # Importa la librería qrcode para generar códigos QR.
from io import BytesIO  # Importa BytesIO para manejar datos binarios en memoria.
from django.core.files import File  # Importa File para manejar archivos en Django.


class Categoria(models.Model):
    """
    Modelo que representa una categoría de productos.
    """
    nombre = models.CharField(max_length=100, unique=True)  # Nombre de la categoría, único.
    descripcion = models.TextField(blank=True)  # Descripción opcional de la categoría.
    total_stock = models.IntegerField(default=0)  # Stock total de productos en esta categoría.
    color = models.CharField(max_length=7, default='#4e73df')  # Color HEX para representar la categoría.

    class Meta:
        verbose_name = 'Categoría'  # Nombre singular para la interfaz de administración.
        verbose_name_plural = 'Categorías'  # Nombre plural para la interfaz de administración.
        ordering = ['nombre']  # Ordena las categorías alfabéticamente por nombre.

    def __str__(self):
        return self.nombre  # Representación en string de la categoría (su nombre).


class Ubicacion(models.Model):
    """
    Modelo que representa una ubicación física para los productos.
    """
    nombre = models.CharField(max_length=100)  # Nombre de la ubicación.
    codigo = models.CharField(max_length=10, unique=True)  # Código único de la ubicación.
    descripcion = models.TextField(blank=True)  # Descripción opcional de la ubicación.

    class Meta:
        verbose_name = 'Ubicación'  # Nombre singular para la interfaz de administración.
        verbose_name_plural = 'Ubicaciones'  # Nombre plural para la interfaz de administración.
        ordering = ['nombre']  # Ordena las ubicaciones alfabéticamente por nombre.

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"  # Representación en string de la ubicación.


class Producto(models.Model):
    """
    Modelo que representa un producto en el sistema.
    """
    ESTADO_STOCK = (  # Opciones para el estado del stock.
        ('OK', 'Stock Normal'),
        ('BAJO', 'Stock Bajo'),
        ('AGOTADO', 'Stock Agotado'),
    )

    codigo_barras = models.CharField(max_length=100, unique=True, verbose_name='Código de Barras') # Permite almacenar el código de barras
    nombre = models.CharField(max_length=200)  # Nombre del producto.
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)  # Categoría del producto.
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL, null=True, blank=True)  # Ubicación del producto
    descripcion = models.TextField(blank=True)  # Descripción opcional del producto.
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Precio de compra del producto.
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Precio de venta del producto.
    stock_actual = models.IntegerField(default=0, validators=[MinValueValidator(0)])  # Stock actual del producto.
    stock_minimo = models.IntegerField(default=5, validators=[MinValueValidator(0)])  # Stock mínimo del producto.
    estado = models.CharField(max_length=10, choices=ESTADO_STOCK, default='OK')  # Estado del stock del producto.
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)  # Imagen del producto.
    qr_code = models.ImageField(upload_to='productos_qr/', blank=True, null=True)  # Campo para almacenar la imagen del código QR.
    activo = models.BooleanField(default=True)  # Indica si el producto está activo.
    creado = models.DateTimeField(auto_now_add=True)  # Fecha de creación del producto.
    actualizado = models.DateTimeField(auto_now=True)  # Fecha de última actualización del producto.

    class Meta:
        ordering = ['nombre']  # Ordena los productos alfabéticamente por nombre.
        indexes = [  # Define índices para mejorar el rendimiento de las consultas.
            models.Index(fields=['nombre']),
            models.Index(fields=['codigo_barras']),
            models.Index(fields=['categoria']),
            models.Index(fields=['estado']),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.codigo_barras})"  # Representación en string del producto.

    def generate_qrcode(self):
        """
        Genera un código QR para el producto y lo guarda en el campo qr_code.
        """
        # Asegúrate de que el producto tiene un ID antes de generar el código QR
        if not self.id:
            self.save()  # Guardar para asignar el id, si aún no lo tiene

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # Nivel de corrección de errores.
            box_size=10,  # Tamaño de cada "celda" del código QR.
            border=4,  # Ancho del borde alrededor del código QR.
        )
        qr.add_data(f"PROD:{self.id}:{self.codigo_barras}")  # Codifica la información del producto en el código QR.
        qr.make(fit=True)  # Ajusta el tamaño del código QR a la información.

        img = qr.make_image(fill_color="black", back_color="white")  # Crea la imagen del código QR.

        buffer = BytesIO()  # Crea un buffer en memoria para guardar la imagen.
        img.save(buffer)  # Guarda la imagen en el buffer.
        filename = f'qr_{self.codigo_barras}.png'  # Genera un nombre de archivo para el código QR.
        self.qr_code.save(filename, File(buffer), save=False)  # Guarda la imagen en el campo qr_code del modelo.

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para generar el código QR antes de guardar el producto.
        """
        if not self.codigo_barras:
            self.codigo_barras = self.codigo
        # Primero guarda el objeto para que se le asigne un id
        super().save(*args, **kwargs)

        # Ahora que el producto tiene un id, generamos el código QR si no existe
        if not self.qr_code:
            self.generate_qrcode()
            # Guardamos de nuevo el objeto solo si el código QR fue generado
            super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Genera la URL para la vista de detalle del producto.
        """
        return reverse('detalle_producto', kwargs={'pk': self.pk})  # Utiliza la función reverse para obtener la URL.

    @property
    def valor_inventario(self):
        """
        Calcula el valor total del inventario para este producto.
        """
        return self.stock_actual * self.precio_compra  # Multiplica el stock actual por el precio de compra.



class MovimientoStock(models.Model):
    """
    Modelo que representa un movimiento de stock de un producto.
    """
    TIPO_MOVIMIENTO = (  # Opciones para el tipo de movimiento.
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
        ('AJUSTE', 'Ajuste'),
        ('TRASPASO', 'Traspaso'),
    )

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')  # Producto afectado por el movimiento.
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)  # Tipo de movimiento.
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])  # Cantidad del movimiento.
    ubicacion_origen = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='movimientos_salida')  # Ubicación de origen (para salidas y traspasos).
    ubicacion_destino = models.ForeignKey(Ubicacion, on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='movimientos_entrada')  # Ubicación de destino (para entradas y traspasos).
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  # Usuario que realizó el movimiento.
    observaciones = models.TextField(blank=True)  # Observaciones sobre el movimiento.
    fecha = models.DateTimeField(auto_now_add=True)  # Fecha y hora del movimiento.

    class Meta:
        verbose_name = 'Movimiento de Stock'  # Nombre singular para la interfaz de administración.
        verbose_name_plural = 'Movimientos de Stock'  # Nombre plural para la interfaz de administración.
        ordering = ['-fecha']  # Ordena los movimientos por fecha descendente (más reciente primero).

    def __str__(self):
        return f"{self.get_tipo_display()} de {self.cantidad} {self.producto} - {self.fecha}"  # Representación en string.

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para actualizar el stock del producto al realizar el movimiento.
        """
        # Actualizar stock del producto
        if not self.pk:  # Solo para nuevos movimientos
            if self.tipo == 'ENTRADA':
                self.producto.stock_actual += self.cantidad  # Aumenta el stock para entradas.
            elif self.tipo == 'SALIDA':
                self.producto.stock_actual -= self.cantidad  # Disminuye el stock para salidas.
            self.producto.save()  # Guarda el producto con el stock actualizado.

        super().save(*args, **kwargs)  # Llama al método save de la clase padre para guardar el movimiento.