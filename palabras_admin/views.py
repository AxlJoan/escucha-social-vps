from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from .models import Extraccion4
from .serializers import Extraccion4Serializer
from .filters import Extraccion4Filter
from django.shortcuts import render

class Extraccion4List(generics.ListAPIView):
    queryset = Extraccion4.objects.all()
    serializer_class = Extraccion4Serializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = Extraccion4Filter

def admin(request):
    return render(request,'admin.html')