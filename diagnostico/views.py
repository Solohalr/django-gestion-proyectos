import logging

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

from . import ml_service
from .models import Consulta
from .traducciones import nombre_sintoma

logger = logging.getLogger(__name__)


@login_required
@permission_required('diagnostico.usar_ia', raise_exception=True)
def diagnostico(request):
    seleccionados = []
    resultados = None
    error = None

    if request.method == 'POST':
        validos = set(ml_service.lista_sintomas())
        # Solo se aceptan claves que existan en el modelo (sin duplicados).
        seleccionados = [
            s for s in dict.fromkeys(request.POST.getlist('sintomas')) if s in validos
        ]

        if not seleccionados:
            error = 'Selecciona al menos un síntoma para analizar.'
        else:
            try:
                resultados = ml_service.predecir(seleccionados)
            except ModuleNotFoundError as exc:
                logger.exception('Falta una dependencia del modelo')
                error = (
                    f'Falta instalar una librería del modelo ({exc.name}). '
                    'Ejecuta: pip install -r requirements.txt'
                )
            except Exception:
                logger.exception('Error ejecutando el modelo de IA')
                error = 'No se pudo ejecutar el modelo. Revisa la consola del servidor.'
            else:
                Consulta.objects.create(
                    doctor=request.user,
                    sintomas=seleccionados,
                    resultados=resultados,
                )

    recientes = Consulta.objects.filter(doctor=request.user)[:5]
    for c in recientes:
        c.sintomas_es = [nombre_sintoma(s) for s in c.sintomas]

    return render(request, 'diagnostico.html', {
        'sintomas': ml_service.sintomas_para_formulario(),
        'seleccionados': seleccionados,
        'resultados': resultados,
        'error': error,
        'recientes': recientes,
    })
