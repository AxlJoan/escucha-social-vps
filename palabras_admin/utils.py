import mysql.connector
import pandas as pd
import re
from nltk.corpus import stopwords
from collections import Counter
from wordcloud import WordCloud
from io import BytesIO
import base64

def obtener_datos_cliente(nombre_cliente=None, estado=None, municipio=None, group_name=None, number2=None, fecha_inicio=None, fecha_fin=None):
    conn = mysql.connector.connect(
        host='158.69.26.160',
        user='admin',
        password='S3gur1d4d2025',
        database='data_wa'
    )
    cursor = conn.cursor()
    query = "SELECT cliente, estado, municipio, group_name, number2, text_data, timestamp FROM extraccion4 WHERE 1=1"
    params = []
    if nombre_cliente:
        query += " AND LOWER(cliente) LIKE LOWER(%s)"
        params.append(f"%{nombre_cliente}%")
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
    if fecha_inicio:
        query += " AND timestamp >= %s"
        params.append(fecha_inicio)
    if fecha_fin:
        query += " AND timestamp <= %s"
        params.append(fecha_fin)
    
    cursor.execute(query, tuple(params))
    results = cursor.fetchall()
    if not results:
        cursor.close()
        conn.close()
        return None
    df = pd.DataFrame(results, columns=[desc[0] for desc in cursor.description])
    cursor.close()
    conn.close()
    return df

