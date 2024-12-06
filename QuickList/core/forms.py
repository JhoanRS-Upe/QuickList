from django import forms
from .models import Retroalimentacion

class RetroalimentacionForm(forms.ModelForm):
    class Meta:
        model = Retroalimentacion
        fields = ['descripcion', 'calificacion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'class': 'form-control'}),
            'calificacion': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }