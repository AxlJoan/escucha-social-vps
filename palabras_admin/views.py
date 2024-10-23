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
import mysql.connector
from mysql.connector import pooling

# Configuración del pool de conexiones
dbconfig = {
    "host": "158.69.26.160",
    "user": "admin",
    "password": "F@c3b00k",
    "database": "data_wa"
}

# Crear el pool de conexiones
connection_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=10,  # Ajusta según la carga esperada
    **dbconfig
)


# Conectar a la base de datos
import mysql.connector
import pandas as pd
from django.shortcuts import render

def obtener_datos_cliente(nombre_cliente=None, estado=None, municipio=None, group_name=None, number2=None):
    conn = connection_pool.get_connection()
    cursor = conn.cursor()

    # Construir el query base
    query = "SELECT cliente, estado, municipio, group_name, number2, text_data FROM extraccion4 WHERE 1=1"
    params = []

    # Agregar filtros opcionales
    if nombre_cliente:
        query += " AND LOWER(cliente) LIKE LOWER(%s)"
        params.append(f"%{nombre_cliente}%")  # Permitir coincidencias parciales

    if estado:
        query += " AND LOWER(estado) LIKE LOWER(%s)"
        params.append(f"%{estado}%")

    if municipio:
        query += " AND LOWER(municipio) LIKE LOWER(%s)"
        params.append(f"%{municipio}%")

    if group_name:
        query += " AND LOWER(group_name) LIKE LOWER(%s)"
        params.append(f"%{group_name}%")
    
    if number2:
        query += " AND LOWER(number2) LIKE LOWER(%s)"
        params.append(f"%{number2}%")

    # Ejecutar el query con los parámetros
    cursor.execute(query, tuple(params))
    results = cursor.fetchall()

    # Verificar si hay resultados
    if not results:
        cursor.close()
        conn.close()
        return None  # Devuelve None si no hay resultados

    # Crear un DataFrame
    df = pd.DataFrame(results, columns=[desc[0] for desc in cursor.description])

    # Cerrar la conexión
    cursor.close()
    conn.close()

    print(df.head())
    return df



# Procesar datos
import re
from nltk.corpus import stopwords
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import BytesIO
import base64

