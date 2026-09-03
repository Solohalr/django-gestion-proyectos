from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Proyecto, Tarea


# ─── PROYECTOS ───────────────────────────────────────────────

def lista_proyectos(request):
    proyectos = Proyecto.objects.all()
    return render(request, 'proyectos.html', {'proyectos': proyectos})


def proyecto_detalle(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    tareas = proyecto.tareas.all()
    return render(request, 'proyecto_detalle.html', {
        'proyecto': proyecto,
        'tareas': tareas,
    })


def proyecto_crear(request):
    error = None

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        duracion = request.POST.get('duracion', '').strip()

        if not nombre:
            error = 'El nombre del proyecto es obligatorio.'
        elif not duracion:
            error = 'La duración es obligatoria.'
        else:
            try:
                duracion_int = int(duracion)
                if duracion_int < 1:
                    error = 'La duración debe ser al menos 1 día.'
                else:
                    Proyecto.objects.create(
                        nombre=nombre,
                        descripcion=descripcion,
                        duracion=duracion_int
                    )
                    messages.success(request, f'Proyecto "{nombre}" creado correctamente.')
                    return redirect('lista_proyectos')
            except ValueError:
                error = 'La duración debe ser un número válido.'

    return render(request, 'proyecto_form.html', {
        'error': error,
        'valores': request.POST if request.method == 'POST' else {},
    })


def proyecto_eliminar(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)

    if request.method == 'POST':
        nombre = proyecto.nombre
        proyecto.delete()  # CASCADE elimina las tareas asociadas
        messages.success(request, f'Proyecto "{nombre}" y sus tareas eliminados.')
        return redirect('lista_proyectos')

    return render(request, 'proyecto_confirmar_eliminar.html', {
        'proyecto': proyecto,
    })


# ─── TAREAS ──────────────────────────────────────────────────

def tarea_crear(request, proyecto_pk):
    proyecto = get_object_or_404(Proyecto, pk=proyecto_pk)
    error = None

    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        prioridad = request.POST.get('prioridad', 'MEDIA')
        estado = request.POST.get('estado', 'PENDIENTE')

        if not titulo:
            error = 'El título de la tarea es obligatorio.'
        else:
            Tarea.objects.create(
                proyecto=proyecto,
                titulo=titulo,
                prioridad=prioridad,
                estado=estado
            )
            messages.success(request, f'Tarea "{titulo}" agregada.')
            return redirect('proyecto_detalle', pk=proyecto.pk)

    return render(request, 'tarea_form.html', {
        'proyecto': proyecto,
        'error': error,
        'prioridades': Tarea.PRIORIDAD_CHOICES,
        'estados': Tarea.ESTADO_CHOICES,
        'valores': request.POST if request.method == 'POST' else {},
    })


@require_POST
def tarea_completar(request, pk):
    tarea = get_object_or_404(Tarea, pk=pk)
    tarea.estado = 'COMPLETADA'
    tarea.save()
    messages.success(request, f'Tarea "{tarea.titulo}" marcada como completada.')
    return redirect('proyecto_detalle', pk=tarea.proyecto.pk)


def tarea_eliminar(request, pk):
    tarea = get_object_or_404(Tarea, pk=pk)
    proyecto_pk = tarea.proyecto.pk

    if request.method == 'POST':
        titulo = tarea.titulo
        tarea.delete()
        messages.success(request, f'Tarea "{titulo}" eliminada.')
        return redirect('proyecto_detalle', pk=proyecto_pk)

    return render(request, 'tarea_confirmar_eliminar.html', {
        'tarea': tarea,
    })
