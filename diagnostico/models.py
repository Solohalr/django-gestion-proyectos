from django.conf import settings
from django.db import models


class Consulta(models.Model):
    """Historial de consultas hechas por un doctor al modelo de IA.

    Además, esta clase define el permiso ``diagnostico.usar_ia``, que es el
    que realmente da acceso a la página del modelo.
    """

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consultas_ia',
    )
    sintomas = models.JSONField(default=list)    # claves de los síntomas elegidos
    resultados = models.JSONField(default=list)  # [{'nombre':..., 'porcentaje':...}]
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado']
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        default_permissions = ()  # solo el permiso personalizado de abajo
        permissions = [
            ('usar_ia', 'Puede usar el diagnóstico con IA'),
        ]

    def __str__(self):
        return f'Consulta de {self.doctor} ({self.creado:%Y-%m-%d %H:%M})'

    @property
    def principal(self):
        return self.resultados[0] if self.resultados else None
