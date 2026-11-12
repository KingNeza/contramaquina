# Contramáquina artificial

Célula de agentes locales (Ollama) para el análisis del necrodiscurso en el Caso Narvarte.
Proyecto colaborativo de la Maestría en Comunicación y Humanidades Digitales · Universidad del Claustro de Sor Juana.

```
corpus/raw ─▶ [01] Decodificador ─▶ fragmentos ─▶ [02] Analista N1 ─▶ verificación de citas
                 (sin LLM)                         (ACDF, JSON)        (descarta alucinaciones)
                                                                              │
   resumen.md ◀─ reporte (pandas) ◀─ [04] Evaluador A/B ◀─ [03] Analista N2 ◀─┘
   validacion/ ─▶ kappa humano vs. célula                    (Mbembe)
```

## Arranque rápido
```bash
ollama pull qwen3:14b
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python llm.py                                  # ¿responde el modelo?
python descargar_corpus.py                     # descarga 25 comunicados oficiales a corpus/raw
CONTRAMAQUINA_SIMULAR=1 python pipeline.py     # plomería sin modelo
python pipeline.py --limite 3                  # análisis real, 3 fragmentos
python validacion/kappa.py                     # acuerdo humano–célula
```

La guía paso a paso (instalación, archivos y sesión) está en **GUIA_SESION.html**: se abre con doble clic en el navegador.

El resultado principal es `salidas/hallazgos.xlsx`.

Los dos documentos de `corpus/raw/` son **ficticios** y solo sirven para probar. Se reemplazan por el corpus real.

## Principios de diseño
- El LLM **señala**; Python **cuenta**; la persona **interpreta**.
- Toda afirmación del modelo lleva cita textual, y toda cita se comprueba contra la fuente.
- El Evaluador prioriza la revisión, nunca borra hallazgos.
- Todo corre en local: el corpus no sale de la máquina.
