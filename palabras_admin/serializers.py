from rest_framework import serializers
from .models import Extraccion4,DatosCompartidos

class Extraccion4Serializer(serializers.ModelSerializer):
    class Meta:
        model = Extraccion4
        fields = '__all__'  # O especifica campos individuales

class DatosCompartidosSerializer(serializers.ModelSerializer):
    campo_calculado = serializers.SerializerMethodField()

    class Meta:
        model = DatosCompartidos
        fields = '__all__'  # Asegúrate de incluir tu campo_calculado si estás especificando los campos manualmente