def generar_nube_palabras(nombre_cliente, estado, municipio, group_name, number2):
    df = obtener_datos_cliente(nombre_cliente, estado, municipio, group_name,)

    # Asegúrate de descargar las stopwords
    import nltk
    nltk.download('stopwords')
    
    # Obtener stopwords en español
    stop_words = set(stopwords.words('spanish'))
    # Agregar stopwords personalizadas
    stop_words.update(['a', 'al', 'algo', 'alguno', 'alguna', 'algunas', 'algunos', 'ambos', 
    'ante', 'antes', 'como', 'con', 'contra', 'cual', 'cuan', 'cuanta', 
    'cuantas', 'cuantos', 'de', 'debe', 'deben', 'debido', 'desde', 'donde', 
    'durante', 'el', 'ella', 'ellas', 'ellos', 'en', 'entre', 'era', 
    'eramos', 'eres', 'es', 'esa', 'esas', 'ese', 'esos', 'esta', 
    'estas', 'estoy', 'fin', 'ha', 'hace', 'haces', 'hacia', 'han', 
    'has', 'hasta', 'hay', 'la', 'las', 'le', 'les', 'lo', 'los', 
    'me', 'mi', 'mio', 'mios', 'muy', 'más', 'menos', 'necesito', 
    'ninguno', 'ninguna', 'no', 'nos', 'nosotros', 'nuestra', 'nuestras', 
    'nuestro', 'nuestros', 'o', 'otra', 'otras', 'otro', 'otros', 
    'para', 'por', 'porque', 'que', 'quien', 'quienes', 'se', 'su', 
    'sus', 'tanto', 'tan', 'tanto', 'te', 'ti', 'tus', 'un', 'una', 
    'unas', 'uno', 'unos', 'usted', 've', 'vez', 'vosotros', 'ya', 
    'él', 'ella', 'ellos', 'ellas', 'https', '5', 'com', 'chat', 'www',
    'hola', 'si', 'no', 'x', 'aquí', 'aqui', 'cómo', 'como', 'día', 'buenos',
    'días', 'dia', 'dias', 'noches', 'noche', 't', 'xd', 'a', 'acá', 'ahí', 
    'ajena', 'ajeno', 'ajenos', 'al', 'algo', 'algún', 'alguna', 'alguno', 
    'algunos', 'allá', 'allí', 'ambos', 'ante', 'antes', 'aquel', 'aquella', 
    'aquello', 'aquellos', 'aquí', 'arriba', 'así', 'atrás', 'aun', 'aunque', 
    'bajo', 'bastante', 'bien', 'cabe', 'cada', 'casi', 'cierto', 'cierta', 
    'ciertos', 'como', 'con', 'conmigo', 'conseguimos', 'conseguir', 'consigo', 
    'consigue', 'consiguen', 'consigues', 'contigo', 'contra', 'cual', 'cuales', 
    'cualquier', 'cualquiera', 'cualquiera', 'cuan', 'cuando', 'cuanto', 'cuanta', 
    'cuantos', 'de', 'dejar', 'del', 'demás', 'demasiada', 'demasiado', 'dentro', 
    'desde', 'donde', 'dos', 'el', 'él', 'ella', 'ello', 'ellos', 'empleáis', 
    'emplean', 'emplear', 'empleas', 'empleo', 'en', 'encima', 'entonces', 
    'entre', 'era', 'eras', 'eramos', 'eran', 'eres', 'es', 'esa', 'ese', 
    'eso', 'esos', 'esta', 'estas', 'estaba', 'estado', 'estáis', 'estamos', 
    'están', 'estar', 'este', 'esto', 'estos', 'estoy', 'etc', 'fin', 'fue', 
    'fueron', 'fui', 'fuimos', 'gueno', 'ha', 'hace', 'haces', 'hacéis', 
    'hacemos', 'hacen', 'hacer', 'hacia', 'hago', 'hasta', 'incluso', 'intenta', 
    'intentas', 'intentáis', 'intentamos', 'intentan', 'intentar', 'intento', 
    'ir', 'jamás', 'junto', 'juntos', 'la', 'lo', 'los', 'largo', 'más', 'me', 
    'menos', 'mi', 'mis', 'mía', 'mías', 'mientras', 'mío', 'míos', 'misma', 
    'mismo', 'mismos', 'modo', 'mucha', 'muchas', 'muchísima', 'muchísimo', 
    'muchos', 'muy', 'nada', 'ni', 'ningún', 'ninguna', 'ninguno', 'ningunos', 
    'no', 'nos', 'nosotras', 'nosotros', 'nuestra', 'nuestro', 'nuestros', 
    'nunca', 'os', 'otra', 'otros', 'para', 'parecer', 'pero', 'poca', 'pocas', 
    'poco', 'podéis', 'podemos', 'poder', 'podría', 'podrías', 'podríais', 
    'podríamos', 'podrían', 'por', 'por qué', 'porque', 'primero', 'puede', 
    'pueden', 'puedo', 'pues', 'que', 'qué', 'querer', 'quién', 'quiénes', 
    'quienesquiera', 'quienquiera', 'quizá', 'quizás', 'sabe', 'sabes', 
    'saben', 'sabéis', 'sabemos', 'saber', 'se', 'según', 'ser', 'si', 'sí', 
    'siempre', 'siendo', 'sin', 'sino', 'so', 'sobre', 'sois', 'solamente', 
    'solo', 'sólo', 'somos', 'soy', 'sr', 'sra', 'sres', 'sta', 'su', 'sus', 
    'suya', 'suyo', 'suyos', 'tal', 'tales', 'también', 'tampoco', 'tan', 
    'tanta', 'tanto', 'te', 'tenéis', 'tenemos', 'tener', 'tengo', 'ti', 
    'tiempo', 'tiene', 'tienen', 'toda', 'todo', 'tomar', 'trabaja', 'trabajo', 
    'trabajáis', 'trabajamos', 'trabajan', 'trabajar', 'trabajas', 'tras', 'tú', 
    'tu', 'tus', 'tuya', 'tuyo', 'tuyos', 'último', 'ultimo', 'un', 'una', 'unos', 
    'usa', 'usas', 'usáis', 'usamos', 'usan', 'usar', 'uso', 'usted', 'ustedes', 
    'va', 'van', 'vais', 'valor', 'vamos', 'varias', 'varios', 'vaya', 'verdadera', 
    'vosotras', 'vosotros', 'voy', 'vuestra', 'vuestro', 'vuestros', 'y', 'ya', 'yo', 
    'xd', 'jajaja', 'jajajaja', 'jajajajaja', 'bueno', 'media', 'gracias', 'we', 
    'wey', 'wa', 'k', 'a', 'ver', 'q', 'am', 'pm', 'c', 's', 'pa', 'v', 'l', 'buena',
    'm', 'sé', 'jaja', 'ah', 'ja', 'p', 'buenas', 'seu', 'em', 'ven'])  # Coloca más stopwords de ser necesario

    # Combinar todos los textos en una sola cadena
    texto_combinado = ' '.join(df['text_data'].dropna())

    # Preprocesar el texto
    palabras = re.findall(r'\w+', texto_combinado.lower())
    palabras_filtradas = [palabra for palabra in palabras if palabra not in stop_words and not palabra.isdigit()]

    # Contar las frecuencias de palabras
    frecuencias = Counter(palabras_filtradas)

    # Generar la nube de palabras
    nube_palabras = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(frecuencias)

    # Convertir la nube de palabras a imagen en base64 para renderizar en el template
    buffer = BytesIO()
    nube_palabras.to_image().save(buffer, format='PNG')
    buffer.seek(0)
    imagen_nube = base64.b64encode(buffer.read()).decode('utf-8')

    return imagen_nube

