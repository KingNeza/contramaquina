"""Verificación de citas: ¿lo que el modelo dice que está en la fuente, está?

Resultados posibles:
  - exacta:        la cita aparece literal (tras normalizar espacios y comillas)
  - aproximada:    hay un pasaje casi idéntico (≥ umbral); se guarda el pasaje real
  - no_encontrada: probable alucinación -> se descarta del análisis
"""
import re
import unicodedata
from difflib import SequenceMatcher


def normalizar(t: str) -> str:
    t = unicodedata.normalize("NFC", t)
    t = t.translate(str.maketrans({"“": '"', "”": '"', "«": '"', "»": '"', "‘": "'", "’": "'", "—": "-", "–": "-"}))
    return re.sub(r"\s+", " ", t).strip().lower()


def verificar_cita(cita: str, fuente: str, umbral: float = 0.90) -> dict:
    c, f = normalizar(cita), normalizar(fuente)
    if not c:
        return {"estado": "no_encontrada", "similitud": 0.0, "pasaje_real": None, "posicion": None}
    pos = f.find(c)
    if pos != -1:
        return {"estado": "exacta", "similitud": 1.0, "pasaje_real": cita, "posicion": pos}

    # Búsqueda aproximada: ventana del tamaño de la cita que se desliza por la fuente.
    largo, mejor, mejor_pos = len(c), 0.0, None
    paso = max(1, largo // 10)
    for i in range(0, max(1, len(f) - largo + 1), paso):
        r = SequenceMatcher(None, c, f[i:i + largo]).ratio()
        if r > mejor:
            mejor, mejor_pos = r, i
    if mejor_pos is not None:  # afinar alrededor del mejor punto
        for i in range(max(0, mejor_pos - paso), min(len(f) - largo + 1, mejor_pos + paso) + 1):
            r = SequenceMatcher(None, c, f[i:i + largo]).ratio()
            if r > mejor:
                mejor, mejor_pos = r, i
    if mejor >= umbral:
        return {"estado": "aproximada", "similitud": round(mejor, 3),
                "pasaje_real": f[mejor_pos:mejor_pos + largo], "posicion": mejor_pos}
    return {"estado": "no_encontrada", "similitud": round(mejor, 3), "pasaje_real": None, "posicion": None}
