import pandas as pd
# import mysql.connector
import pandas as pd
import re
from nltk.corpus import stopwords
from collections import Counter
from wordcloud import WordCloud
from io import BytesIO
import base64
from palabras_admin.models import MonitoreoPalabras

"""
Nombre de la función: cargar_datos_csv
Descripción: Función que carga los datos desde un archivo CSV y convierte la columna "timestamp" a formato datetime.
Entradas: El csv datos_cache.csv que es generado por el código exportar_csv.py.
Salidas: Un DataFrame de Pandas con los datos del archivo CSV.
"""
def cargar_datos_csv():
    ruta_csv = '/var/www/django-palab/datos_cache.csv'  # Ajusta la ruta según corresponda
    # Parseamos la columna "timestamp" a formato datetime
    df = pd.read_csv(ruta_csv, parse_dates=['timestamp'])
    return df

"""
Nombre de la función: obtener_datos_cliente
Descripción: Filtra los datos del CSV según los parámetros proporcionados, permitiendo buscar por cliente, estado, 
             municipio, nombre del grupo, número de teléfono y rango de fechas.
Entradas: 
            - nombre_cliente (str, opcional): Nombre del cliente a filtrar.
            - estado (str, opcional): Estado a filtrar.
            - municipio (str, opcional): Municipio a filtrar.
            - group_name (str, opcional): Nombre del grupo a filtrar.
            - number2 (str, opcional): Número de teléfono a filtrar.
            - fecha_inicio (str, opcional): Fecha mínima para filtrar (en formato YYYY-MM-DD).
            - fecha_fin (str, opcional): Fecha máxima para filtrar (en formato YYYY-MM-DD).
Salidas: 
            - Un DataFrame filtrado con los datos coincidentes o None si no hay resultados.
"""
def obtener_datos_cliente(nombre_cliente=None, estado=None, municipio=None, group_name=None, number2=None, text_data=None, fecha_inicio=None, fecha_fin=None, usuario=None):
    df = cargar_datos_csv()
    
    if nombre_cliente:
        df = df[df["cliente"].str.lower().str.contains(nombre_cliente.lower(), na=False)]
    if estado:
        df = df[df["estado"].str.lower().str.contains(estado.lower(), na=False)]
    if municipio:
        df = df[df["municipio"].str.lower().str.contains(municipio.lower(), na=False)]
    if group_name:
        df = df[df["group_name"].str.lower().str.contains(group_name.lower(), na=False)]
    if number2:
        # Convirtiendo number2 a string para aplicar el filtro
        df = df[df["number2"].astype(str).str.lower().str.contains(number2.lower(), na=False)]
    if text_data:
        df = df[df["text_data"].str.lower().str.contains(text_data.lower(), na=False)]  # Nuevo filtro
    if fecha_inicio:
        # Convertir la fecha de filtro a datetime si no lo está
        df = df[df["timestamp"] >= pd.to_datetime(fecha_inicio)]
    if fecha_fin:
        df = df[df["timestamp"] <= pd.to_datetime(fecha_fin)]
        
    # Filtrar por palabras monitoreadas
    if usuario:
        palabras_monitoreo = list(MonitoreoPalabras.objects.filter(usuario=usuario).values_list('palabra', flat=True))
        if palabras_monitoreo:  # Solo filtrar si hay palabras
            df = df[df["text_data"].fillna('').str.contains('|'.join(palabras_monitoreo), case=False, na=False)]
    
    if df.empty:
        return None
    return df

"""
Nombre de la función: obtener_grupos
Descripción: Obtiene la lista de grupos únicos asociados a un cliente en la base de datos.
Entradas: 
            - nombre_cliente (str): Nombre del cliente cuyos grupos se desean obtener.
Salidas: 
            - Una lista de diccionarios con los nombres de los grupos asociados al cliente.
"""
def obtener_grupos(nombre_cliente):
    df = cargar_datos_csv()
    df = df[df["cliente"].str.lower() == nombre_cliente.lower()]
    grupos = df["group_name"].dropna().unique()
    return [{"group_name": g} for g in grupos]

