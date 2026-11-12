"""[03] ANALISTA NIVEL 2 — relee los hallazgos verificados del N1 desde la
necropolítica (Mbembe). Solo recibe hallazgos que pasaron la verificación.

Versión inicial: una categoría N2 (o NINGUNA) por hallazgo. Ideas para crecer:
permitir varias categorías, darle el fragmento completo como contexto, etc.
"""
from typing import Literal

from pydantic import BaseModel, Field

from llm import preguntar_json

SISTEMA = """Eres un asistente de codificación teórica. Recibes un hallazgo ya identificado como
mecanismo revictimizante y debes decidir si, además, expresa alguna categoría de necropolítica / necrodiscurso.

Usa SOLO estas categorías. Si ninguna aplica con claridad, responde NINGUNA.

{categorias}"""


def clasificar_hallazgo(hallazgo: dict, categorias: list[dict]) -> dict:
    ids = [c["id"] for c in categorias] + ["NINGUNA"]

    class Respuesta(BaseModel):
        categoria_n2: Literal[tuple(ids)]
        justificacion_n2: str = Field(description="Una o dos frases")

    texto_cats = "\n".join(f"- {c['id']}: {c['definicion'].strip()}" for c in categorias)
    usuario = (f"Categoría N1: {hallazgo['categoria']}\n"
               f"Cita: \"{hallazgo['cita']}\"\n"
               f"Enunciador: {hallazgo['enunciador']}\n"
               f"Justificación N1: {hallazgo['justificacion']}")
    r = preguntar_json(SISTEMA.format(categorias=texto_cats), usuario, Respuesta)
    return r.model_dump()
