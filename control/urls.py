from django.conf.urls.static import static
from django.urls import path

from . import views
from .views import ProductoListView, ReporteErrorView, CategoriaListView, CategoriaCreateView, ProductoDeleteView, \
    CategoriaUpdateView
from django.conf import settings
from django.conf.urls.static import static
app_name = 'stock'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('productos/', ProductoListView.as_view(), name='producto_list'),
    path('productos/nuevo/', views.ProductoCreateView.as_view(), name='producto_create'),
    path('productos/<int:pk>/', views.ProductoDetailView.as_view(), name='producto_detail'),
    path('productos/<int:pk>/editar/', views.ProductoUpdateView.as_view(), name='producto_edit'),
    path('reportar-error/', ReporteErrorView.as_view(), name='reportar_error'),
    path('categorias/nueva/', CategoriaCreateView.as_view(), name='categoria_create'),
    path('productos/<int:pk>/eliminar/', views.ProductoDeleteView.as_view(), name='producto_delete'),
    path('categorias/', views.CategoriaListView.as_view(), name='categoria_list'),
    path('categoria/<int:pk>/eliminar/', views.CategoriaDeleteView.as_view(), name='categoria_delete'),
    path('categoria/<int:pk>/editar/', CategoriaUpdateView.as_view(), name='categoria_edit'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)