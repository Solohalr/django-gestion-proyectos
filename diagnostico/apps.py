from django.apps import AppConfig
from django.db.models.signals import post_migrate


def crear_roles(sender, **kwargs):
    """Tras migrar, asegura que existan los grupos Doctor y Usuario."""
    from accounts.roles import obtener_grupo_doctor, obtener_grupo_usuario

    obtener_grupo_doctor()
    obtener_grupo_usuario()


class DiagnosticoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'diagnostico'
    verbose_name = 'Diagnóstico con IA'

    def ready(self):
        # Debe ir después de django.contrib.auth en INSTALLED_APPS para que el
        # permiso "usar_ia" ya exista cuando se crea el grupo Doctor.
        post_migrate.connect(crear_roles, sender=self)
