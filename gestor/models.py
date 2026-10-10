from django.db import models


class Proyecto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, default='')
    duracion = models.PositiveIntegerField(help_text='Duración en días')
    imagen = models.ImageField(
        upload_to='proyectos/',
        default='proyectos/logo.png',
        blank=True,
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'

    def __str__(self):
        return self.nombre

    @property
    def total_tareas(self):
        return self.tareas.count()

    @property
    def tareas_completadas(self):
        return self.tareas.filter(estado='COMPLETADA').count()


class Tarea(models.Model):
    PRIORIDAD_CHOICES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
    ]
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROGRESO', 'En Progreso'),
        ('COMPLETADA', 'Completada'),
    ]

    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='tareas'
    )
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, default='')
    prioridad = models.CharField(
        max_length=10,
        choices=PRIORIDAD_CHOICES,
        default='MEDIA'
    )
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='PENDIENTE'
    )

    class Meta:
        ordering = ['estado', '-prioridad', 'id']
        verbose_name = 'Tarea'
        verbose_name_plural = 'Tareas'

    def __str__(self):
        return self.titulo

    @property
    def esta_completada(self):
        return self.estado == 'COMPLETADA'