# Crear la vista para renderizar la nube
from django.contrib import messages
from django.shortcuts import render

def nube_palabras_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:  # Verifica si el usuario es un admin
            nombre_cliente = request.GET.get('cliente')  # Permite buscar cualquier cliente
        else:
            nombre_cliente = request.user.username  # Usa su nombre de usuario
    else:
        nombre_cliente = 'prueba'  # O un valor predeterminado si no está autenticado

    estado = request.GET.get('estado')
    municipio = request.GET.get('municipio')
    group_name = request.GET.get('group_name')
    number2 = request.GET.get('number2')
    # Obtener estados y municipios distintos
    estados_municipios = obtener_estados_municipios_distintos(nombre_cliente)
    grupos = obtener_grupos(nombre_cliente)

    # Genera la nube de palabras usando el nombre de cliente proporcionado
    imagen_nube = generar_nube_palabras(nombre_cliente, estado, municipio, group_name, number2)

    # Verifica si la imagen de la nube de palabras está vacía (significa que no hay datos)
    if imagen_nube is None or not imagen_nube.strip():
        messages.warning(request, "No se encontraron datos que coincidan con la búsqueda.")

    return render(request, 'tu_template.html', {
        'imagen_nube': imagen_nube,
        'nombre_cliente': nombre_cliente,
        'estado': estado,
        'municipio': municipio,
        'group_name': group_name,
        'number2': number2,
        'estados_municipios': estados_municipios,
        'grupos': grupos,
    })


from django.shortcuts import render
import mysql.connector
import pandas as pd

# Crear vista para renderizar la tabla
def tabla_datos_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:  # Verifica si el usuario es un admin
            nombre_cliente = request.GET.get('cliente')  # Permite buscar cualquier cliente
        else:
            nombre_cliente = request.user.username  # Usa su nombre de usuario
    else:
        nombre_cliente = 'prueba'  # O un valor predeterminado si no está autenticado

    estado = request.GET.get('estado')
    municipio = request.GET.get('municipio')
    group_name = request.GET.get('group_name')
    number2 = request.GET.get('number2')
    # Obtener estados y municipios distintos
    estados_municipios = obtener_estados_municipios_distintos(nombre_cliente)
    grupos = obtener_grupos(nombre_cliente)

    # Conectar a la base de datos
    conn = connection_pool.get_connection()
    
    cursor = conn.cursor()

    # Construir el query base
    query = "SELECT * FROM extraccion4 WHERE 1=1"
    params = []

    # Agregar filtros opcionales
    if nombre_cliente:
        query += " AND LOWER(cliente) LIKE LOWER(%s)"
        params.append(f"%{nombre_cliente}%")  # Permitir coincidencias parciales

    if estado:
        query += " AND LOWER(estado) LIKE LOWER(%s)"
        params.append(f"%{estado}%")

    if municipio:
        query += " AND LOWER(municipio) LIKE LOWER(%s)"
        params.append(f"%{municipio}%")

    if group_name:
        query += " AND LOWER(group_name) LIKE LOWER(%s)"
        params.append(f"%{group_name}%")

    if number2:
        query += " AND LOWER(number2) LIKE LOWER(%s)"
        params.append(f"%{number2}%")

    # Ejecutar el query con los parámetros
    cursor.execute(query, tuple(params))
    results = cursor.fetchall()

    # Crear un DataFrame si hay resultados
    if results:
        df = pd.DataFrame(results, columns=[desc[0] for desc in cursor.description])
        # Convertir DataFrame a lista de diccionarios
        datos_tabla = df.to_dict(orient='records')
    else:
        datos_tabla = []  # Cambiar a lista vacía si no hay resultados

    # Cerrar la conexión
    cursor.close()
    conn.close()

    # Paginación
    paginator = Paginator(datos_tabla, 100)  # Mostrar 100 registros por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Renderizar la plantilla con los datos
    return render(request, 'tu_template.html', {
        'datos_tabla': datos_tabla,
        'nombre_cliente': nombre_cliente,
        'estado': estado,
        'municipio': municipio,
        'group_name': group_name,
        'number2': number2,
        'estados_municipios': estados_municipios,
        'grupos': grupos,
    })

