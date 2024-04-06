from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from .models import Extraccion4,PalabraCompartida
from .serializers import Extraccion4Serializer
from .filters import Extraccion4Filter
from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
import json  # Importar módulo json
from collections import Counter

class Extraccion4List(generics.ListAPIView):
    queryset = Extraccion4.objects.all()
    serializer_class = Extraccion4Serializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = Extraccion4Filter

def admin(request):
    return render(request,'admin.html')

def compartir(request):
    if request.method == 'POST':
        # Asegurarse de que se está leyendo correctamente el cuerpo de la solicitud JSON
        datos_json = json.loads(request.body)
        datos = datos_json.get('frecuencias')

        if datos is not None:
            palabra_compartida = PalabraCompartida.objects.create(datos=datos)
            share_link = request.build_absolute_uri(f'/ver_compartido/{palabra_compartida.id}/')
            return JsonResponse({'success': True, 'shareLink': share_link})
        else:
            return JsonResponse({'success': False, 'error': 'No se proporcionaron datos.'}, status=400)

    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)

def ver_compartido(request, uuid):
    palabra_compartida = get_object_or_404(PalabraCompartida, pk=uuid)
    # Suponiendo que 'datos' es una lista de diccionarios con las claves 'text' y 'size'
    datos_brutos = palabra_compartida.datos
    
    # Contabilizar las frecuencias de las palabras, sin importar mayúsculas o minúsculas
    contador_frecuencias = Counter()
    for item in datos_brutos:
        palabra = item['text'].lower()  # Convertir a minúsculas para consolidar
        frecuencia = item['size']
        contador_frecuencias[palabra] += frecuencia
    
    # Convertir el contador a la lista de tuplas esperada por el template
    datos = contador_frecuencias.most_common()  # Esto ordena por las más frecuentes
    
    # Pasar los datos procesados al contexto del template
    return render(request, 'tu_template.html', {'datos': datos})