'''
Nombre de la función: generar_top_palabras
Descripción: Genera una lista con las 10 palabras más frecuentes en los textos asociados a 
             un cliente dentro de un rango de fechas, excluyendo palabras vacías (stopwords).
Entradas:
            - nombre_cliente (str): Nombre del cliente para filtrar los datos.
            - estado (str): Estado asociado a los datos.
            - municipio (str): Municipio asociado a los datos.
            - group_name (str): Nombre del grupo de donde provienen los mensajes.
            - number2 (str): Número de teléfono asociado.
            - fecha_inicio (str): Fecha de inicio para filtrar los datos.
            - fecha_fin (str): Fecha de fin para filtrar los datos.
Salidas:
            - Una lista de las 10 palabras más frecuentes en los textos, excluyendo stopwords y números.
'''
def generar_top_palabras(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin):
    df = obtener_datos_cliente(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin)
    if df is None or df.empty:
        return []
    # Combinar todo el texto de la columna 'text_data'
    texto_combinado = ' '.join(df['text_data'].dropna())
    # Descargar stopwords (quiet=True para que no imprima mensajes)
    import nltk
    nltk.download('stopwords', quiet=True)
    stop_words = set(stopwords.words('spanish'))
    # Agrega stopwords personalizadas según necesites
    stop_words.update(['a', 'al', 'algo', 'alguno', 'alguna', 'algunas', 'algunos', 'ambos', 'ante', 'antes', 'como', 'con', 'contra', 'cual', 'cuan', 'cuanta', 'wey', 'wa', 'k', 'a', 'ver', 'q', 'am', 'pm', 'c', 's', 'pa', 'v', 'l', 'buena','m', 'sé', 'jaja', 'ah', 'ja', 'p', 'buenas', 'seu', 'em',
    'cuantas', 'cuantos', 'de', 'debe', 'deben', 'debido', 'desde', 'donde', 'durante', 'el', 'ella', 'ellas', 'ellos', 'en', 'entre', 'era', 'eramos', 'eres', 'es', 'esa', 'esas', 'ese', 'esos', 'esta', 'estas', 'estoy', 'fin', 'ha', 'hace', 'haces', 'hacia', 'han', 
    'has', 'hasta', 'hay', 'la', 'las', 'le', 'les', 'lo', 'los', 'me', 'mi', 'mio', 'mios', 'muy', 'más', 'menos', 'necesito', 'ninguno', 'ninguna', 'no', 'nos', 'nosotros', 'nuestra', 'nuestras', 'nuestro', 'nuestros', 'o', 'otra', 'otras', 'otro', 'otros', 
    'para', 'por', 'porque', 'que', 'quien', 'quienes', 'se', 'su', 'sus', 'tanto', 'tan', 'tanto', 'te', 'ti', 'tus', 'un', 'una', 'unas', 'uno', 'unos', 'usted', 've', 'vez', 'vosotros', 'ya', 'él', 'ella', 'ellos', 'ellas', 'https', '5', 'com', 'chat', 'www',
    'hola', 'si', 'no', 'x', 'aquí', 'aqui', 'cómo', 'como', 'día', 'buenos','días', 'dia', 'dias', 'noches', 'noche', 't', 'xd', 'a', 'acá', 'ahí', 'ajena', 'ajeno', 'ajenos', 'al', 'algo', 'algún', 'alguna', 'alguno', 'algunos', 'allá', 'allí', 'ambos', 'ante', 'antes', 'aquel', 'aquella', 
    'aquello', 'aquellos', 'aquí', 'arriba', 'así', 'atrás', 'aun', 'aunque', 'bajo', 'bastante', 'bien', 'cabe', 'cada', 'casi', 'cierto', 'cierta', 'ciertos', 'como', 'con', 'conmigo', 'conseguimos', 'conseguir', 'consigo', 'consigue', 'consiguen', 'consigues', 'contigo', 'contra', 'cual', 'cuales', 
    'cualquier', 'cualquiera', 'cualquiera', 'cuan', 'cuando', 'cuanto', 'cuanta', 'cuantos', 'de', 'dejar', 'del', 'demás', 'demasiada', 'demasiado', 'dentro', 
    'desde', 'donde', 'dos', 'el', 'él', 'ella', 'ello', 'ellos', 'empleáis', 'emplean', 'emplear', 'empleas', 'empleo', 'en', 'encima', 'entonces', 'entre', 'era', 'eras', 'eramos', 'eran', 'eres', 'es', 'esa', 'ese', 'eso', 'esos', 'esta', 'estas', 'estaba', 'estado', 'estáis', 'estamos', 
    'están', 'estar', 'este', 'esto', 'estos', 'estoy', 'etc', 'fin', 'fue', 'fueron', 'fui', 'fuimos', 'gueno', 'ha', 'hace', 'haces', 'hacéis', 'hacemos', 'hacen', 'hacer', 'hacia', 'hago', 'hasta', 'incluso', 'intenta', 'intentas', 'intentáis', 'intentamos', 'intentan', 'intentar', 'intento', 
    'ir', 'jamás', 'junto', 'juntos', 'la', 'lo', 'los', 'largo', 'más', 'me', 'menos', 'mi', 'mis', 'mía', 'mías', 'mientras', 'mío', 'míos', 'misma', 'mismo', 'mismos', 'modo', 'mucha', 'muchas', 'muchísima', 'muchísimo', 'muchos', 'muy', 'nada', 'ni', 'ningún', 'ninguna', 'ninguno', 'ningunos', 
    'no', 'nos', 'nosotras', 'nosotros', 'nuestra', 'nuestro', 'nuestros', 'nunca', 'os', 'otra', 'otros', 'para', 'parecer', 'pero', 'poca', 'pocas', 'poco', 'podéis', 'podemos', 'poder', 'podría', 'podrías', 'podríais', 'podríamos', 'podrían', 'por', 'por qué', 'porque', 'primero', 'puede', 
    'pueden', 'puedo', 'pues', 'que', 'qué', 'querer', 'quién', 'quiénes', 'quienesquiera', 'quienquiera', 'quizá', 'quizás', 'sabe', 'sabes', 'saben', 'sabéis', 'sabemos', 'saber', 'se', 'según', 'ser', 'si', 'sí', 'siempre', 'siendo', 'sin', 'sino', 'so', 'sobre', 'sois', 'solamente', 
    'solo', 'sólo', 'somos', 'soy', 'sr', 'sra', 'sres', 'sta', 'su', 'sus', 'suya', 'suyo', 'suyos', 'tal', 'tales', 'también', 'tampoco', 'tan', 'tanta', 'tanto', 'te', 'tenéis', 'tenemos', 'tener', 'tengo', 'ti', 'tiempo', 'tiene', 'tienen', 'toda', 'todo', 'tomar', 'trabaja', 'trabajo', 
    'trabajáis', 'trabajamos', 'trabajan', 'trabajar', 'trabajas', 'tras', 'tú', 'tu', 'tus', 'tuya', 'tuyo', 'tuyos', 'último', 'ultimo', 'un', 'una', 'unos', 'usa', 'usas', 'usáis', 'usamos', 'usan', 'usar', 'uso', 'usted', 'ustedes', 'va', 'van', 'vais', 'valor', 'vamos', 'varias', 'varios', 'vaya', 'verdadera', 
    'vosotras', 'vosotros', 'voy', 'vuestra', 'vuestro', 'vuestros', 'y', 'ya', 'yo', 'xd', 'jajaja', 'jajajaja', 'jajajajaja', 'bueno', 'media', 'gracias', 'we', 'ven', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'share'])  # Coloca más stopwords de ser necesario
    # Extraer palabras (se convierten a minúsculas)
    palabras = re.findall(r'\w+', texto_combinado.lower())
    palabras_filtradas = [p for p in palabras if p not in stop_words and not p.isdigit()]
    frecuencias = Counter(palabras_filtradas)
    top_palabras = frecuencias.most_common(10)
    return top_palabras

