from django.urls import path  # Importa la función path para definir patrones de URL.
from . import views  # Importa el módulo de vistas del directorio actual (app 'stock').
from .views import ProductoListView, ReporteErrorView, CategoriaCreateView, \
    CategoriaUpdateView  # Importa vistas específicas desde el módulo .views.
from django.conf import settings  # Importa la configuración de Django.
from django.conf.urls.static import static  # Importa la función static para servir archivos estáticos en desarrollo.

app_name = 'stock'  # Define el namespace de la aplicación para las URLs.

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),  # URL para la vista del dashboard.
    path('productos/', ProductoListView.as_view(), name='producto_list'),  # URL para la lista de productos.
    path('productos/nuevo/', views.ProductoCreateView.as_view(), name='producto_create'),  # URL para crear un nuevo producto.
    path('productos/<int:pk>/', views.ProductoDetailView.as_view(), name='producto_detail'),  # URL para los detalles de un producto específico (identificado por su clave primaria 'pk').
    path('productos/<int:pk>/editar/', views.ProductoUpdateView.as_view(), name='producto_edit'),  # URL para editar un producto existente.
    path('reportar-error/', ReporteErrorView.as_view(), name='reportar_error'),  # URL para la vista de reportar un error.
    path('categorias/nueva/', CategoriaCreateView.as_view(), name='categoria_create'),  # URL para crear una nueva categoría.
    path('productos/<int:pk>/eliminar/', views.ProductoDeleteView.as_view(), name='producto_delete'),  # URL para eliminar un producto.
    path('categorias/', views.CategoriaListView.as_view(), name='categoria_list'),  # URL para la lista de categorías.
    path('categoria/<int:pk>/eliminar/', views.CategoriaDeleteView.as_view(), name='categoria_delete'),  # URL para eliminar una categoría.
    path('categoria/<int:pk>/editar/', CategoriaUpdateView.as_view(), name='categoria_edit'),  # URL para editar una categoría existente.
]

# Solo se sirve contenido multimedia si DEBUG está activado en la configuración.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)