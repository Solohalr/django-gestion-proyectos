from django.contrib import admin
from .models import Proyecto, Tarea


class TareaInline(admin.TabularInline):
    model = Tarea
    extra = 0


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'duracion', 'total_tareas')
    search_fields = ('nombre',)
    inlines = [TareaInline]

    def total_tareas(self, obj):
        return obj.tareas.count()
    total_tareas.short_description = 'Tareas'


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'proyecto', 'prioridad', 'estado')
    list_filter = ('estado', 'prioridad')
    search_fields = ('titulo',)
