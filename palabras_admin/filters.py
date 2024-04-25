import django_filters
from .models import Extraccion4

class Extraccion4Filter(django_filters.FilterSet):
    class Meta:
        model = Extraccion4
        fields = {
            'cliente': ['exact'],  # Puedes especificar el tipo de comparación
            'estado': ['exact'],
            'municipio': ['exact'],
            # Añade más campos según necesites
        }