'''
Nombre de la función: generar_nube_palabras
Descripción: Genera un texto combinado de los mensajes asociados a un cliente dentro de un rango 
             de fechas, eliminando palabras vacías (stopwords). Este texto se usa para la generación de nubes de palabras.
Entradas:
            - nombre_cliente (str): Nombre del cliente para filtrar los datos.
            - estado (str): Estado asociado a los datos.
            - municipio (str): Municipio asociado a los datos.
            - group_name (str): Nombre del grupo de donde provienen los mensajes.
            - number2 (str): Número de teléfono asociado.
            - fecha_inicio (str): Fecha de inicio para filtrar los datos.
            - fecha_fin (str): Fecha de fin para filtrar los datos.
Salidas:
            - Texto combinado de los mensajes filtrados, sin stopwords, listo para generar una nube de palabras.
'''
def generar_nube_palabras(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin):
    df = obtener_datos_cliente(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin)
    if df is None or df.empty:
        return ""
    texto_combinado = ' '.join(df['text_data'].dropna())
    import nltk
    nltk.download('stopwords', quiet=True)
    stop_words = set(stopwords.words('spanish'))
    stop_words.update(['a', 'al', 'algo', 'alguno', 'alguna', 'algunas', 'algunos', 'ambos', 'ante', 'antes', 'como', 'con', 'contra', 'cual', 'cuan', 'cuanta', 'wey', 'wa', 'k', 'a', 'ver', 'q', 'am', 'pm', 'c', 's', 'pa', 'v', 'l', 'buena','m', 'sé', 'jaja', 'ah', 'ja', 'p', 'buenas', 'seu', 'em',
    'cuantas', 'cuantos', 'de', 'debe', 'deben', 'debido', 'desde', 'donde', 'durante', 'el', 'ella', 'ellas', 'ellos', 'en', 'entre', 'era', 'eramos', 'eres', 'es', 'esa', 'esas', 'ese', 'esos', 'esta', 'estas', 'estoy', 'fin', 'ha', 'hace', 'haces', 'hacia', 'han', 
    'has', 'hasta', 'hay', 'la', 'las', 'le', 'les', 'lo', 'los', 'me', 'mi', 'mio', 'mios', 'muy', 'más', 'menos', 'necesito', 'ninguno', 'ninguna', 'no', 'nos', 'nosotros', 'nuestra', 'nuestras', 'nuestro', 'nuestros', 'o', 'otra', 'otras', 'otro', 'otros', 
    'para', 'por', 'porque', 'que', 'quien', 'quienes', 'se', 'su', 'sus', 'tanto', 'tan', 'tanto', 'te', 'ti', 'tus', 'un', 'una', 'unas', 'uno', 'unos', 'usted', 've', 'vez', 'vosotros', 'ya', 'él', 'ella', 'ellos', 'ellas', 'https', '5', 'com', 'chat', 'www',
    'hola', 'si', 'no', 'x', 'aquí', 'aqui', 'cómo', 'como', 'día', 'buenos','días', 'dia', 'dias', 'noches', 'noche', 't', 'xd', 'a', 'acá', 'ahí', 'ajena', 'ajeno', 'ajenos', 'al', 'algo', 'algún', 'alguna', 'alguno', 'algunos', 'allá', 'allí', 'ambos', 'ante', 'antes', 'aquel', 'aquella', 
    'aquello', 'aquellos', 'aquí', 'arriba', 'así', 'atrás', 'aun', 'aunque', 'bajo', 'bastante', 'bien', 'cabe', 'cada', 'casi', 'cierto', 'cierta', 'ciertos', 'como', 'con', 'conmigo', 'conseguimos', 'conseguir', 'consigo', 'consigue', 'consiguen', 'consigues', 'contigo', 'contra', 'cual', 'cuales', 
    'cualquier', 'cualquiera', 'cualquiera', 'cuan', 'cuando', 'cuanto', 'cuanta', 'cuantos', 'de', 'dejar', 'del', 'demás', 'demasiada', 'demasiado', 'dentro', 
    'desde', 'donde', 'dos', 'el', 'él', 'ella', 'ello', 'ellos', 'empleáis', 'emplean', 'emplear', 'empleas', 'empleo', 'en', 'encima', 'entonces', 'entre', 'era', 'eras', 'eramos', 'eran', 'eres', 'es', 'esa', 'ese', 'eso', 'esos', 'esta', 'estas', 'estaba', 'estado', 'estáis', 'estamos', 
    'están', 'estar', 'este', 'esto', 'estos', 'estoy', 'etc', 'fin', 'fue', 'fueron', 'fui', 'fuimos', 'gueno', 'ha', 'hace', 'haces', 'hacéis', 'hacemos', 'hacen', 'hacer', 'hacia', 'hago', 'hasta', 'incluso', 'intenta', 'intentas', 'intentáis', 'intentamos', 'intentan', 'intentar', 'intento', 
    'ir', 'jamás', 'junto', 'juntos', 'la', 'lo', 'los', 'largo', 'más', 'me', 'menos', 'mi', 'mis', 'mía', 'mías', 'mientras', 'mío', 'míos', 'misma', 'mismo', 'mismos', 'modo', 'mucha', 'muchas', 'muchísima', 'muchísimo', 'muchos', 'muy', 'nada', 'ni', 'ningún', 'ninguna', 'ninguno', 'ningunos', 
    'no', 'nos', 'nosotras', 'nosotros', 'nuestra', 'nuestro', 'nuestros', 'nunca', 'os', 'otra', 'otros', 'para', 'parecer', 'pero', 'poca', 'pocas', 'poco', 'podéis', 'podemos', 'poder', 'podría', 'podrías', 'podríais', 'podríamos', 'podrían', 'por', 'por qué', 'porque', 'primero', 'puede', 
    'pueden', 'puedo', 'pues', 'que', 'qué', 'querer', 'quién', 'quiénes', 'quienesquiera', 'quienquiera', 'quizá', 'quizás', 'sabe', 'sabes', 'saben', 'sabéis', 'sabemos', 'saber', 'se', 'según', 'ser', 'si', 'sí', 'siempre', 'siendo', 'sin', 'sino', 'so', 'sobre', 'sois', 'solamente', 
    'solo', 'sólo', 'somos', 'soy', 'sr', 'sra', 'sres', 'sta', 'su', 'sus', 'suya', 'suyo', 'suyos', 'tal', 'tales', 'también', 'tampoco', 'tan', 'tanta', 'tanto', 'te', 'tenéis', 'tenemos', 'tener', 'tengo', 'ti', 'tiempo', 'tiene', 'tienen', 'toda', 'todo', 'tomar', 'trabaja', 'trabajo', 
    'trabajáis', 'trabajamos', 'trabajan', 'trabajar', 'trabajas', 'tras', 'tú', 'tu', 'tus', 'tuya', 'tuyo', 'tuyos', 'último', 'ultimo', 'un', 'una', 'unos', 'usa', 'usas', 'usáis', 'usamos', 'usan', 'usar', 'uso', 'usted', 'ustedes', 'va', 'van', 'vais', 'valor', 'vamos', 'varias', 'varios', 'vaya', 'verdadera', 
    'vosotras', 'vosotros', 'voy', 'vuestra', 'vuestro', 'vuestros', 'y', 'ya', 'yo', 'xd', 'jajaja', 'jajajaja', 'jajajajaja', 'bueno', 'media', 'gracias', 'we', 'ven', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'share'])  # Coloca más stopwords de ser necesario
    palabras = re.findall(r'\w+', texto_combinado.lower())
    palabras_filtradas = [p for p in palabras if p not in stop_words and not p.isdigit()]
    frecuencias = Counter(palabras_filtradas)
    wc = WordCloud(width=800, height=400, background_color='white')
    wordcloud = wc.generate_from_frequencies(frecuencias)
    buffer = BytesIO()
    wordcloud.to_image().save(buffer, format='PNG')
    buffer.seek(0)
    imagen_nube = base64.b64encode(buffer.read()).decode('utf-8')
    return imagen_nube