# Función para insertar mensajes como administrador a la base de datos "data_wa"
from django.http import HttpResponseForbidden

from django.http import HttpResponseForbidden
import mysql.connector

def insertar_mensajes_view(request):    
    # Verificar si el usuario es un administrador
    if not request.user.is_staff:
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")

    if request.method == 'POST':
        text_data = request.POST.get('text_data')  # Usar el nombre adecuado
        cantidad = int(request.POST.get('cantidad', 0))
        cliente = request.POST.get('cliente')  # Obtener el cliente del formulario
        number2 = request.POST.get('number2') # Obtener el número de teléfono del formulario
        estado = request.POST.get('estado')
        municipio = request.POST.get('municipio')
        group_name = request.POST.get('group_name')

        if text_data and cantidad > 0 and cliente:
            # Conectar a la base de datos
            conn = connection_pool.get_connection()
            cursor = conn.cursor()

            # Insertar los mensajes en la base de datos
            sql = "INSERT INTO extraccion4 (text_data, cliente, number2, estado, municipio, group_name) VALUES (%s, %s, %s, %s, %s, %s)"
            data = [(text_data, cliente, number2, estado, municipio, group_name)] * cantidad  # Crear una lista con el mensaje y el cliente repetido
            
            try:
                cursor.executemany(sql, data)
                conn.commit()
                mensaje = f"Se han insertado {cantidad} mensajes con el texto '{text_data}' para el cliente '{cliente}' utilizando el siguiente número '{number2}', dentro del estado y municipio de '{estado}', '{municipio}'."
            except Exception as e:
                mensaje = f"Ocurrió un error: {str(e)}"
            finally:
                # Cerrar la conexión
                cursor.close()
                conn.close()

    return render(request, 'tu_template.html', {'mensaje': mensaje})

def obtener_estados_municipios_distintos(nombre_cliente):
    conn = connection_pool.get_connection()
    cursor = conn.cursor()

    # Consulta para obtener estados y municipios distintos
    query = """
        SELECT DISTINCT estado, municipio
        FROM extraccion4 
        WHERE LOWER(cliente) = LOWER(%s)
    """
    
    cursor.execute(query, (nombre_cliente,))
    resultados = cursor.fetchall()

    # Cerrar la conexión
    cursor.close()
    conn.close()

    # Convertir resultados en un diccionario
    estados_municipios = [{"estado": row[0], "municipio": row[1]} for row in resultados]
    return estados_municipios

def obtener_grupos(nombre_cliente):
    conn = connection_pool.get_connection()
    cursor = conn.cursor()

    # Consulta para obtener grupos distintos
    query = """
        SELECT DISTINCT group_name 
        FROM extraccion4 
        WHERE LOWER(cliente) = LOWER(%s)
    """
    
    cursor.execute(query, (nombre_cliente,))
    resultados = cursor.fetchall()

    # Cerrar la conexión
    cursor.close()
    conn.close()

    # Convertir resultados en un diccionario
    grupos = [{"group_name": row[0]} for row in resultados]
    return grupos

from django.http import JsonResponse
import mysql.connector
  
