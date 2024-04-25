"""
URL configuration for nube_palabras project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path,include
from rest_framework import routers
from palabras_admin import views
from .views import Extraccion4List,Vista_Analisis,ClassifyNumberView

urlpatterns = [
    path('login/', views.login, name='login'),  # Correcto
    path('api/extraccion4/', Extraccion4List.as_view(), name='extraccion4-list'),
    path('nube_admin/',views.admin,name='nube_admin'),
    path('api/compartir/', views.compartir, name='compartir'),
    path('ver_compartido/<uuid:uuid>/', views.ver_compartido, name='ver_compartido'),
    path('analisis/', Vista_Analisis.as_view(), name='extraccion4_list'),
    path('classify/<int:id>/', ClassifyNumberView.as_view(), name='classify-number'),
    path('estadisticas/',views.statistics_view,name='estadisticas'),

]
