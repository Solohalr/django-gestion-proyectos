"""Roles del sistema.

  - Admin   -> cuenta con is_staff / superusuario (se crea con createsuperuser).
              Es quien crea doctores y asigna permisos.
  - Doctor  -> grupo "Doctor". Recibe el permiso diagnostico.usar_ia.
  - Usuario -> grupo "Usuario" (registro público). Sin permisos hasta que un
              admin se los asigne desde la pantalla "Permisos".
"""
from django.contrib.auth.models import Group, Permission

GRUPO_DOCTOR = 'Doctor'
GRUPO_USUARIO = 'Usuario'


def obtener_grupo_doctor():
    """Devuelve el grupo Doctor; si no existe lo crea con el permiso de la IA."""
    grupo, creado = Group.objects.get_or_create(name=GRUPO_DOCTOR)
    if creado:
        permiso = Permission.objects.filter(
            content_type__app_label='diagnostico', codename='usar_ia'
        ).first()
        if permiso:
            grupo.permissions.add(permiso)
    return grupo


def obtener_grupo_usuario():
    """Devuelve el grupo Usuario (sin permisos por defecto)."""
    return Group.objects.get_or_create(name=GRUPO_USUARIO)[0]