'''
Nombre de la función: obtener_mensajes_totales
Descripción: Función que obtiene el número total de mensajes para un cliente específico, aplicando varios filtros.
Entradas: 
            - nombre_cliente (str) - Nombre del cliente a consultar.
            - estado (str) - Estado relacionado con los mensajes.
            - municipio (str) - Municipio relacionado con los mensajes.
            - group_name (str) - Nombre del grupo de WhatsApp.
            - number2 (str) - Número de teléfono del remitente.
            - fecha_inicio (str) - Fecha de inicio para filtrar los mensajes.
            - fecha_fin (str) - Fecha de fin para filtrar los mensajes.
Salidas: 
            - int - Número total de mensajes en el rango de fechas especificado.
'''
def obtener_mensajes_totales(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin):
    df = obtener_datos_cliente(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin)
    if df is None:
        return 0
    return len(df)

'''
Nombre de la función: obtener_numeros_totales
Descripción: Función que obtiene el número total de números de teléfono únicos para un cliente específico,
                 consultando la base de datos y devolviendo el valor más reciente registrado.
Entradas: 
            - nombre_cliente (str) - Nombre del cliente a consultar.
Salidas: 
            - dict: Un diccionario con las claves:
                    - "total" (int) - Número total de números únicos de teléfono.
'''
import mysql.connector

