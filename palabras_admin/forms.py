# forms.py
from django import forms
from .models import PalabraCompartida

class PalabraCompartidaForm(forms.ModelForm):
    class Meta:
        model = PalabraCompartida
        fields = ['datos', 'total_grupos']
        widgets = {
            'datos': forms.Textarea(attrs={'cols': 40, 'rows': 5}),
            'total_grupos': forms.NumberInput(attrs={'min': 0}),
        }
        help_texts = {
            'datos': 'Ingrese los datos de la palabra compartida.',
            'total_grupos': 'Ingrese el total de grupos que utilizan esta palabra.',
        }
