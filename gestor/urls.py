from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Proyectos
    path('proyectos/', views.lista_proyectos, name='lista_proyectos'),
    path('proyectos/nuevo/', views.proyecto_crear, name='proyecto_crear'),
    path('proyectos/<int:pk>/', views.proyecto_detalle, name='proyecto_detalle'),
    path('proyectos/<int:pk>/editar/', views.proyecto_editar, name='proyecto_editar'),
    path('proyectos/<int:pk>/eliminar/', views.proyecto_eliminar, name='proyecto_eliminar'),

    # Tareas
    path('proyectos/<int:proyecto_pk>/tareas/nueva/', views.tarea_crear, name='tarea_crear'),
    path('tareas/<int:pk>/completar/', views.tarea_completar, name='tarea_completar'),
    path('tareas/<int:pk>/avanzar/', views.avanzar_estado_tarea, name='avanzar_estado_tarea'),
    path('tareas/<int:pk>/eliminar/', views.tarea_eliminar, name='tarea_eliminar'),
]