def obtener_numeros_totales(nombre_cliente):
    if not nombre_cliente:  # Si es None o vacío, evitar consulta
        return 0
    
    MYSQL_USER = "admin"
    MYSQL_PASS = "S3gur1d4d2025"
    MYSQL_HOST = "158.69.26.160"
    MYSQL_DB = "data_wa"

    try:
        con = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASS,
            database=MYSQL_DB
        )
        cursor = con.cursor(dictionary=True)
        
        query = """
        SELECT total, fecha_subida FROM total_participantes
        WHERE cliente = %s
        ORDER BY fecha_subida DESC LIMIT 1;
        """
        cursor.execute(query, (nombre_cliente,))
        result = cursor.fetchone()
        
        return result['total'] if result else 0
    except mysql.connector.Error as e:
        print(f"Error en MySQL: {e}")
        return 0
    finally:
        if 'con' in locals():
            con.close()

'''
Nombre de la función: obtener_grupos_extraidos
Descripción: Función que obtiene el número total de grupos únicos de WhatsApp para un cliente específico, aplicando varios filtros.
Entradas: 
            - nombre_cliente (str) - Nombre del cliente a consultar.
            - estado (str) - Estado relacionado con los mensajes.
            - municipio (str) - Municipio relacionado con los mensajes.
            - group_name (str) - Nombre del grupo de WhatsApp.
            - number2 (str) - Número de teléfono del remitente.
            - fecha_inicio (str) - Fecha de inicio para filtrar los mensajes.
            - fecha_fin (str) - Fecha de fin para filtrar los mensajes
Salidas: 
            - int - Número total de grupos únicos en el rango de fechas especificado.
'''
def obtener_grupos_extraidos(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin):
    df = obtener_datos_cliente(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin)
    if df is None:
        return 0
    return df['group_name'].nunique()

