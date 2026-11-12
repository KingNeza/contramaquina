"""Puente único con el modelo local (Ollama).

Todos los agentes hablan con el modelo a través de `preguntar_json`, así que
cambiar de modelo se hace en un solo lugar (config.yaml).
"""
import json
import os

import yaml
from pydantic import BaseModel, ValidationError

with open(os.path.join(os.path.dirname(__file__), "config.yaml"), encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

# Modo simulado: permite probar la "plomería" del pipeline sin Ollama.
SIMULAR = os.environ.get("CONTRAMAQUINA_SIMULAR") == "1"


def preguntar_json(sistema: str, usuario: str, esquema: type[BaseModel], reintentos: int = 2) -> BaseModel:
    """Envía un prompt y obliga al modelo a responder con el esquema JSON dado."""
    if SIMULAR:
        from simulador import respuesta_simulada
        return esquema.model_validate(respuesta_simulada(esquema, usuario))

    import ollama

    kwargs = dict(
        model=CONFIG["modelo"],
        messages=[{"role": "system", "content": sistema}, {"role": "user", "content": usuario}],
        format=esquema.model_json_schema(),
        options={
            "temperature": CONFIG.get("temperatura", 0.2),
            "repeat_penalty": 1.15,   # castiga repetir lo mismo (evita ciclos)
            "num_predict": 2048,      # tope de longitud: nunca se queda colgado
        },
    )
    if CONFIG.get("desactivar_razonamiento"):
        kwargs["think"] = False

    ultimo_error = None
    for intento in range(reintentos + 1):
        try:
            r = ollama.chat(**kwargs)
            return esquema.model_validate_json(r["message"]["content"])
        except (ValidationError, json.JSONDecodeError) as e:
            ultimo_error = e
            print(f"  ⚠ respuesta inválida (intento {intento + 1}), reintentando...")
    raise RuntimeError(f"El modelo no devolvió JSON válido tras {reintentos + 1} intentos: {ultimo_error}")


if __name__ == "__main__":
    # Prueba: una pregunta que el modelo SÍ sabe responder.
    class Respuesta(BaseModel):
        concepto: str
        definicion: str

    print(preguntar_json(
        "Responde solo en JSON, en español.",
        "Define en una frase qué es el análisis crítico del discurso.",
        Respuesta,
    ))
