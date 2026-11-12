from unittest import mock

import numpy as np
from django.contrib.auth.models import Group, Permission, User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from accounts.roles import GRUPO_DOCTOR, GRUPO_USUARIO
from . import ml_service
from .models import Consulta
from .traducciones import ENFERMEDADES_ES, SINTOMAS_ES


class TraduccionesTests(SimpleTestCase):
    def test_todos_los_sintomas_tienen_traduccion(self):
        faltan = [s for s in ml_service.lista_sintomas() if s not in SINTOMAS_ES]
        self.assertEqual(faltan, [])
        self.assertEqual(len(ml_service.lista_sintomas()), 131)

    def test_todas_las_enfermedades_tienen_traduccion(self):
        encoder = ml_service._cargar_pickle('label_encoder.pkl')
        faltan = [c for c in encoder.classes_ if c not in ENFERMEDADES_ES]
        self.assertEqual(faltan, [])
        self.assertEqual(len(encoder.classes_), 41)

    def test_formulario_ordenado_y_en_espanol(self):
        nombres = [n for _, n in ml_service.sintomas_para_formulario()]
        self.assertIn('Dolor de cabeza', nombres)
        self.assertNotIn('headache', nombres)


class ServicioModeloTests(SimpleTestCase):
    def test_vector_y_resultados(self):
        """Verifica la codificación 0/1 y el orden/filtrado de resultados."""
        sintomas = ml_service.lista_sintomas()
        capturado = {}

        class ModeloFalso:
            classes_ = np.arange(41)

            def predict_proba(self, x):
                capturado['x'] = x
                p = np.full(41, 0.001)
                p[10] = 0.7   # common_cold
                p[15] = 0.25  # fungal_infection
                p = p / p.sum()
                return np.array([p])

        encoder = ml_service._cargar_pickle('label_encoder.pkl')
        with mock.patch.object(ml_service, '_cargar_modelo',
                               return_value=(ModeloFalso(), encoder)):
            res = ml_service.predecir(['cough', 'headache', 'no_existe'])

        x = capturado['x']
        self.assertEqual(x.shape, (1, 131))
        self.assertEqual(x.sum(), 2)
        self.assertEqual(x[0, sintomas.index('cough')], 1)
        self.assertEqual(x[0, sintomas.index('headache')], 1)
        self.assertEqual(res[0]['clave'], 'common_cold')
        self.assertEqual(res[0]['nombre'], 'Resfriado común')
        self.assertEqual(res[1]['clave'], 'fungal_infection')
        self.assertTrue(all(r['porcentaje'] >= 0.5 for r in res))
        self.assertEqual([r['porcentaje'] for r in res],
                         sorted((r['porcentaje'] for r in res), reverse=True))


RESULTADO_FALSO = [
    {'clave': 'common_cold', 'nombre': 'Resfriado común', 'porcentaje': 80.0},
    {'clave': 'allergy', 'nombre': 'Alergia', 'porcentaje': 15.5},
]


class RolesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser('admin', 'a@x.com', 'AdminPass123!')

    def test_grupos_creados_tras_migrar(self):
        doctor = Group.objects.get(name=GRUPO_DOCTOR)
        self.assertTrue(doctor.permissions.filter(codename='usar_ia').exists())
        usuario = Group.objects.get(name=GRUPO_USUARIO)
        self.assertEqual(usuario.permissions.count(), 0)

    def test_registro_publico_crea_usuario_sin_permisos(self):
        r = self.client.post(reverse('registro'), {
            'username': 'pepe', 'password1': 'ClaveSegura123!', 'password2': 'ClaveSegura123!',
        })
        self.assertRedirects(r, reverse('home'))
        pepe = User.objects.get(username='pepe')
        self.assertFalse(pepe.is_staff)
        self.assertTrue(pepe.groups.filter(name=GRUPO_USUARIO).exists())
        self.assertFalse(pepe.has_perm('diagnostico.usar_ia'))
        # home muestra el aviso de acceso limitado
        self.assertContains(self.client.get(reverse('home')), 'Acceso limitado')
        # y la IA está bloqueada con una página amigable
        r = self.client.get(reverse('diagnostico'))
        self.assertEqual(r.status_code, 403)
        self.assertContains(r, 'Acceso limitado', status_code=403)

    def test_solo_admin_gestiona_doctores(self):
        User.objects.create_user('normal', password='ClaveSegura123!')
        self.client.login(username='normal', password='ClaveSegura123!')
        for nombre in ('doctores', 'crear_doctor'):
            r = self.client.get(reverse(nombre))
            self.assertEqual(r.status_code, 302)
            self.assertIn('login', r['Location'])
        r = self.client.post(reverse('crear_doctor'), {'username': 'hack', 'password1': 'x', 'password2': 'x'})
        self.assertFalse(User.objects.filter(username='hack').exists())

    def test_admin_crea_doctor_y_este_usa_la_ia(self):
        self.client.login(username='admin', password='AdminPass123!')
        self.assertEqual(self.client.get(reverse('doctores')).status_code, 200)
        r = self.client.post(reverse('crear_doctor'), {
            'username': 'dra_lopez', 'first_name': 'Ana', 'last_name': 'López',
            'email': 'ana@x.com', 'password1': 'ClaveSegura123!', 'password2': 'ClaveSegura123!',
        })
        self.assertRedirects(r, reverse('doctores'))
        doc = User.objects.get(username='dra_lopez')
        self.assertFalse(doc.is_staff)
        self.assertTrue(doc.has_perm('diagnostico.usar_ia'))

        self.client.logout()
        self.client.login(username='dra_lopez', password='ClaveSegura123!')
        r = self.client.get(reverse('diagnostico'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Dolor de cabeza')
        self.assertContains(r, 'Falta de aire')
        self.assertNotContains(r, 'value="headache" data-nombre="headache"')
        # un doctor no puede entrar a la gestión de doctores
        self.assertEqual(self.client.get(reverse('doctores')).status_code, 302)

    def test_crear_doctor_valida_datos(self):
        self.client.login(username='admin', password='AdminPass123!')
        r = self.client.post(reverse('crear_doctor'), {
            'username': 'admin', 'password1': 'abc', 'password2': 'distinta',
        })
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'ya está en uso')
        self.assertContains(r, 'no coinciden')
        r = self.client.post(reverse('crear_doctor'), {
            'username': 'debil', 'password1': '12345678', 'password2': '12345678',
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username='debil').exists())

    def test_promover_y_quitar_doctor(self):
        u = User.objects.create_user('juan', password='ClaveSegura123!')
        self.client.login(username='admin', password='AdminPass123!')
        self.client.post(reverse('agregar_doctor', args=[u.id]))
        self.assertTrue(User.objects.get(pk=u.pk).has_perm('diagnostico.usar_ia'))
        self.client.post(reverse('quitar_doctor', args=[u.id]))
        u = User.objects.get(pk=u.pk)
        self.assertFalse(u.has_perm('diagnostico.usar_ia'))
        self.assertTrue(u.groups.filter(name=GRUPO_USUARIO).exists())

    def test_admin_puede_dar_permiso_de_ia_al_grupo_usuario(self):
        """Los usuarios son limitados hasta que el admin les da el permiso."""
        u = User.objects.create_user('maria', password='ClaveSegura123!')
        u.groups.add(Group.objects.get(name=GRUPO_USUARIO))
        self.client.login(username='maria', password='ClaveSegura123!')
        self.assertEqual(self.client.get(reverse('diagnostico')).status_code, 403)
        self.client.logout()

        self.client.login(username='admin', password='AdminPass123!')
        grupo = Group.objects.get(name=GRUPO_USUARIO)
        perm = Permission.objects.get(codename='usar_ia')
        r = self.client.post(reverse('permisos'), {'grupo': grupo.id, 'permisos': [perm.id]})
        self.assertEqual(r.status_code, 302)
        # la página de permisos muestra el permiso en español
        self.assertContains(self.client.get(reverse('permisos') + f'?grupo={grupo.id}'),
                            'Usar el diagnóstico con IA')
        self.client.logout()

        self.client.login(username='maria', password='ClaveSegura123!')
        self.assertEqual(self.client.get(reverse('diagnostico')).status_code, 200)

    def test_nav_segun_rol(self):
        self.client.login(username='admin', password='AdminPass123!')
        html = self.client.get(reverse('home')).content.decode()
        self.assertIn('Doctores', html)
        self.assertIn('Grupos', html)
        self.client.logout()
        u = User.objects.create_user('limitado', password='ClaveSegura123!')
        self.client.login(username='limitado', password='ClaveSegura123!')
        html = self.client.get(reverse('home')).content.decode()
        self.assertNotIn('Diagnóstico IA', html)
        self.assertNotIn('>\n                    Proyectos', html)
        self.assertNotIn('Doctores', html)


class VistaDiagnosticoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.doc = User.objects.create_user('doc', password='ClaveSegura123!')
        cls.doc.groups.add(Group.objects.get(name=GRUPO_DOCTOR))
        cls.otro = User.objects.create_user('otro', password='ClaveSegura123!')
        cls.otro.groups.add(Group.objects.get(name=GRUPO_DOCTOR))

    def setUp(self):
        self.client.login(username='doc', password='ClaveSegura123!')

    def test_anonimo_va_al_login(self):
        self.client.logout()
        r = self.client.get(reverse('diagnostico'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login/', r['Location'])

    @mock.patch('diagnostico.views.ml_service.predecir', return_value=RESULTADO_FALSO)
    def test_post_muestra_porcentajes_y_guarda_historial(self, predecir):
        r = self.client.post(reverse('diagnostico'), {
            'sintomas': ['cough', 'headache', 'cough', 'inventado'],
        })
        self.assertEqual(r.status_code, 200)
        predecir.assert_called_once_with(['cough', 'headache'])  # sin duplicados ni inválidos
        self.assertContains(r, 'Resultados del modelo')
        self.assertContains(r, 'Resfriado común')
        self.assertContains(r, '80,0')
        self.assertContains(r, 'width: 80.0%')
        # los síntomas elegidos siguen marcados
        self.assertContains(r, 'value="cough" data-nombre="Tos"\n                               checked')
        c = Consulta.objects.get()
        self.assertEqual(c.doctor, self.doc)
        self.assertEqual(c.sintomas, ['cough', 'headache'])

    def test_sin_sintomas_muestra_error(self):
        r = self.client.post(reverse('diagnostico'), {})
        self.assertContains(r, 'Selecciona al menos un síntoma')
        self.assertNotContains(r, 'Resultados del modelo')
        self.assertEqual(Consulta.objects.count(), 0)

    @mock.patch('diagnostico.views.ml_service.predecir',
                side_effect=ModuleNotFoundError("No module named 'xgboost'", name='xgboost'))
    def test_falta_xgboost_da_mensaje_claro(self, _):
        with self.assertLogs('diagnostico.views', level='ERROR'):
            r = self.client.post(reverse('diagnostico'), {'sintomas': ['cough']})
        self.assertContains(r, 'pip install -r requirements.txt')
        self.assertEqual(Consulta.objects.count(), 0)

    @mock.patch('diagnostico.views.ml_service.predecir', side_effect=RuntimeError('boom'))
    def test_error_generico_no_rompe_la_pagina(self, _):
        with self.assertLogs('diagnostico.views', level='ERROR'):
            r = self.client.post(reverse('diagnostico'), {'sintomas': ['cough']})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'No se pudo ejecutar el modelo')

    @mock.patch('diagnostico.views.ml_service.predecir', return_value=RESULTADO_FALSO)
    def test_historial_es_privado(self, _):
        self.client.post(reverse('diagnostico'), {'sintomas': ['fatigue']})
        self.client.logout()
        self.client.login(username='otro', password='ClaveSegura123!')
        r = self.client.get(reverse('diagnostico'))
        self.assertNotContains(r, 'Mis consultas recientes')
