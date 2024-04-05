import django_filters
from .models import Extraccion4

class Extraccion4Filter(django_filters.FilterSet):
    class Meta:
        model = Extraccion4
        fields = {
            'cliente': ['exact', 'icontains'],  # Puedes especificar el tipo de comparación
            'estado': ['exact', 'icontains'],
            'municipio': ['exact','icontains'],
            # Añade más campos según necesites
        }
