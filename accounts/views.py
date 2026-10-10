from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages


def es_admin(user):
    """Solo usuarios autenticados y con is_staff pueden acceder."""
    return user.is_authenticated and user.is_staff


def registro(request):
    datos = {}
    errors = []

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        datos = request.POST

        if not username:
            errors.append('El nombre de usuario es obligatorio.')
        if not password1:
            errors.append('La contraseña es obligatoria.')
        if password1 != password2:
            errors.append('Las contraseñas no coinciden.')
        if username and User.objects.filter(username=username).exists():
            errors.append('El nombre de usuario ya está en uso.')
        if email and User.objects.filter(email=email).exists():
            errors.append('El correo electrónico ya está en uso.')

        if not errors:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
            )
            login(request, user)
            messages.success(request, f'Bienvenido, {username}.')
            return redirect('home')

    return render(request, 'registro.html', {'datos': datos, 'errors': errors})


@user_passes_test(es_admin)
def grupos(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre_grupo', '').strip()
        if nombre:
            if Group.objects.filter(name=nombre).exists():
                messages.error(request, f'Ya existe un grupo llamado "{nombre}".')
            else:
                Group.objects.create(name=nombre)
                messages.success(request, f'Grupo "{nombre}" creado.')
            return redirect('grupos')

    grupos_list = Group.objects.all().order_by('name')
    return render(request, 'grupos.html', {'grupos': grupos_list})


@user_passes_test(es_admin)
def eliminar_grupo(request, id_grupo):
    if request.method == 'POST':
        grupo = get_object_or_404(Group, id=id_grupo)
        nombre = grupo.name
        grupo.delete()
        messages.success(request, f'Grupo "{nombre}" eliminado.')
    return redirect('grupos')


def dar_miembros(grupo):
    return grupo.user_set.all().order_by('username')


def dar_no_miembros(grupo):
    miembros_ids = grupo.user_set.values_list('id', flat=True)
    return User.objects.exclude(id__in=miembros_ids).order_by('username')


@user_passes_test(es_admin)
def editar_grupo(request, id_grupo):
    grupo = get_object_or_404(Group, id=id_grupo)

    if request.method == 'POST':
        nuevo_nombre = request.POST.get('name', '').strip()
        if nuevo_nombre:
            grupo.name = nuevo_nombre
            grupo.save()
            messages.success(request, 'Nombre del grupo actualizado.')
            return redirect('grupos')

    return render(request, 'editar_grupo.html', {
        'grupo': grupo,
        'miembros': dar_miembros(grupo),
        'no_miembros': dar_no_miembros(grupo),
    })


@user_passes_test(es_admin)
def agregar_usuario_grupo(request, id_grupo):
    grupo = get_object_or_404(Group, id=id_grupo)
    if request.method == 'POST':
        id_user = request.POST.get('id_user')
        if id_user:
            user = get_object_or_404(User, id=id_user)
            grupo.user_set.add(user)
            messages.success(request, f'Usuario "{user.username}" agregado al grupo.')
    return redirect('editar_grupo', id_grupo=grupo.id)


@user_passes_test(es_admin)
def eliminar_usuario_grupo(request, id_grupo):
    grupo = get_object_or_404(Group, id=id_grupo)
    if request.method == 'POST':
        id_user = request.POST.get('id_user')
        if id_user:
            user = get_object_or_404(User, id=id_user)
            grupo.user_set.remove(user)
            messages.success(request, f'Usuario "{user.username}" eliminado del grupo.')
    return redirect('editar_grupo', id_grupo=grupo.id)


# Traducciones y descripciones de permisos (español)
PERMISOS_ES = {
    # Gestor de proyectos (los más importantes)
    'gestor.add_proyecto': ('Crear proyectos', 'Permite crear nuevos proyectos.'),
    'gestor.change_proyecto': ('Editar proyectos', 'Permite modificar nombre, descripción, duración e imagen de un proyecto.'),
    'gestor.delete_proyecto': ('Eliminar proyectos', 'Permite borrar proyectos y sus tareas asociadas.'),
    'gestor.view_proyecto': ('Ver proyectos', 'Permite ver la lista y el detalle de los proyectos.'),
    'gestor.add_tarea': ('Crear tareas', 'Permite añadir tareas a un proyecto.'),
    'gestor.change_tarea': ('Editar / avanzar tareas', 'Permite cambiar el estado de una tarea (Pendiente → En progreso → Completada).'),
    'gestor.delete_tarea': ('Eliminar tareas', 'Permite borrar tareas de un proyecto.'),
    'gestor.view_tarea': ('Ver tareas', 'Permite ver las tareas dentro de un proyecto.'),
    # Auth
    'auth.add_user': ('Crear usuarios', 'Permite crear nuevos usuarios del sistema.'),
    'auth.change_user': ('Editar usuarios', 'Permite modificar datos de usuarios.'),
    'auth.delete_user': ('Eliminar usuarios', 'Permite borrar usuarios.'),
    'auth.view_user': ('Ver usuarios', 'Permite ver la lista de usuarios.'),
    'auth.add_group': ('Crear grupos', 'Permite crear grupos de usuarios.'),
    'auth.change_group': ('Editar grupos', 'Permite modificar grupos y sus miembros.'),
    'auth.delete_group': ('Eliminar grupos', 'Permite borrar grupos.'),
    'auth.view_group': ('Ver grupos', 'Permite ver los grupos existentes.'),
    'auth.add_permission': ('Crear permisos', 'Permite crear permisos personalizados.'),
    'auth.change_permission': ('Editar permisos', 'Permite modificar permisos.'),
    'auth.delete_permission': ('Eliminar permisos', 'Permite borrar permisos.'),
    'auth.view_permission': ('Ver permisos', 'Permite ver la lista de permisos.'),
    # Admin
    'admin.add_logentry': ('Crear entradas de log', 'Permite crear registros en el historial del admin.'),
    'admin.change_logentry': ('Editar entradas de log', 'Permite modificar el historial del admin.'),
    'admin.delete_logentry': ('Eliminar entradas de log', 'Permite borrar registros del historial.'),
    'admin.view_logentry': ('Ver entradas de log', 'Permite ver el historial de acciones del admin.'),
    # Sessions
    'sessions.add_session': ('Crear sesiones', 'Permite crear sesiones de usuario.'),
    'sessions.change_session': ('Editar sesiones', 'Permite modificar sesiones.'),
    'sessions.delete_session': ('Eliminar sesiones', 'Permite cerrar/borrar sesiones.'),
    'sessions.view_session': ('Ver sesiones', 'Permite ver las sesiones activas.'),
    # Contenttypes
    'contenttypes.add_contenttype': ('Crear tipos de contenido', 'Permiso interno de Django.'),
    'contenttypes.change_contenttype': ('Editar tipos de contenido', 'Permiso interno de Django.'),
    'contenttypes.delete_contenttype': ('Eliminar tipos de contenido', 'Permiso interno de Django.'),
    'contenttypes.view_contenttype': ('Ver tipos de contenido', 'Permiso interno de Django.'),
}


def traducir_permiso(permiso):
    """Devuelve (titulo_es, descripcion) para un Permission de Django."""
    key = f"{permiso.content_type.app_label}.{permiso.codename}"
    if key in PERMISOS_ES:
        return PERMISOS_ES[key]
    # Fallback genérico en español
    accion = {
        'add': 'Crear',
        'change': 'Editar',
        'delete': 'Eliminar',
        'view': 'Ver',
    }.get(permiso.codename.split('_')[0], permiso.codename)
    modelo = permiso.codename.split('_', 1)[-1].replace('_', ' ')
    titulo = f"{accion} {modelo}"
    return (titulo, permiso.name)


@user_passes_test(es_admin)
def permisos(request):
    permisos_qs = Permission.objects.select_related('content_type').order_by(
        'content_type__app_label', 'content_type__model', 'codename'
    )
    grupos_qs = Group.objects.all().order_by('name')

    grupo_id = request.POST.get('grupo') or request.GET.get('grupo')

    if grupo_id:
        grupo = get_object_or_404(Group, id=grupo_id)
    else:
        grupo = grupos_qs.first()

    if request.method == 'POST' and grupo:
        permisos_ids = request.POST.getlist('permisos')
        grupo.permissions.set(permisos_ids)
        messages.success(request, f'Permisos del grupo "{grupo.name}" actualizados.')
        return redirect(f"{reverse('permisos')}?grupo={grupo.id}")

    permisos_grupo = set()
    if grupo:
        permisos_grupo = set(grupo.permissions.values_list('id', flat=True))

    # Lista con título y descripción en español
    permisos_lista = []
    for p in permisos_qs:
        titulo, desc = traducir_permiso(p)
        permisos_lista.append({
            'id': p.id,
            'titulo': titulo,
            'descripcion': desc,
            'codename': f"{p.content_type.app_label}.{p.codename}",
            'app': p.content_type.app_label,
        })

    return render(request, 'permisos.html', {
        'permisos': permisos_lista,
        'grupos': grupos_qs,
        'grupo': grupo,
        'permisos_grupo': permisos_grupo,
    })
