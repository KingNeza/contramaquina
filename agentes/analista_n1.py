"""[02] ANALISTA NIVEL 1 — detecta mecanismos discursivos revictimizantes (ACDF).

El modelo NO cuenta ni resume: solo señala fragmentos, con cita textual,
categoría del libro de códigos y justificación. Python hace el resto.
"""
from typing import Literal

from pydantic import BaseModel, Field

from llm import preguntar_json


def describir_codebook(categorias: list[dict]) -> str:
    bloques = []
    for c in categorias:
        b = [f"### {c['id']} — {c['nombre']}", f"Definición: {c['definicion'].strip()}"]
        if c.get("incluye"):
            b.append("Incluye: " + "; ".join(c["incluye"]))
        if c.get("excluye"):
            b.append("NO incluye: " + "; ".join(c["excluye"]))
        if c.get("ejemplos"):
            b.append("Ejemplo: " + " | ".join(c["ejemplos"]))
        bloques.append("\n".join(b))
    return "\n\n".join(bloques)


def construir_esquema(ids: list[str]):
    Categoria = Literal[tuple(ids)]

    class Hallazgo(BaseModel):
        categoria: Categoria
        cita: str = Field(description="Copia LITERAL del texto, sin cambiar una sola palabra")
        enunciador: str = Field(description="Quién dice o reproduce la frase (autoridad, medio, testigo...)")
        victima_referida: str = Field(description="A quién se refiere, o 'general'")
        justificacion: str = Field(description="Por qué encaja en la categoría, en una o dos frases")

    class Respuesta(BaseModel):
        hallazgos: list[Hallazgo]

    return Respuesta


SISTEMA = """Eres un asistente de codificación para una investigación de Análisis Crítico del Discurso con perspectiva feminista.
Tu tarea es SEÑALAR fragmentos, no interpretar el caso ni opinar sobre él.

Reglas:
1. Usa SOLO las categorías del libro de códigos. Si nada encaja, devuelve una lista vacía.
2. La "cita" debe copiarse LITERALMENTE del texto: mismas palabras, mismo orden. Nunca parafrasees ni completes.
3. Cita la porción más corta que muestre el mecanismo (idealmente una oración).
4. Respeta las exclusiones de cada categoría.
5. Si dudas, NO lo incluyas: un falso positivo cuesta más que una omisión.

LIBRO DE CÓDIGOS:
{codebook}"""


def analizar_fragmento(fragmento: str, categorias: list[dict]) -> list[dict]:
    esquema = construir_esquema([c["id"] for c in categorias])
    sistema = SISTEMA.format(codebook=describir_codebook(categorias))
    usuario = f"TEXTO A CODIFICAR:\n\"\"\"\n{fragmento}\n\"\"\""
    respuesta = preguntar_json(sistema, usuario, esquema)
    return [h.model_dump() for h in respuesta.hallazgos]
