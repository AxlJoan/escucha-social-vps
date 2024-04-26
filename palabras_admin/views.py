from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from .models import Extraccion4,PalabraCompartida,CountryCode,AreaCodeMX
from .serializers import Extraccion4Serializer
from .filters import Extraccion4Filter
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
import json  # Importar módulo json
from collections import Counter
from django.views.generic import ListView
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.views import View
from django.views.generic import ListView, UpdateView
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt

class Extraccion4List(generics.ListAPIView):
    queryset = Extraccion4.objects.all()
    serializer_class = Extraccion4Serializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = Extraccion4Filter

def admin(request):
    return render(request,'admin.html')

@csrf_exempt  # Asegúrate de manejar CSRF apropiadamente en producción
def compartir(request):
    if request.method == 'POST':
        try:
            datos_json = json.loads(request.body)
            datos = datos_json.get('frecuencias')
            total_grupos = datos_json.get('totalGrupos')
            nombre = datos_json.get('nombre')
            id_palabra_compartida = datos_json.get('id', None)

            if datos:
                if id_palabra_compartida:
                    # Actualizar un enlace existente
                    palabra_compartida = PalabraCompartida.objects.get(id=id_palabra_compartida)
                else:
                    # Crear un nuevo enlace
                    palabra_compartida = PalabraCompartida()

                palabra_compartida.datos = datos
                palabra_compartida.total_grupos = total_grupos
                palabra_compartida.name = nombre
                palabra_compartida.save()
                
                share_link = request.build_absolute_uri(f'/palabras_admin/ver_compartido/{palabra_compartida.id}/')
                return JsonResponse({'success': True, 'shareLink': share_link})
            else:
                return JsonResponse({'success': False, 'error': 'No se proporcionaron datos suficientes.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)

def obtener_enlaces(request):
    if request.method == 'GET':
        enlaces = PalabraCompartida.objects.all()
        datos = [{'id': str(enlace.id), 'nombre': enlace.name} for enlace in enlaces]  # Convert UUID to string
        return JsonResponse(datos, safe=False)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def ver_compartido(request, uuid):
    palabra_compartida = get_object_or_404(PalabraCompartida, pk=uuid)
    datos_brutos = palabra_compartida.datos
    
    total_grupos = palabra_compartida.total_grupos  # Retrieve total groups
    
    contador_frecuencias = Counter()
    for item in datos_brutos:
        palabra = item.get('text', '').lower()
        frecuencia = item.get('size', 0)
        if palabra and frecuencia:  # This ensures only valid data is processed
            contador_frecuencias[palabra] += frecuencia

    datos = contador_frecuencias.most_common()
    return render(request, 'tu_template.html', {'datos': datos, 'totalGrupos': total_grupos})

class Vista_Analisis(ListView):
    model = Extraccion4
    template_name = 'analisis.html'
    context_object_name = 'extracciones'
    paginate_by = 100  # Ajusta este número según lo que sea manejable para tu página

    def get_queryset(self):
        queryset = super().get_queryset()
        self.filterset = Extraccion4Filter(self.request.GET, queryset=queryset)
        return self.filterset.qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.filterset.qs.distinct()  # Asegúrate de que el queryset esté filtrado

        # Paginación
        page = self.request.GET.get('page')
        paginator = Paginator(queryset, self.paginate_by)

        try:
            extracciones = paginator.page(page)
        except PageNotAnInteger:
            extracciones = paginator.page(1)
        except EmptyPage:
            extracciones = paginator.page(paginator.num_pages)

        # Calcula el total de grupos únicos basado en el queryset filtrado
        if self.request.GET:
            group_names = queryset.values_list('group_name', flat=True).distinct()
            total_unique_groups = len(set(group_names))
        else:
            total_unique_groups = None

        # Agregar la paginación y el filtro al contexto
        context['extracciones'] = extracciones
        context['total_unique_groups'] = total_unique_groups
        context['filterset'] = self.filterset
        return context
    

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('nube_admin')  # Redirecciona a donde quieras después del login
    return render(request, 'login.html')  # Asegúrate de tener esta plantilla


class ClassifyNumberView(View):
    def get(self, request, id):
        try:
            entry = Extraccion4.objects.get(id=id)
            normalized_number = ''.join(filter(str.isdigit, entry.number))
            print(f"Normalized number: {normalized_number}")  # Depuración

            # Detectar código de país y determinar longitud del país
            country_code = '+52' if normalized_number.startswith('52') else '+' + normalized_number[:2]
            country = CountryCode.objects.filter(code=country_code).first()
            print(f"Country code: {country_code}")  # Depuración

            if country:
                country_count = Extraccion4.objects.filter(number__startswith=country.code.replace('+', '')).count()
                index = normalized_number.find(country.code.replace('+', '')) + len(country.code.replace('+', ''))
                if normalized_number[index] == '1':
                    index += 1  # Omitir el prefijo de troncal si existe

                # Suponiendo códigos de área de 2 o 3 dígitos
                for length in (2, 3):
                    area_code = normalized_number[index:index + length]
                    area = AreaCodeMX.objects.filter(code=area_code).first()
                    if area:
                        state_count = Extraccion4.objects.filter(number__startswith=country.code.replace('+', '') + area_code).count()
                        print(f"Area code: {area_code}, State count: {state_count}")  # Depuración
                        if state_count:
                            break

            response_data = {
                'country_code': country_code,
                'country': country.pais if country else 'Unknown',
                'country_count': country_count,
                'area_code': area_code if 'area_code' in locals() else 'Unknown',
                'estado': area.estado if area else 'Unknown',
                'state_count': state_count if 'state_count' in locals() else 0
            }
            return JsonResponse(response_data)
        except Extraccion4.DoesNotExist:
            return JsonResponse({'error': 'Entry not found'}, status=404)

def statistics_view(request):
    # Diccionarios para mantener los conteos por país y estado
    country_counts = {}
    state_counts = {}

    # Procesar por cada país definido en CountryCode
    for country in CountryCode.objects.all():
        # Filtrar entradas por código de país
        entries = Extraccion4.objects.filter(number__startswith=country.code.replace('+', ''))
        country_count = entries.count()
        country_counts[country.pais] = country_count

        if country.code == '+52':  # Procesamiento especial para México
            # Considerar el prefijo de troncal '1' si está presente
            entries_with_trunk = entries.filter(number__startswith=country.code.replace('+', '') + '1')
            entries_without_trunk = entries.exclude(number__startswith=country.code.replace('+', '') + '1')

            # Procesar códigos de área con y sin el prefijo de troncal
            for area in AreaCodeMX.objects.all():
                # Contar estados con prefijo de troncal
                state_count_with_trunk = entries_with_trunk.filter(
                    number__startswith=country.code.replace('+', '') + '1' + area.code
                ).count()

                # Contar estados sin prefijo de troncal
                state_count_without_trunk = entries_without_trunk.filter(
                    number__startswith=country.code.replace('+', '') + area.code
                ).count()

                total_state_count = state_count_with_trunk + state_count_without_trunk
                if area.estado not in state_counts:
                    state_counts[area.estado] = total_state_count
                else:
                    state_counts[area.estado] += total_state_count

    # Debugging outputs
    print(country_counts)
    print(state_counts)

    return render(request, 'statistics.html', {
        'country_counts': country_counts, 
        'state_counts': state_counts
    })

class PalabraCompartidaListView(ListView):
    model = PalabraCompartida
    context_object_name = 'palabras'
    template_name = 'list.html'

class PalabraCompartidaUpdateView(UpdateView):
    model = PalabraCompartida
    fields = ['datos', 'total_grupos']
    template_name = 'edit.html'
    success_url = reverse_lazy('palabra-list')