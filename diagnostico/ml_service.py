"""Carga y uso del modelo de IA (XGBoost) que predice la enfermedad.

Archivos en ``diagnostico/ml/``:
  - disease_model.pkl  -> XGBClassifier entrenado
  - label_encoder.pkl  -> LabelEncoder (índice de clase -> nombre de enfermedad)
  - symptom_list.pkl   -> lista ordenada de síntomas (columnas del modelo)

IMPORTANTE: los .pkl se cargan con ``pickle``, que puede ejecutar código al
cargarse. Solo coloques ahí archivos de tu confianza.
"""
import pickle
import threading
import unicodedata
from pathlib import Path

from .traducciones import nombre_enfermedad, nombre_sintoma

ML_DIR = Path(__file__).resolve().parent / 'ml'

_lock = threading.Lock()
_sintomas = None
_modelo_cache = None


def _cargar_pickle(nombre):
    with open(ML_DIR / nombre, 'rb') as f:
        return pickle.load(f)


def _quitar_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()


def lista_sintomas():
    """Claves de síntomas en el orden exacto que espera el modelo."""
    global _sintomas
    if _sintomas is None:
        with _lock:
            if _sintomas is None:
                _sintomas = list(_cargar_pickle('symptom_list.pkl'))
    return _sintomas


def sintomas_para_formulario():
    """[(clave, nombre_es)] ordenado alfabéticamente en español."""
    items = [(clave, nombre_sintoma(clave)) for clave in lista_sintomas()]
    return sorted(items, key=lambda it: _quitar_acentos(it[1]))


def _cargar_modelo():
    """Devuelve (modelo, encoder), cargándolos solo la primera vez."""
    global _modelo_cache
    if _modelo_cache is None:
        with _lock:
            if _modelo_cache is None:
                modelo = _cargar_pickle('disease_model.pkl')
                encoder = _cargar_pickle('label_encoder.pkl')
                esperado = getattr(modelo, 'n_features_in_', None)
                if esperado is not None and esperado != len(lista_sintomas()):
                    raise RuntimeError(
                        f'El modelo espera {esperado} síntomas pero symptom_list.pkl '
                        f'tiene {len(lista_sintomas())}.'
                    )
                _modelo_cache = (modelo, encoder)
    return _modelo_cache


def predecir(seleccionados, maximo=10, minimo_pct=0.5):
    """Calcula la probabilidad de cada enfermedad para los síntomas dados.

    Devuelve una lista ordenada de mayor a menor:
        [{'clave', 'nombre', 'porcentaje'}, ...]
    Solo incluye enfermedades con al menos ``minimo_pct`` % (siempre al
    menos la más probable) y como máximo ``maximo`` filas.
    """
    import numpy as np  # import perezoso: solo se necesita al predecir

    sintomas = lista_sintomas()
    posicion = {s: i for i, s in enumerate(sintomas)}
    x = np.zeros((1, len(sintomas)), dtype=np.float32)
    for s in seleccionados:
        if s in posicion:
            x[0, posicion[s]] = 1.0

    modelo, encoder = _cargar_modelo()
    probabilidades = modelo.predict_proba(x)[0]
    claves = encoder.inverse_transform(modelo.classes_)

    filas = sorted(
        (
            {
                'clave': str(clave),
                'nombre': nombre_enfermedad(str(clave)),
                'porcentaje': round(float(p) * 100, 1),
            }
            for clave, p in zip(claves, probabilidades)
        ),
        key=lambda f: f['porcentaje'],
        reverse=True,
    )
    relevantes = [f for f in filas if f['porcentaje'] >= minimo_pct][:maximo]
    return relevantes or filas[:1]
