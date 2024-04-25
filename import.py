import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nube_palabras.settings')
django.setup()

from palabras_admin.models import CountryCode, AreaCodeMX  # Modificado aquí

# Aquí pones tus funciones de importación...
def import_country_codes(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('codigos de pais'):
                CountryCode.objects.get_or_create(code=line)

def import_area_codes_mx(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                AreaCodeMX.objects.get_or_create(code=line)

if __name__ == '__main__':
    import_country_codes('codes.txt')
    import_area_codes_mx('CodesMX.txt')