'''
Nombre de la función: generar_grafo
Descripción: Función que genera un grafo de relaciones entre los números de teléfono y los grupos de WhatsApp para un cliente específico.
Entradas: 
            - nombre_cliente (str) - Nombre del cliente a consultar.
            - group_name (str) - Nombre del grupo de WhatsApp.
            - number2 (str) - Número de teléfono del remitente.
            - fecha_inicio (str) - Fecha de inicio para filtrar los mensajes.
            - fecha_fin (str) - Fecha de fin para filtrar los mensajes
Salidas: 
            - str - HTML generado para visualizar el grafo de relaciones.
'''
def generar_grafo(nombre_cliente, group_name, number2, fecha_inicio, fecha_fin):
    df = obtener_datos_cliente(nombre_cliente, None, None, group_name, number2, fecha_inicio, fecha_fin)
    if df is None or df.empty:
        return ""
    from pyvis.network import Network
    net = Network(height="400px", width="100%", bgcolor="white", font_color="black")
    for _, row in df.iterrows():
        num = str(row['number2'])
        grp = str(row['group_name'])
        net.add_node(grp, label=grp, color="#b08cff")
        net.add_node(num, label=num, color="#fa8ba2")
        net.add_edge(grp, num)
    # Generar el HTML del grafo como string sin usar archivos temporales.
    html_str = net.generate_html(notebook=False)
    return html_str

'''
Nombre de la función: generar_analisis_sentimientos
Descripción: Función que genera un análisis de sentimientos para los mensajes de un cliente específico, aplicando varios filtros.
Entradas: 
            - nombre_cliente (str) - Nombre del cliente a consultar.
            - estado (str) - Estado relacionado con los mensajes.
            - municipio (str) - Municipio relacionado con los mensajes.
            - group_name (str) - Nombre del grupo de WhatsApp.
            - number2 (str) - Número de teléfono del remitente.
            - fecha_inicio (str) - Fecha de inicio para filtrar los mensajes.
            - fecha_fin (str) - Fecha de fin para filtrar los mensajes
Salidas: 
            - dict - Diccionario con el conteo de sentimientos (Negativo, Neutral, Positivo) o un error.
'''
def generar_analisis_sentimientos(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin):
    df = obtener_datos_cliente(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin)
    if df is None or df.empty:
        return {}
    
    textos = list(df['text_data'].dropna())
    # Limitar a los primeros 100 mensajes (o el número que consideres adecuado)
    textos_limitados = textos[:50]

    try:
        from transformers import pipeline
        sentiment_pipeline = pipeline("sentiment-analysis", model="SickBoy/analisis-sentimientos-spanish-eds", truncation=True)
        resultados = sentiment_pipeline(textos_limitados)
    except Exception as e:
        return {"Error": str(e)}
    
    # Diccionario de mapeo: ajusta según corresponda a tu modelo
    mapeo = {
        "LABEL_0": "Negativo",
        "LABEL_1": "Neutral",
        "LABEL_2": "Positivo"
    }
    
    conteo_sentimientos = {}
    for resultado in resultados:
        etiqueta = resultado.get('label', 'Desconocido')
        etiqueta_legible = mapeo.get(etiqueta, etiqueta)
        conteo_sentimientos[etiqueta_legible] = conteo_sentimientos.get(etiqueta_legible, 0) + 1

    return conteo_sentimientos