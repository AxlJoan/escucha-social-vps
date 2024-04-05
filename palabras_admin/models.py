# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
import uuid
from django.db import models
from .roles import ADMIN_ROLE, VIEWER 
from django.contrib.auth.models import User
from django.conf import settings

class Extraccion(models.Model):
    chat_row_id = models.IntegerField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)
    received_timestamp = models.DateTimeField(blank=True, null=True)
    text_data = models.TextField(blank=True, null=True)
    from_me = models.IntegerField(blank=True, null=True)
    number = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    verified_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    cliente = models.CharField(max_length=255, blank=True, null=True)
    estado = models.CharField(max_length=255, blank=True, null=True)
    municipio = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'extraccion'


class Extraccion2(models.Model):
    chat_row_id = models.IntegerField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)
    received_timestamp = models.DateTimeField(blank=True, null=True)
    text_data = models.TextField(blank=True, null=True)
    from_me = models.IntegerField(blank=True, null=True)
    number = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    verified_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    cliente = models.CharField(max_length=255, blank=True, null=True)
    estado = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'extraccion2'


class Extraccion3(models.Model):
    chat_row_id = models.IntegerField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)
    received_timestamp = models.DateTimeField(blank=True, null=True)
    text_data = models.TextField(blank=True, null=True)
    from_me = models.IntegerField(blank=True, null=True)
    number = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    verified_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    cliente = models.CharField(max_length=255, blank=True, null=True)
    estado = models.CharField(max_length=255, blank=True, null=True)
    municipio = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'extraccion3'


class Extraccion4(models.Model):
    chat_row_id = models.IntegerField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)
    received_timestamp = models.DateTimeField(blank=True, null=True)
    text_data = models.TextField(blank=True, null=True)
    from_me = models.IntegerField(blank=True, null=True)
    number = models.CharField(max_length=255, blank=True, null=True, db_index=True)  # Individual field index
    number2 = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    verified_name = models.CharField(max_length=255, blank=True, null=True)
    server = models.CharField(max_length=255, blank=True, null=True)
    device = models.CharField(max_length=255, blank=True, null=True)
    group_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    cliente = models.CharField(max_length=255, blank=True, null=True, db_index=True)  # Individual field index
    estado = models.CharField(max_length=255, blank=True, null=True, db_index=True)  # Individual field index
    municipio = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'extraccion4'
        indexes = [
            models.Index(fields=['number', 'cliente'], name='number_cliente_idx'),  # Composite index
            models.Index(fields=['estado', 'municipio'], name='estado_municipio_idx'),  # Composite index
        ]


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    role = models.CharField(max_length=50, choices=[
        (ADMIN_ROLE, 'Admin'),
        (VIEWER, 'visualizador'),
    ])
    def __str__(self):
        return self.user.username

class DatosCompartidos(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    datos = models.JSONField()
    creado_en = models.DateTimeField(auto_now_add=True)
    identificador_unico = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    # Agrega más campos según sea necesario
    
