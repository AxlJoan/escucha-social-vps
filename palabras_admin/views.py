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
from asgiref.sync import sync_to_async
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache

@sync_to_async
def filter_extraccion4(cliente=None, estado=None, municipio=None):
    cache_key = f"extraccion4-{cliente}-{estado}-{municipio}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data

    q_objects = Q()
    if cliente:
        q_objects &= Q(cliente__icontains=cliente)
    if estado:
        q_objects &= Q(estado__icontains=estado)
    if municipio:
        q_objects &= Q(municipio__icontains=municipio)

    data = list(Extraccion4.objects.filter(q_objects).values('text_data', 'cliente', 'estado', 'municipio', 'group_name'))
    cache.set(cache_key, data, timeout=60*15)  # Cache for 15 minutes
    return data

# Aplicando el cache_page directamente a la función vista
@cache_page(60 * 15)
async def extraccion4_list(request):
    cliente = request.GET.get('cliente', '')
    estado = request.GET.get('estado', '')
    municipio = request.GET.get('municipio', '')

    data = await filter_extraccion4(cliente, estado, municipio)
    return JsonResponse(data, safe=False)

def admin(request):
    return render(request,'tu_template.html')

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
        try:
            frecuencia = int(item.get('size', 0))
        except (ValueError, TypeError) as e:
            # Log the problematic value for debugging
            print(f"Skipping invalid size value: {item.get('size')} - Error: {e}")
            frecuencia = 0  # Default to 0 if conversion fails

        if palabra and frecuencia:  # This ensures only valid data is processed
            contador_frecuencias[palabra] += frecuencia

    datos = contador_frecuencias.most_common()
    return render(request, 'tu_template.html', {'datos': datos, 'totalGrupos': total_grupos})

# Antes era template_name = 'analisis.html'
class Vista_Analisis(ListView):
    model = Extraccion4
    template_name = 'tu_template.html'
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
            return redirect('dashboard')  # Redirecciona a donde quieras después del login
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
                area_codes = AreaCodeMX.objects.all().values_list('code', flat=True)
                for length in (2, 3):
                    area_code = normalized_number[index:index + length]
                    if area_code in area_codes:
                        area = AreaCodeMX.objects.get(code=area_code)
                        state_count = Extraccion4.objects.filter(
                            number__startswith=country.code.replace('+', '') + area_code
                        ).count()
                        print(f"Area code: {area_code}, State count: {state_count}")  # Depuración
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
    countries = CountryCode.objects.all()
    entries = Extraccion4.objects.all()

    for country in countries:
        # Filtrar entradas por código de país
        country_code = country.code.replace('+', '')
        country_entries = entries.filter(number__startswith=country_code)
        country_count = country_entries.count()
        country_counts[country.pais] = country_count

        if country.code == '+52':  # Procesamiento especial para México
            # Considerar el prefijo de troncal '1' si está presente
            entries_with_trunk = country_entries.filter(number__startswith=country_code + '1')
            entries_without_trunk = country_entries.exclude(number__startswith=country_code + '1')

            # Procesar códigos de área con y sin el prefijo de troncal
            for area in AreaCodeMX.objects.all():
                state_count_with_trunk = entries_with_trunk.filter(
                    number__startswith=country_code + '1' + area.code
                ).count()

                state_count_without_trunk = entries_without_trunk.filter(
                    number__startswith=country_code + area.code
                ).count()

                total_state_count = state_count_with_trunk + state_count_without_trunk
                state_counts[area.estado] = state_counts.get(area.estado, 0) + total_state_count

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

# ----------------------------- A partir de aquí inicia mi código ------------------------
from django.shortcuts import render
from django.http import HttpResponseForbidden
import mysql.connector
from .utils import (
    obtener_datos_cliente,
    obtener_grupos,
    generar_top_palabras,
    generar_nube_palabras,
    obtener_mensajes_totales,
    obtener_numeros_totales,
    obtener_grupos_extraidos,
    generar_grafo,
    generar_analisis_sentimientos
)
from django.core.paginator import Paginator

