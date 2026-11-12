"""[04] EVALUADOR — asigna relevancia analítica A/B para priorizar la revisión manual.

Importante: el Evaluador PRIORIZA, no filtra. Los hallazgos B no se borran;
solo se revisan después. Así se evita que el sesgo del modelo decida qué se pierde.
"""
from typing import Literal

from pydantic import BaseModel, Field

from llm import preguntar_json

SISTEMA = """Evalúas la relevancia analítica de hallazgos para una tesis sobre necrodiscurso en el Caso Narvarte.

Criterios (borrador: el investigador debe ajustarlos):
- A: el enunciador es una autoridad o un medio de amplio alcance, el mecanismo es explícito,
     y el hallazgo ayuda a mostrar cómo se construyó la narrativa oficial.
- B: mecanismo implícito o ambiguo, enunciador marginal, o hallazgo redundante.

Responde con la importancia y una justificación breve."""


class Evaluacion(BaseModel):
    importancia: Literal["A", "B"]
    justificacion_eval: str = Field(description="Una frase")


def evaluar(h: dict) -> dict:
    usuario = (f"Documento: {h['doc_id']} (fuente: {h['fuente']}, fecha: {h['fecha']})\n"
               f"Categoría N1: {h['categoria']} | Categoría N2: {h.get('categoria_n2', '—')}\n"
               f"Enunciador: {h['enunciador']}\n"
               f"Cita: \"{h['cita']}\"")
    return preguntar_json(SISTEMA, usuario, Evaluacion).model_dump()
