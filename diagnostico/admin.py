from django.contrib import admin
from .models import Consulta


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'creado')
    list_filter = ('doctor',)
    readonly_fields = ('doctor', 'sintomas', 'resultados', 'creado')