"""
Nombre de la función: dashboard_view
Descripción: Vista que maneja el dashboard de la aplicación, extrayendo los filtros desde la solicitud del usuario, 
             obteniendo los datos correspondientes, generando métricas como el top de palabras, nube de palabras, 
             grafos y análisis de sentimientos, además de manejar la paginación de los resultados.
Entradas:
            - request (HttpRequest): Objeto que contiene los datos de la solicitud, como parámetros GET y el usuario autenticado.
Salidas:
            - HttpResponse: Retorna una respuesta renderizada con el contexto que incluye las métricas y resultados generados.
"""
def dashboard_view(request):
    # Extraer filtros
    if request.user.is_authenticated:
        # Verificar si el usuario es admin, si es así forzar 'QuintanaRoo' si no hay 'cliente' en GET
        if request.user.is_staff:
            nombre_cliente = request.GET.get('cliente', 'maralezama')  # Si no pasa 'cliente', se toma 'Test'
        else:
            nombre_cliente = request.GET.get('cliente', request.user.username)
    else:
        nombre_cliente = 'QuintanaRoo'
    
    estado = request.GET.get('estado', '')
    municipio = request.GET.get('municipio', '')
    group_name = request.GET.get('group_name', '')
    number2 = request.GET.get('number2', '')
    text_data = request.GET.get('text_data', '')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    
    # Obtener datos utilizando las funciones auxiliares
    top_palabras = generar_top_palabras(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin)
    imagen_nube = generar_nube_palabras(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin)
    
    df = obtener_datos_cliente(nombre_cliente, estado, municipio, group_name, number2, text_data, fecha_inicio, fecha_fin)
    if df is not None:
        datos_lista = df.to_dict(orient='records')
    else:
        datos_lista = []

    # Paginación
    paginador = Paginator(datos_lista, 50)  # 50 registros por página
    page_number = request.GET.get('page')  # Obtener el número de página desde la URL
    datos_paginados = paginador.get_page(page_number)  # Obtener la página actual

    # Obtener grupos
    grupos = obtener_grupos(nombre_cliente)

    # Generar grafo
    grafo_html = generar_grafo(nombre_cliente, group_name, number2, fecha_inicio, fecha_fin)

    # Nuevas métricas
    mensajes_totales = obtener_mensajes_totales(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin)
    numeros_totales = obtener_numeros_totales(nombre_cliente)
    grupos_extraidos = obtener_grupos_extraidos(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin)
    analisis_sentimientos = generar_analisis_sentimientos(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin)

    if analisis_sentimientos:
        key = max(analisis_sentimientos, key=analisis_sentimientos.get)
        sentimiento_predominante = key
    else:
        sentimiento_predominante = "Sin datos"

    context = {
        'nombre_cliente': nombre_cliente,
        'estado': estado,
        'municipio': municipio,
        'group_name': group_name,
        'number2': number2,
        'text_data': text_data,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'top_palabras': top_palabras,
        'imagen_nube': imagen_nube,
        'datos_tabla': datos_paginados,  # Aquí va la lista paginada
        'grupos': grupos,
        'mensajes_totales': mensajes_totales,
        'numeros_totales': numeros_totales,
        'grupos_extraidos': grupos_extraidos,
        'grafo_html': grafo_html,
        'analisis_sentimientos': analisis_sentimientos,
        'sentimiento_predominante': sentimiento_predominante,
    }
    return render(request, 'tu_template.html', context)
#-------------------------------------------------------------------------#
"""
Nombre de la función: insertar_mensajes_view
Descripción: Vista que permite a los administradores insertar mensajes en la base de datos, validando que el usuario tenga permisos de administrador. 
             Los mensajes se insertan en la tabla 'extraccion4' con los datos proporcionados en la solicitud.
Entradas:
            - request (HttpRequest): Objeto que contiene los datos de la solicitud, incluyendo los mensajes a insertar.
Salidas:
            - HttpResponse: Retorna una respuesta renderizada con el mensaje de éxito o error.
"""
def insertar_mensajes_view(request):
    # Solo administradores pueden insertar mensajes
    if not request.user.is_staff:
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")
    
    mensaje = ""
    if request.method == 'POST':
        text_data = request.POST.get('text_data')
        cantidad = int(request.POST.get('cantidad', 0))
        cliente = request.POST.get('cliente')
        number2 = request.POST.get('number2')
        estado = request.POST.get('estado')
        municipio = request.POST.get('municipio')
        group_name = request.POST.get('group_name')
        
        if text_data and cantidad > 0 and cliente:
            conn = mysql.connector.connect(
                host='158.69.26.160',
                user='admin',
                password='S3gur1d4d2025',
                database='data_wa'
            )
            cursor = conn.cursor()
            sql = "INSERT INTO extraccion4 (text_data, cliente, number2, estado, municipio, group_name) VALUES (%s, %s, %s, %s, %s, %s)"
            data = [(text_data, cliente, number2, estado, municipio, group_name)] * cantidad
            
            try:
                cursor.executemany(sql, data)
                conn.commit()
                mensaje = f"Se han insertado {cantidad} mensajes para el cliente '{cliente}'."
            except Exception as e:
                mensaje = f"Ocurrió un error: {str(e)}"
            finally:
                cursor.close()
                conn.close()
    
    return render(request, 'tu_template.html', {'mensaje': mensaje})
