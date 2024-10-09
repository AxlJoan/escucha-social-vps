from rest_framework import serializers
from .models import Extraccion4,DatosCompartidos

class Extraccion4Serializer(serializers.ModelSerializer):
    class Meta:
        model = Extraccion4
        fields = ['text_data', 'cliente', 'estado', 'municipio',"group_name"]  # Especifica campos individuales aquí


class DatosCompartidosSerializer(serializers.ModelSerializer):
    campo_calculado = serializers.SerializerMethodField()

    class Meta:
        model = DatosCompartidos
        fields = "__all__" # Asegúrate de incluir tu campo_calculado si estás especificando los campos manualmente