def obtener_grupos(nombre_cliente):
    conn = mysql.connector.connect(
        host='158.69.26.160',
        user='admin',
        password='S3gur1d4d2025',
        database='data_wa'
    )
    cursor = conn.cursor()
    query = """
        SELECT DISTINCT group_name 
        FROM extraccion4 
        WHERE LOWER(cliente) = LOWER(%s)
    """
    cursor.execute(query, (nombre_cliente,))
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    grupos = [{"group_name": row[0]} for row in resultados]
    return grupos

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
    stop_words.update(['a', 'al', 'algo', 'alguno', 'alguna', 'algunas', 'algunos', 'ambos', 'ante', 'antes', 'como', 'con', 'contra', 'cual', 'cuan', 'cuanta', 
    'cuantas', 'cuantos', 'de', 'debe', 'deben', 'debido', 'desde', 'donde', 'durante', 'el', 'ella', 'ellas', 'ellos', 'en', 'entre', 'era', 
    'eramos', 'eres', 'es', 'esa', 'esas', 'ese', 'esos', 'esta', 'estas', 'estoy', 'fin', 'ha', 'hace', 'haces', 'hacia', 'han', 
    'has', 'hasta', 'hay', 'la', 'las', 'le', 'les', 'lo', 'los', 'me', 'mi', 'mio', 'mios', 'muy', 'más', 'menos', 'necesito', 
    'ninguno', 'ninguna', 'no', 'nos', 'nosotros', 'nuestra', 'nuestras', 'nuestro', 'nuestros', 'o', 'otra', 'otras', 'otro', 'otros', 
    'para', 'por', 'porque', 'que', 'quien', 'quienes', 'se', 'su', 'sus', 'tanto', 'tan', 'tanto', 'te', 'ti', 'tus', 'un', 'una', 
    'unas', 'uno', 'unos', 'usted', 've', 'vez', 'vosotros', 'ya', 'él', 'ella', 'ellos', 'ellas', 'https', '5', 'com', 'chat', 'www',
    'hola', 'si', 'no', 'x', 'aquí', 'aqui', 'cómo', 'como', 'día', 'buenos','días', 'dia', 'dias', 'noches', 'noche', 't', 'xd', 'a', 'acá', 'ahí', 
    'ajena', 'ajeno', 'ajenos', 'al', 'algo', 'algún', 'alguna', 'alguno', 'algunos', 'allá', 'allí', 'ambos', 'ante', 'antes', 'aquel', 'aquella', 
    'aquello', 'aquellos', 'aquí', 'arriba', 'así', 'atrás', 'aun', 'aunque', 'bajo', 'bastante', 'bien', 'cabe', 'cada', 'casi', 'cierto', 'cierta', 
    'ciertos', 'como', 'con', 'conmigo', 'conseguimos', 'conseguir', 'consigo', 'consigue', 'consiguen', 'consigues', 'contigo', 'contra', 'cual', 'cuales', 
    'cualquier', 'cualquiera', 'cualquiera', 'cuan', 'cuando', 'cuanto', 'cuanta', 'cuantos', 'de', 'dejar', 'del', 'demás', 'demasiada', 'demasiado', 'dentro', 
    'desde', 'donde', 'dos', 'el', 'él', 'ella', 'ello', 'ellos', 'empleáis', 'emplean', 'emplear', 'empleas', 'empleo', 'en', 'encima', 'entonces', 
    'entre', 'era', 'eras', 'eramos', 'eran', 'eres', 'es', 'esa', 'ese', 'eso', 'esos', 'esta', 'estas', 'estaba', 'estado', 'estáis', 'estamos', 
    'están', 'estar', 'este', 'esto', 'estos', 'estoy', 'etc', 'fin', 'fue', 'fueron', 'fui', 'fuimos', 'gueno', 'ha', 'hace', 'haces', 'hacéis', 
    'hacemos', 'hacen', 'hacer', 'hacia', 'hago', 'hasta', 'incluso', 'intenta', 'intentas', 'intentáis', 'intentamos', 'intentan', 'intentar', 'intento', 
    'ir', 'jamás', 'junto', 'juntos', 'la', 'lo', 'los', 'largo', 'más', 'me', 'menos', 'mi', 'mis', 'mía', 'mías', 'mientras', 'mío', 'míos', 'misma', 
    'mismo', 'mismos', 'modo', 'mucha', 'muchas', 'muchísima', 'muchísimo', 'muchos', 'muy', 'nada', 'ni', 'ningún', 'ninguna', 'ninguno', 'ningunos', 
    'no', 'nos', 'nosotras', 'nosotros', 'nuestra', 'nuestro', 'nuestros', 'nunca', 'os', 'otra', 'otros', 'para', 'parecer', 'pero', 'poca', 'pocas', 
    'poco', 'podéis', 'podemos', 'poder', 'podría', 'podrías', 'podríais', 'podríamos', 'podrían', 'por', 'por qué', 'porque', 'primero', 'puede', 
    'pueden', 'puedo', 'pues', 'que', 'qué', 'querer', 'quién', 'quiénes', 'quienesquiera', 'quienquiera', 'quizá', 'quizás', 'sabe', 'sabes', 
    'saben', 'sabéis', 'sabemos', 'saber', 'se', 'según', 'ser', 'si', 'sí', 'siempre', 'siendo', 'sin', 'sino', 'so', 'sobre', 'sois', 'solamente', 
    'solo', 'sólo', 'somos', 'soy', 'sr', 'sra', 'sres', 'sta', 'su', 'sus', 'suya', 'suyo', 'suyos', 'tal', 'tales', 'también', 'tampoco', 'tan', 
    'tanta', 'tanto', 'te', 'tenéis', 'tenemos', 'tener', 'tengo', 'ti', 'tiempo', 'tiene', 'tienen', 'toda', 'todo', 'tomar', 'trabaja', 'trabajo', 
    'trabajáis', 'trabajamos', 'trabajan', 'trabajar', 'trabajas', 'tras', 'tú', 'tu', 'tus', 'tuya', 'tuyo', 'tuyos', 'último', 'ultimo', 'un', 'una', 'unos', 
    'usa', 'usas', 'usáis', 'usamos', 'usan', 'usar', 'uso', 'usted', 'ustedes', 'va', 'van', 'vais', 'valor', 'vamos', 'varias', 'varios', 'vaya', 'verdadera', 
    'vosotras', 'vosotros', 'voy', 'vuestra', 'vuestro', 'vuestros', 'y', 'ya', 'yo', 'xd', 'jajaja', 'jajajaja', 'jajajajaja', 'bueno', 'media', 'gracias', 'we', 
    'wey', 'wa', 'k', 'a', 'ver', 'q', 'am', 'pm', 'c', 's', 'pa', 'v', 'l', 'buena','m', 'sé', 'jaja', 'ah', 'ja', 'p', 'buenas', 'seu', 'em', 'ven'])  # Coloca más stopwords de ser necesario
    # Extraer palabras (se convierten a minúsculas)
    palabras = re.findall(r'\w+', texto_combinado.lower())
    palabras_filtradas = [p for p in palabras if p not in stop_words and not p.isdigit()]
    frecuencias = Counter(palabras_filtradas)
    top_palabras = frecuencias.most_common(10)
    return top_palabras

