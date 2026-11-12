"""Respuestas falsas para probar la plomería sin Ollama:
    CONTRAMAQUINA_SIMULAR=1 python pipeline.py

Útil para depurar el flujo de datos. NO produce análisis real.
"""
import random
import re

random.seed(0)


def respuesta_simulada(esquema, usuario: str) -> dict:
    nombre = esquema.__name__
    props = esquema.model_json_schema()
    if "hallazgos" in props.get("properties", {}):
        # toma una oración real del fragmento como "cita" y, a veces, inventa una (para probar el verificador)
        texto = usuario.split('"""')[1] if '"""' in usuario else usuario
        oraciones = [o.strip() for o in re.split(r"(?<=[.!?])\s+", texto) if len(o.strip()) > 40]
        ids = props["$defs"]["Hallazgo"]["properties"]["categoria"]["enum"]
        hallazgos = []
        for o in random.sample(oraciones, k=min(2, len(oraciones))):
            hallazgos.append({"categoria": random.choice(ids), "cita": o, "enunciador": "simulado",
                              "victima_referida": "general", "justificacion": "simulación"})
        hallazgos.append({"categoria": ids[0], "cita": "Esta frase no existe en ninguna fuente del corpus.",
                          "enunciador": "simulado", "victima_referida": "general", "justificacion": "alucinación de prueba"})
        return {"hallazgos": hallazgos}
    if nombre == "Evaluacion":
        return {"importancia": random.choice(["A", "B"]), "justificacion_eval": "simulación"}
    if "categoria_n2" in props.get("properties", {}):
        ids = props["properties"]["categoria_n2"]["enum"]
        return {"categoria_n2": random.choice(ids), "justificacion_n2": "simulación"}
    return {k: "simulado" for k in props.get("properties", {})}
