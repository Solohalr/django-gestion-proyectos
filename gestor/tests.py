from django.test import TestCase
from .models import Proyecto, Tarea


class ProyectoModelTest(TestCase):
    def test_crear_proyecto(self):
        p = Proyecto.objects.create(nombre='Test', descripcion='Desc', duracion=10)
        self.assertEqual(str(p), 'Test')
        self.assertEqual(p.total_tareas, 0)

    def test_cascade_delete(self):
        p = Proyecto.objects.create(nombre='Test', duracion=5)
        Tarea.objects.create(proyecto=p, titulo='Tarea 1')
        self.assertEqual(Tarea.objects.count(), 1)
        p.delete()
        self.assertEqual(Tarea.objects.count(), 0)
