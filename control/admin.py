from django.contrib import admin
from django.utils.html import format_html
from .models import Categoria, Ubicacion, Producto, MovimientoStock


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'color_display', 'producto_count')
    search_fields = ('nombre',)

    def color_display(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {};"></div>',
            obj.color
        )

    color_display.short_description = 'Color'

    def producto_count(self, obj):
        return obj.producto_set.count()

    producto_count.short_description = 'Productos'


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'descripcion_corta')
    search_fields = ('nombre', 'codigo')

    def descripcion_corta(self, obj):
        return obj.descripcion[:50] + '...' if obj.descripcion else ''

    descripcion_corta.short_description = 'Descripción'


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'stock_display',
                    'estado_display', 'precio_compra', 'precio_venta', 'activo')
    list_filter = ('categoria', 'estado', 'activo')
    search_fields = ('codigo', 'nombre', 'descripcion')
    readonly_fields = ('qr_preview', 'creado', 'actualizado')
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'codigo_barras', 'nombre', 'descripcion', 'activo')
        }),
        ('Categorización', {
            'fields': ('categoria', 'ubicacion')
        }),
        ('Precios y Stock', {
            'fields': ('precio_compra', 'precio_venta', 'stock_actual', 'stock_minimo', 'estado')
        }),
        ('Imágenes', {
            'fields': ('imagen', 'qr_preview')
        }),
        ('Auditoría', {
            'fields': ('creado', 'actualizado'),
            'classes': ('collapse',)
        }),
    )

    def stock_display(self, obj):
        color = 'green'
        if obj.estado == 'BAJO':
            color = 'orange'
        elif obj.estado == 'AGOTADO':
            color = 'red'
        return format_html(
            '<span style="color: {};">{}</span> / {}',
            color, obj.stock_actual, obj.stock_minimo
        )

    stock_display.short_description = 'Stock (Actual/Mín)'

    def estado_display(self, obj):
        colors = {
            'OK': 'green',
            'BAJO': 'orange',
            'AGOTADO': 'red'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors[obj.estado], obj.get_estado_display()
        )

    estado_display.short_description = 'Estado'

    def qr_preview(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" style="max-height: 100px;" />',
                obj.qr_code.url
            )
        return "No generado"

    qr_preview.short_description = 'Código QR'


@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'producto', 'tipo_display', 'cantidad',
                    'ubicaciones_display', 'usuario')
    list_filter = ('tipo', 'fecha', 'producto__categoria')
    search_fields = ('producto__nombre', 'producto__codigo', 'observaciones')
    date_hierarchy = 'fecha'
    readonly_fields = ('fecha', 'usuario')

    def tipo_display(self, obj):
        colors = {
            'ENTRADA': 'green',
            'SALIDA': 'red',
            'AJUSTE': 'blue',
            'TRASPASO': 'purple'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors[obj.tipo], obj.get_tipo_display()
        )

    tipo_display.short_description = 'Tipo'

    def ubicaciones_display(self, obj):
        if obj.tipo == 'TRASPASO':
            return f"{obj.ubicacion_origen} → {obj.ubicacion_destino}"
        elif obj.tipo == 'ENTRADA':
            return f"→ {obj.ubicacion_destino}"
        elif obj.tipo == 'SALIDA':
            return f"{obj.ubicacion_origen} →"
        return "-"

    ubicaciones_display.short_description = 'Ubicaciones'

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Solo para nuevos movimientos
            obj.usuario = request.user
        super().save_model(request, obj, form, change)