#-------------------------------------------------------------------------#
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .utils import generar_grafo  # Mantenemos la función original

"""
Nombre de la función: grafo_completo_view
Descripción: Vista que genera y muestra un grafo completo basado en los filtros proporcionados en la solicitud del usuario, 
             personalizando la visualización del grafo con CSS responsivo.
Entradas:
            - request (HttpRequest): Objeto que contiene los datos de la solicitud, como los filtros para generar el grafo.
Salidas:
            - HttpResponse: Retorna una respuesta renderizada con el HTML del grafo generado y el CSS aplicado.
"""
@login_required
def grafo_completo_view(request):
    # Obtener filtros según sea necesario:
    nombre_cliente = request.GET.get('cliente') if request.user.is_staff else request.user.username
    group_name = request.GET.get('group_name')
    number2 = request.GET.get('number2')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # Llamamos a la función que genera el grafo.
    grafo_html = generar_grafo(nombre_cliente, group_name, number2, fecha_inicio, fecha_fin)
    
    if grafo_html:
        # Inyectamos CSS que fuerza la altura, el fondo oscuro y que los textos sean blancos
        responsive_css = """
        <style>
            /* Fijamos la altura y el background */
            #mynetwork {
                height: 850px !important;
                background-color: #fff !important;
            }
            /* Para móviles */
            @media only screen and (max-width: 768px) {
                #mynetwork {
                    height: 400px !important;
                }
            }
            /* Forzamos que todos los elementos dentro de #mynetwork muestren texto blanco.
               Además, para elementos SVG usamos fill para que los textos en SVG sean blancos. */
            #mynetwork, 
            #mynetwork * {
                color: #fff !important;
                fill: #fff !important;
            }
        </style>
        """
        # Inyectamos el bloque de estilos antes de </head>
        grafo_html = grafo_html.replace("</head>", responsive_css + "</head>")
    
    context = {'grafo_html': grafo_html}
    return render(request, 'grafo_completo.html', context)
#-------------------------------------------------------------------------#
import json
import os
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings

# Ruta al archivo donde se almacenarán las palabras monitoreadas
def get_palabras_file_path(usuario):
    return os.path.join(settings.MEDIA_ROOT, f"{usuario.username}_palabras.json")

# Función para cargar las palabras monitoreadas desde el archivo JSON
def cargar_palabras_monitoreo(usuario):
    file_path = get_palabras_file_path(usuario)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return []

# Función para guardar las palabras monitoreadas en el archivo JSON
def guardar_palabras_monitoreo(usuario, palabras_monitoreo):
    file_path = get_palabras_file_path(usuario)
    with open(file_path, 'w') as f:
        json.dump(palabras_monitoreo, f)

import pandas as pd
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from .utils import cargar_datos_csv  # Función que carga el CSV

