from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from .models import Proyecto, Tarea


# ─── HOME ────────────────────────────────────────────────────

@login_required
def home(request):
    total_proyectos = Proyecto.objects.count()
    total_tareas = Tarea.objects.count()
    tareas_completadas = Tarea.objects.filter(estado='COMPLETADA').count()
    return render(request, 'home.html', {
        'total_proyectos': total_proyectos,
        'total_tareas': total_tareas,
        'tareas_completadas': tareas_completadas,
    })


# ─── PROYECTOS ───────────────────────────────────────────────

@login_required
@permission_required('gestor.view_proyecto', raise_exception=True)
def lista_proyectos(request):
    proyectos = Proyecto.objects.all()
    return render(request, 'proyectos.html', {'proyectos': proyectos})


@login_required
@permission_required('gestor.view_proyecto', raise_exception=True)
def proyecto_detalle(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    tareas = proyecto.tareas.all()
    return render(request, 'proyecto_detalle.html', {
        'proyecto': proyecto,
        'tareas': tareas,
    })


@login_required
@permission_required('gestor.add_proyecto', raise_exception=True)
def proyecto_crear(request):
    error = None

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        duracion = request.POST.get('duracion', '').strip()
        imagen = request.FILES.get('imagen')

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
                    proyecto = Proyecto(
                        nombre=nombre,
                        descripcion=descripcion,
                        duracion=duracion_int,
                    )
                    if imagen:
                        proyecto.imagen = imagen
                    proyecto.save()
                    messages.success(request, f'Proyecto "{nombre}" creado correctamente.')
                    return redirect('lista_proyectos')
            except ValueError:
                error = 'La duración debe ser un número válido.'

    return render(request, 'proyecto_form.html', {
        'error': error,
        'valores': request.POST if request.method == 'POST' else {},
        'modo': 'crear',
    })


@login_required
@permission_required('gestor.change_proyecto', raise_exception=True)
def proyecto_editar(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)
    error = None

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        duracion = request.POST.get('duracion', '').strip()
        imagen = request.FILES.get('imagen')

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
                    proyecto.nombre = nombre
                    proyecto.descripcion = descripcion
                    proyecto.duracion = duracion_int
                    if imagen:
                        proyecto.imagen = imagen
                    proyecto.save()
                    messages.success(request, f'Proyecto "{nombre}" actualizado.')
                    return redirect('proyecto_detalle', pk=proyecto.pk)
            except ValueError:
                error = 'La duración debe ser un número válido.'

    return render(request, 'proyecto_form.html', {
        'error': error,
        'proyecto': proyecto,
        'valores': {
            'nombre': proyecto.nombre,
            'descripcion': proyecto.descripcion,
            'duracion': proyecto.duracion,
        },
        'modo': 'editar',
    })


@login_required
@permission_required('gestor.delete_proyecto', raise_exception=True)
def proyecto_eliminar(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)

    if request.method == 'POST':
        nombre = proyecto.nombre
        proyecto.delete()
        messages.success(request, f'Proyecto "{nombre}" y sus tareas eliminados.')
        return redirect('lista_proyectos')

    return render(request, 'proyecto_confirmar_eliminar.html', {
        'proyecto': proyecto,
    })


# ─── TAREAS ──────────────────────────────────────────────────

@login_required
@permission_required('gestor.add_tarea', raise_exception=True)
def tarea_crear(request, proyecto_pk):
    proyecto = get_object_or_404(Proyecto, pk=proyecto_pk)
    error = None

    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        prioridad = request.POST.get('prioridad', 'MEDIA')
        estado = request.POST.get('estado', 'PENDIENTE')

        if not titulo:
            error = 'El título de la tarea es obligatorio.'
        else:
            Tarea.objects.create(
                proyecto=proyecto,
                titulo=titulo,
                descripcion=descripcion,
                prioridad=prioridad,
                estado=estado,
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


@login_required
@require_POST
@permission_required('gestor.change_tarea', raise_exception=True)
def tarea_completar(request, pk):
    tarea = get_object_or_404(Tarea, pk=pk)
    tarea.estado = 'COMPLETADA'
    tarea.save()
    messages.success(request, f'Tarea "{tarea.titulo}" marcada como completada.')
    return redirect('proyecto_detalle', pk=tarea.proyecto.pk)


@login_required
@require_POST
@permission_required('gestor.change_tarea', raise_exception=True)
def avanzar_estado_tarea(request, pk):
    tarea = get_object_or_404(Tarea, pk=pk)
    if tarea.estado == 'PENDIENTE':
        tarea.estado = 'EN_PROGRESO'
        mensaje = f'Tarea "{tarea.titulo}" ahora está en progreso.'
    elif tarea.estado == 'EN_PROGRESO':
        tarea.estado = 'COMPLETADA'
        mensaje = f'Tarea "{tarea.titulo}" marcada como completada.'
    else:
        mensaje = f'Tarea "{tarea.titulo}" ya está completada.'
        messages.info(request, mensaje)
        return redirect('proyecto_detalle', pk=tarea.proyecto.pk)

    tarea.save()
    messages.success(request, mensaje)
    return redirect('proyecto_detalle', pk=tarea.proyecto.pk)


@login_required
@permission_required('gestor.delete_tarea', raise_exception=True)
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
