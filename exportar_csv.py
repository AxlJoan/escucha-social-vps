import csv
import os
import logging
import mysql.connector
from datetime import datetime
import re  # Para expresiones regulares

# Configuración del log
log_file = "/var/www/django-palab/logs/exportar_csv.log"
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def exportar_datos_csv():
    ruta_csv = "/var/www/django-palab/datos_cache.csv"
    
    try:
        # 🔹 Conectar a la base de datos MySQL manualmente
        conn = mysql.connector.connect(
            host='158.69.26.160',
            user='admin',
            password='S3gur1d4d2025',
            database='data_wa'
        )
        cursor = conn.cursor()

        # 🔹 Ejecutar la consulta para obtener los datos
        cursor.execute("SELECT cliente, estado, municipio, group_name, number2, text_data, timestamp, received_timestamp FROM extraccion4")
        filas = cursor.fetchall()
        
        if not filas:
            logging.warning("⚠️ No se encontraron datos en la tabla 'extraccion4'.")
            return

        # 🔹 Filtrar duplicados usando un set con (text_data, received_timestamp)
        mensajes_filtrados = set()  
        filas_filtradas = []

        for fila in filas:
            cliente, estado, municipio, group_name, number2, text_data, timestamp, received_timestamp = fila
            


            # Verificar si el par (text_data, timestamp) ya fue procesado
            if (text_data, received_timestamp) not in mensajes_filtrados:
                mensajes_filtrados.add((text_data, received_timestamp))
                filas_filtradas.append(fila)

        if not filas_filtradas:
            logging.warning("⚠️ No se encontraron mensajes válidos después de aplicar los filtros.")
            return

        # 🔹 Guardar en CSV
        with open(ruta_csv, mode="w", encoding="utf-8", newline="") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(["cliente", "estado", "municipio", "group_name", "number2", "text_data", "timestamp", "received_timestamp"])
            escritor.writerows(filas_filtradas)

        mensaje = f"✅ CSV actualizado correctamente: {datetime.now()}"
        logging.info(mensaje)
        print(mensaje)

    except Exception as e:
        error_msg = f"❌ Error al exportar CSV: {str(e)}"
        logging.error(error_msg)
        print(error_msg)

    finally:
        cursor.close()
        conn.close()

# Ejecutar la función al correr el script
if __name__ == "__main__":
    exportar_datos_csv()