@login_required
def monitoreo_view(request):
    usuario = request.user

    # 1. Obtener el nombre del cliente asociado al usuario
    if request.user.is_authenticated:
        if request.user.is_staff:
            nombre_cliente = request.GET.get('cliente', 'maralezama')  # Admin puede seleccionar cliente
        else:
            nombre_cliente = request.GET.get('cliente', request.user.username)  # Usuario normal solo ve su cliente
    else:
        nombre_cliente = 'QuintanaRoo'  # En caso de usuario no autenticado

    # 2. Cargar las palabras monitoreadas
    monitored_words = cargar_palabras_monitoreo(usuario)

    # 3. Procesar el formulario para añadir una nueva palabra
    if request.method == "POST":
        palabra = request.POST.get('palabra')
        if palabra:
            if palabra in monitored_words:
                messages.error(request, f"La palabra '{palabra}' ya está siendo monitoreada.")
            elif len(monitored_words) >= 10:
                messages.error(request, "Solo puedes monitorear hasta 10 palabras.")
            else:
                monitored_words.append(palabra)
                guardar_palabras_monitoreo(usuario, monitored_words)
                messages.success(request, f"Palabra '{palabra}' añadida a monitoreo.")
            return redirect('monitoreo')

    # 4. Cargar datos desde el CSV y filtrar por cliente
    df = cargar_datos_csv()
    df = df[df["cliente"] == nombre_cliente]

    # 5. Aplicar filtros adicionales antes de segmentar por palabras
    text_data = request.GET.get('text_data', '')
    group_name = request.GET.get('group_name', '')
    number2 = request.GET.get('number2', '')
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')

    if text_data:
        df = df[df["text_data"].fillna('').str.lower().str.contains(text_data.lower(), na=False)]
    if group_name:
        df = df[df["group_name"].fillna('').str.lower().str.contains(group_name.lower(), na=False)]
    if number2:
        df = df[df["number2"].fillna('').str.lower().str.contains(number2.lower(), na=False)]
    if fecha_inicio:
        df = df[df["timestamp"] >= pd.to_datetime(fecha_inicio)]
    if fecha_fin:
        df = df[df["timestamp"] <= pd.to_datetime(fecha_fin)]

    # 6. Métricas generales (antes de segmentar por palabras)
    total_mensajes = len(df)  # Total de mensajes filtrados antes de aplicar palabras monitoreadas
    total_palabras_global = 0  # Suma total de ocurrencias de todas las palabras monitoreadas

    # 7. Obtener palabra seleccionada (si se ha hecho clic en una palabra específica)
    palabra_seleccionada = request.GET.get('palabra_seleccionada', '')

    # 8. Filtrar datos por cada palabra monitoreada (y aplicar filtros adicionales)
    tablas_palabras = {}
    total_palabras = {}

    for palabra in monitored_words:
        df_filtrado = df[df["text_data"].fillna('').str.contains(palabra, case=False, na=False)]
        if not df_filtrado.empty:
            tablas_palabras[palabra] = df_filtrado.to_dict(orient='records')
            total_palabras[palabra] = df_filtrado["text_data"].fillna('').str.lower().str.count(palabra.lower()).sum()
            total_palabras_global += total_palabras[palabra]  # Sumar al total general

    # 9. Si el usuario seleccionó una palabra específica, solo mostramos esa tabla
    if palabra_seleccionada and palabra_seleccionada in tablas_palabras:
        tablas_palabras = {palabra_seleccionada: tablas_palabras[palabra_seleccionada]}

    # 10. Paginación para cada tabla (50 registros por página)
    datos_paginados = {}
    for palabra, datos in tablas_palabras.items():
        paginador = Paginator(datos, 50)
        page_number = request.GET.get('page')
        datos_paginados[palabra] = paginador.get_page(page_number)

    # 11. Contexto para la plantilla
    context = {
        'monitored_words': monitored_words,  
        'total_mensajes': total_mensajes,       # Mantengo tu métrica original
        'total_palabras': total_palabras_global,  # Suma total de todas las palabras monitoreadas
        'tablas_palabras': datos_paginados,    # Cada palabra tiene su propia tabla paginada
        'palabra_seleccionada': palabra_seleccionada,  
        'text_data': text_data,  
        'group_name': group_name,
        'number2': number2,       
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin
    }

    return render(request, 'monitoreo.html', context)


@login_required
def eliminar_palabra(request, palabra):
    usuario = request.user

    # Cargar las palabras monitoreadas del archivo
    palabras_monitoreo = cargar_palabras_monitoreo(usuario)

    if palabra in palabras_monitoreo:
        palabras_monitoreo.remove(palabra)
        guardar_palabras_monitoreo(usuario, palabras_monitoreo)
        messages.success(request, f"Palabra '{palabra}' eliminada del monitoreo.")
    else:
        messages.error(request, f"La palabra '{palabra}' no está siendo monitoreada.")

    return redirect('monitoreo')
