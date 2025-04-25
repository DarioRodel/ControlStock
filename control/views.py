from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from .models import Producto, Categoria, MovimientoStock
from .forms import ProductoForm
from django.views.generic.edit import FormView
from .forms import ReporteErrorForm
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, F
from django.db.models.functions import TruncMonth
from django.views.generic.edit import DeleteView


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'stock/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener todos los productos
        productos = Producto.objects.all()

        # Obtener los últimos 10 movimientos de stock, relacionados con productos y usuarios
        movimientos = MovimientoStock.objects.select_related('producto', 'usuario').order_by('-fecha')[:10]

        # Contar el total de productos y categorías
        total_productos = productos.count()
        total_categorias = Categoria.objects.count()

        # Calcular el valor total del inventario
        valor_total_inventario = productos.aggregate(
            total=Sum(F('precio_compra') * F('stock_actual'))
        )['total'] or 0

        # Obtener los productos con stock bajo
        productos_bajo_stock = Producto.objects.filter(stock_actual__lt=10)

        # Gráfico de stock por categoría
        categorias = Categoria.objects.all()
        categorias_data = []

        for categoria in categorias:
            # Calcular el total de stock por cada categoría
            total_stock = productos.filter(categoria=categoria).aggregate(total=Sum('stock_actual'))['total'] or 0

            # Añadir los datos de la categoría al gráfico de stock
            categorias_data.append({
                'nombre': categoria.nombre,
                'total_stock': total_stock,
                'color': categoria.color or '#4F46E5'  # Usar un color predeterminado si no hay color
            })

        historico = (
            MovimientoStock.objects
            .annotate(mes=TruncMonth('fecha'))
            .values('mes')
            .annotate(
                entradas=Sum('cantidad', filter=Q(tipo='ENTRADA')),
                salidas=Sum('cantidad', filter=Q(tipo='SALIDA'))
            )
            .order_by('mes')[:12]
        )

        # Rellenar meses sin datos
        meses = []
        datos_entradas = []
        datos_salidas = []

        for h in historico:
            meses.append(h['mes'].strftime('%b-%Y'))
            datos_entradas.append(h['entradas'] or 0)
            datos_salidas.append(h['salidas'] or 0)

        historico_data = {
            'labels': meses,
            'entradas': datos_entradas,
            'salidas': datos_salidas
        }

        context.update({
            'total_productos': total_productos,
            'total_categorias': total_categorias,
            'valor_inventario': valor_total_inventario,
            'productos_bajo_stock': productos_bajo_stock,
            'movimientos': movimientos,
            'categorias_data': categorias_data,
            'historico_data': historico_data,
        })

        return context



# Vistas para Productos
class ProductoListView(LoginRequiredMixin, ListView):
    model = Producto
    template_name = 'stock/producto_list.html'
    context_object_name = 'productos'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtros
        search = self.request.GET.get('search')
        categoria = self.request.GET.get('categoria')
        estado = self.request.GET.get('estado')

        if search:
            queryset = queryset.filter(
                Q(codigo__icontains=search) |
                Q(nombre__icontains=search) |
                Q(descripcion__icontains=search)
            )

        if categoria:
            queryset = queryset.filter(categoria__id=categoria)

        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset.select_related('categoria', 'ubicacion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all()
        context['estados'] = Producto.ESTADO_STOCK
        return context


class ProductoDetailView(LoginRequiredMixin, DetailView):
    model = Producto
    template_name = 'stock/producto_detail.html'
    context_object_name = 'producto'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['movimientos'] = self.object.movimientos.all()[:10]
        return context


# stock/views.py

class ProductoCreateView(LoginRequiredMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'stock/producto_create.html'
    success_url = reverse_lazy('stock:producto_list')  # ✅ Agregamos esto

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, 'Producto guardado correctamente.')
        return super().form_valid(form)  # ✅ Usamos el método base, que maneja el redirect automáticamente

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fields'] = ['codigo', 'nombre', 'precio_compra', 'precio_venta']
        return context


class ProductoUpdateView(LoginRequiredMixin, UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'stock/producto_create.html'
    success_url = reverse_lazy('stock:producto_list')

    def form_valid(self, form):
        messages.success(self.request, 'Producto actualizado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fields'] = ['codigo', 'nombre', 'precio_compra', 'precio_venta']
        return context


class MovimientoStockCreateView(LoginRequiredMixin, CreateView):
    model = MovimientoStock
    form_class = MovimientoStock
    template_name = 'stock/movimiento_form.html'

    def form_valid(self, form):
        movimiento = form.save(commit=False)
        movimiento.usuario = self.request.user

        producto = movimiento.producto

        if movimiento.tipo == 'ENTRADA':
            producto.stock_actual += movimiento.cantidad
            if movimiento.ubicacion_destino:
                producto.ubicacion = movimiento.ubicacion_destino

        elif movimiento.tipo == 'SALIDA':
            producto.stock_actual -= movimiento.cantidad

        elif movimiento.tipo == 'TRASPASO':
            producto.ubicacion = movimiento.ubicacion_destino

        producto.save()
        movimiento.save()

        messages.success(
            self.request,
            f"Movimiento registrado exitosamente. Stock actual: {producto.stock_actual}"
        )

        return redirect('producto_detail', pk=producto.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Eliminamos la consulta de los últimos movimientos en esta vista
        return context


class ReporteErrorView(FormView):
    template_name = 'stock/reportar_error.html'
    form_class = ReporteErrorForm
    success_url = reverse_lazy('reportar_error')

    def form_valid(self, form):
        # Aquí podrías guardar o enviar el error
        print("Reporte enviado:")
        print(form.cleaned_data)

        messages.success(self.request, "Gracias por reportar el error. Nuestro equipo lo revisará pronto.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Hay errores en el formulario. Por favor revísalo.")
        return super().form_invalid(form)


class ProductoDeleteView(LoginRequiredMixin, DeleteView):
    model = Producto
    template_name = 'stock/producto_delete.html'  # Plantilla que confirmará la eliminación
    success_url = reverse_lazy('stock:producto_list')  # Redirige a la lista de productos después de eliminar

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Producto eliminado correctamente.')
        return super().delete(request, *args, **kwargs)


class CategoriaDeleteView(LoginRequiredMixin, DeleteView):
    model = Categoria
    template_name = 'stock/categoria_delete.html'  # Plantilla para la confirmación de eliminación
    success_url = reverse_lazy('stock:categoria_list')  # Redirige a la lista de categorías después de eliminar

    def delete(self, request, *args, **kwargs):
        # Añadir mensaje de éxito
        messages.success(self.request, 'Categoría eliminada correctamente.')
        return super().delete(request, *args, **kwargs)


class CategoriaListView(ListView):
    model = Categoria
    template_name = 'stock/categoria_list.html'
    context_object_name = 'categorias'


class CategoriaCreateView(CreateView):
    model = Categoria
    fields = ['nombre', 'color']
    template_name = 'stock/categoria_create.html'
    success_url = reverse_lazy('stock:categoria_list')


class CategoriaUpdateView(LoginRequiredMixin, UpdateView):
    model = Categoria
    fields = ['nombre', 'color']  # Asegúrate de incluir los campos que quieres permitir editar
    template_name = 'stock/categoria_edit.html'
    context_object_name = 'categoria'

    # Después de actualizar, redirigimos al usuario a la lista de categorías
    success_url = reverse_lazy('stock:categoria_list')

    def form_valid(self, form):
        messages.success(self.request, 'Categoría actualizada correctamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Hubo un error al actualizar la categoría.')
        return super().form_invalid(form)
