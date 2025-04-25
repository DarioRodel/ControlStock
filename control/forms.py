from django import forms
from .models import MovimientoStock, Producto, Ubicacion


class MovimientoStockForm(forms.ModelForm):
    class Meta:
        model = MovimientoStock
        fields = ['producto', 'tipo', 'cantidad', 'ubicacion_origen', 'ubicacion_destino', 'observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtramos productos activos
        self.fields['producto'].queryset = Producto.objects.filter(activo=True)

        # Filtramos ubicaciones activas
        self.fields['ubicacion_origen'].queryset = Ubicacion.objects.all()
        self.fields['ubicacion_destino'].queryset = Ubicacion.objects.all()

        # Campos requeridos condicionales
        self.fields['ubicacion_origen'].required = False
        self.fields['ubicacion_destino'].required = False

        # Añadir clases CSS a los campos
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        cantidad = cleaned_data.get('cantidad')
        producto = cleaned_data.get('producto')
        ubicacion_origen = cleaned_data.get('ubicacion_origen')
        ubicacion_destino = cleaned_data.get('ubicacion_destino')

        # Validación para SALIDA
        if tipo == 'SALIDA':
            if producto.stock_actual < cantidad:
                raise forms.ValidationError(
                    f"No hay suficiente stock. Stock actual: {producto.stock_actual}"
                )
            if not ubicacion_origen:
                raise forms.ValidationError("Debe seleccionar una ubicación de origen para las salidas")

        # Validación para TRASPASO
        if tipo == 'TRASPASO':
            if not ubicacion_origen or not ubicacion_destino:
                raise forms.ValidationError("Debe seleccionar ambas ubicaciones para traspasos")
            if ubicacion_origen == ubicacion_destino:
                raise forms.ValidationError("Las ubicaciones de origen y destino deben ser diferentes")

        return cleaned_data



class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        exclude = ['estado']  # Excluir el campo estado del formulario
        error_messages = {
            'codigo': {'required': 'Este campo es obligatorio.'},
            'nombre': {'required': 'Este campo es obligatorio.'},
            'precio_compra': {'required': 'Este campo es obligatorio.'},
            'precio_venta': {'required': 'Este campo es obligatorio.'},
        }
class ReporteErrorForm(forms.Form):
    asunto = forms.CharField(label="Asunto", max_length=100, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Título breve del error',
    }))
    descripcion = forms.CharField(label="Descripción", widget=forms.Textarea(attrs={
        'class': 'form-control',
        'placeholder': 'Describe el error lo más detalladamente posible...',
        'rows': 5
    }))
    email = forms.EmailField(label="Correo electrónico", required=False, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'tu@correo.com'
    }))