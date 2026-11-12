# Gestor de Proyectos (Django) + Diagnóstico con IA

Aplicación para gestionar proyectos y tareas, con un módulo de **diagnóstico con IA**
(modelo XGBoost) al que solo acceden los doctores.

## Roles

| Rol | Cómo se crea | Qué puede hacer |
|-----|--------------|-----------------|
| **Admin** | `python manage.py createsuperuser` | Crea doctores (menú **Doctores**), administra grupos y asigna permisos (menú **Permisos**). |
| **Doctor** | Lo crea el admin en **Doctores** (o convierte a un usuario existente) | Entra a **Diagnóstico IA**: elige síntomas y ve el porcentaje por enfermedad. |
| **Usuario** | Registro público (`/registro/`) | Acceso **limitado**: no ve nada hasta que un admin le asigne permisos. |

Para dar acceso a un usuario sin hacerlo doctor: el admin va a **Permisos**, elige el grupo
`Usuario` (o cualquier otro) y marca *Usar el diagnóstico con IA* y/o los permisos de proyectos.

## Instalación

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate        # crea la tabla de consultas y los grupos Doctor / Usuario
python manage.py createsuperuser
python manage.py runserver
```

Abre http://127.0.0.1:8000/ — te redirigirá al login.

## Diagnóstico con IA

- Página: `/diagnostico/` (permiso `diagnostico.usar_ia`).
- Muestra los 131 síntomas del modelo **en español**, con buscador; el doctor marca los que
  quiera y recibe un recuadro con la probabilidad (%) de cada enfermedad (hasta 10, ≥ 0,5 %).
- Cada consulta queda guardada en el historial del doctor (solo él la ve).
- Es una herramienta de apoyo: no sustituye el criterio clínico.

Archivos del modelo en `diagnostico/ml/` (`disease_model.pkl`, `label_encoder.pkl`,
`symptom_list.pkl`). Se cargan con `pickle`: **solo coloques ahí archivos de tu confianza**.
Las traducciones al español están en `diagnostico/traducciones.py`.

## Estructura

- `gestor/` — proyectos y tareas
- `accounts/` — login, registro, grupos, permisos y gestión de doctores (`roles.py`)
- `diagnostico/` — módulo de IA (`ml_service.py`, `views.py`, `traducciones.py`, `ml/`)
- `media/` — imágenes subidas de proyectos

## Pruebas

```bash
python manage.py test
```