def generar_nube_palabras(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin):
    df = obtener_datos_cliente(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin)
    if df is None or df.empty:
        return ""
    texto_combinado = ' '.join(df['text_data'].dropna())
    import nltk
    nltk.download('stopwords', quiet=True)
    stop_words = set(stopwords.words('spanish'))
    stop_words.update(['a', 'al', 'algo', 'alguno', 'alguna', 'algunas', 'algunos', 'ambos', 'ante', 'antes', 'como', 'con', 'contra', 'cual', 'cuan', 'cuanta', 
    'cuantas', 'cuantos', 'de', 'debe', 'deben', 'debido', 'desde', 'donde', 'durante', 'el', 'ella', 'ellas', 'ellos', 'en', 'entre', 'era', 
    'eramos', 'eres', 'es', 'esa', 'esas', 'ese', 'esos', 'esta', 'estas', 'estoy', 'fin', 'ha', 'hace', 'haces', 'hacia', 'han', 
    'has', 'hasta', 'hay', 'la', 'las', 'le', 'les', 'lo', 'los', 'me', 'mi', 'mio', 'mios', 'muy', 'más', 'menos', 'necesito', 
    'ninguno', 'ninguna', 'no', 'nos', 'nosotros', 'nuestra', 'nuestras', 'nuestro', 'nuestros', 'o', 'otra', 'otras', 'otro', 'otros', 
    'para', 'por', 'porque', 'que', 'quien', 'quienes', 'se', 'su', 'sus', 'tanto', 'tan', 'tanto', 'te', 'ti', 'tus', 'un', 'una', 
    'unas', 'uno', 'unos', 'usted', 've', 'vez', 'vosotros', 'ya', 'él', 'ella', 'ellos', 'ellas', 'https', '5', 'com', 'chat', 'www',
    'hola', 'si', 'no', 'x', 'aquí', 'aqui', 'cómo', 'como', 'día', 'buenos','días', 'dia', 'dias', 'noches', 'noche', 't', 'xd', 'a', 'acá', 'ahí', 
    'ajena', 'ajeno', 'ajenos', 'al', 'algo', 'algún', 'alguna', 'alguno', 'algunos', 'allá', 'allí', 'ambos', 'ante', 'antes', 'aquel', 'aquella', 
    'aquello', 'aquellos', 'aquí', 'arriba', 'así', 'atrás', 'aun', 'aunque', 'bajo', 'bastante', 'bien', 'cabe', 'cada', 'casi', 'cierto', 'cierta', 
    'ciertos', 'como', 'con', 'conmigo', 'conseguimos', 'conseguir', 'consigo', 'consigue', 'consiguen', 'consigues', 'contigo', 'contra', 'cual', 'cuales', 
    'cualquier', 'cualquiera', 'cualquiera', 'cuan', 'cuando', 'cuanto', 'cuanta', 'cuantos', 'de', 'dejar', 'del', 'demás', 'demasiada', 'demasiado', 'dentro', 
    'desde', 'donde', 'dos', 'el', 'él', 'ella', 'ello', 'ellos', 'empleáis', 'emplean', 'emplear', 'empleas', 'empleo', 'en', 'encima', 'entonces', 
    'entre', 'era', 'eras', 'eramos', 'eran', 'eres', 'es', 'esa', 'ese', 'eso', 'esos', 'esta', 'estas', 'estaba', 'estado', 'estáis', 'estamos', 
    'están', 'estar', 'este', 'esto', 'estos', 'estoy', 'etc', 'fin', 'fue', 'fueron', 'fui', 'fuimos', 'gueno', 'ha', 'hace', 'haces', 'hacéis', 
    'hacemos', 'hacen', 'hacer', 'hacia', 'hago', 'hasta', 'incluso', 'intenta', 'intentas', 'intentáis', 'intentamos', 'intentan', 'intentar', 'intento', 
    'ir', 'jamás', 'junto', 'juntos', 'la', 'lo', 'los', 'largo', 'más', 'me', 'menos', 'mi', 'mis', 'mía', 'mías', 'mientras', 'mío', 'míos', 'misma', 
    'mismo', 'mismos', 'modo', 'mucha', 'muchas', 'muchísima', 'muchísimo', 'muchos', 'muy', 'nada', 'ni', 'ningún', 'ninguna', 'ninguno', 'ningunos', 
    'no', 'nos', 'nosotras', 'nosotros', 'nuestra', 'nuestro', 'nuestros', 'nunca', 'os', 'otra', 'otros', 'para', 'parecer', 'pero', 'poca', 'pocas', 
    'poco', 'podéis', 'podemos', 'poder', 'podría', 'podrías', 'podríais', 'podríamos', 'podrían', 'por', 'por qué', 'porque', 'primero', 'puede', 
    'pueden', 'puedo', 'pues', 'que', 'qué', 'querer', 'quién', 'quiénes', 'quienesquiera', 'quienquiera', 'quizá', 'quizás', 'sabe', 'sabes', 
    'saben', 'sabéis', 'sabemos', 'saber', 'se', 'según', 'ser', 'si', 'sí', 'siempre', 'siendo', 'sin', 'sino', 'so', 'sobre', 'sois', 'solamente', 
    'solo', 'sólo', 'somos', 'soy', 'sr', 'sra', 'sres', 'sta', 'su', 'sus', 'suya', 'suyo', 'suyos', 'tal', 'tales', 'también', 'tampoco', 'tan', 
    'tanta', 'tanto', 'te', 'tenéis', 'tenemos', 'tener', 'tengo', 'ti', 'tiempo', 'tiene', 'tienen', 'toda', 'todo', 'tomar', 'trabaja', 'trabajo', 
    'trabajáis', 'trabajamos', 'trabajan', 'trabajar', 'trabajas', 'tras', 'tú', 'tu', 'tus', 'tuya', 'tuyo', 'tuyos', 'último', 'ultimo', 'un', 'una', 'unos', 
    'usa', 'usas', 'usáis', 'usamos', 'usan', 'usar', 'uso', 'usted', 'ustedes', 'va', 'van', 'vais', 'valor', 'vamos', 'varias', 'varios', 'vaya', 'verdadera', 
    'vosotras', 'vosotros', 'voy', 'vuestra', 'vuestro', 'vuestros', 'y', 'ya', 'yo', 'xd', 'jajaja', 'jajajaja', 'jajajajaja', 'bueno', 'media', 'gracias', 'we', 
    'wey', 'wa', 'k', 'a', 'ver', 'q', 'am', 'pm', 'c', 's', 'pa', 'v', 'l', 'buena','m', 'sé', 'jaja', 'ah', 'ja', 'p', 'buenas', 'seu', 'em', 'ven'])  # Coloca más stopwords de ser necesario
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

# Nuevas funciones para métricas
def obtener_mensajes_totales(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin):
    df = obtener_datos_cliente(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin)
    if df is None:
        return 0
    return len(df)

def obtener_numeros_totales(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin):
    df = obtener_datos_cliente(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin)
    if df is None:
        return 0
    return df['number2'].nunique()

def obtener_grupos_extraidos(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin):
    df = obtener_datos_cliente(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin)
    if df is None:
        return 0
    return df['group_name'].nunique()

def generar_grafo(nombre_cliente, group_name, number2, fecha_inicio, fecha_fin):
    df = obtener_datos_cliente(nombre_cliente, None, None, group_name, number2, fecha_inicio, fecha_fin)
    if df is None or df.empty:
        return ""

    # Limitar a los primeros 100 registros
    df = df.head(100)
    
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

def generar_analisis_sentimientos(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin):
    df = obtener_datos_cliente(nombre_cliente, estado, municipio, group_name, number2, fecha_inicio, fecha_fin)
    if df is None or df.empty:
        return {}
    
    textos = list(df['text_data'].dropna())
    # Limitar a los primeros 150 mensajes (o el número que consideres adecuado)
    textos_limitados = textos[:150]
    
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



