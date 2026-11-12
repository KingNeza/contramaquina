"""Orquestador de la célula Contramáquina.

Uso:
    python pipeline.py                 # corre todo
    python pipeline.py --etapa n1      # solo una etapa (lee la salida de la anterior)
    python pipeline.py --limite 3      # procesa solo 3 fragmentos (para probar rápido)

Etapas: decodificar -> n1 (+ verificación) -> n2 -> evaluar -> reporte
Cada etapa escribe un .jsonl en salidas/, así se puede repetir una sin rehacer las demás.
"""
import argparse
import json
import time
from pathlib import Path

import yaml

from llm import CONFIG
from fragmentos import fragmentar
from verificar import verificar_cita
from agentes.decodificador import decodificar
from agentes.analista_n1 import analizar_fragmento
from agentes.analista_n2 import clasificar_hallazgo
from agentes.evaluador import evaluar

R = CONFIG["rutas"]
SALIDAS = Path(R["salidas"])
SALIDAS.mkdir(exist_ok=True)


def guardar(nombre, filas):
    with open(SALIDAS / nombre, "w", encoding="utf-8") as f:
        for fila in filas:
            f.write(json.dumps(fila, ensure_ascii=False) + "\n")
    print(f"  → {len(filas)} registros en salidas/{nombre}")


def cargar(nombre):
    with open(SALIDAS / nombre, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def codebook():
    with open(R["codebook"], encoding="utf-8") as f:
        return yaml.safe_load(f)


def etapa_decodificar(_):
    print("[01] Decodificador")
    docs = decodificar(R["crudo"], R["limpio"])
    guardar("01_documentos.jsonl", docs)


def etapa_n1(args):
    print(f"[02] Analista N1  (modelo: {CONFIG['modelo']})")
    cats = codebook()["nivel_1"]
    cfg = CONFIG["fragmentos"]
    hallazgos, descartes, procesados = [], [], 0
    for doc in cargar("01_documentos.jsonl"):
        for frag in fragmentar(doc["texto"], cfg["max_caracteres"], cfg["solapamiento"]):
            if args.limite and procesados >= args.limite:
                break
            procesados += 1
            t0 = time.time()
            for h in analizar_fragmento(frag["texto"], cats):
                v = verificar_cita(h["cita"], doc["texto"], CONFIG["verificacion"]["umbral_aproximada"])
                fila = {"doc_id": doc["doc_id"], "fecha": doc["fecha"], "fuente": doc["fuente"],
                        "frag_id": frag["frag_id"], **h, "verificacion": v["estado"],
                        "similitud": v["similitud"], "pasaje_real": v["pasaje_real"]}
                (hallazgos if v["estado"] != "no_encontrada" else descartes).append(fila)
            print(f"  · {doc['doc_id']} frag {frag['frag_id']}  ({time.time() - t0:.1f}s)")
    # El solapamiento puede producir la misma cita dos veces: se deduplica.
    unicos = {(h["doc_id"], h["categoria"], h["cita"].strip().lower()): h for h in hallazgos}
    guardar("02_hallazgos_n1.jsonl", list(unicos.values()))
    guardar("02_descartes_alucinacion.jsonl", descartes)


def etapa_n2(_):
    print("[03] Analista N2")
    cats = codebook()["nivel_2"]
    filas = [{**h, **clasificar_hallazgo(h, cats)} for h in cargar("02_hallazgos_n1.jsonl")]
    guardar("03_hallazgos_n2.jsonl", filas)


def etapa_evaluar(_):
    print("[04] Evaluador")
    filas = [{**h, **evaluar(h)} for h in cargar("03_hallazgos_n2.jsonl")]
    guardar("04_hallazgos_evaluados.jsonl", filas)


def etapa_reporte(_):
    from reporte import generar_reporte
    generar_reporte(SALIDAS)


ETAPAS = {"decodificar": etapa_decodificar, "n1": etapa_n1, "n2": etapa_n2,
          "evaluar": etapa_evaluar, "reporte": etapa_reporte}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--etapa", choices=list(ETAPAS), help="Corre solo esta etapa")
    p.add_argument("--limite", type=int, default=0, help="Máximo de fragmentos en N1 (0 = todos)")
    a = p.parse_args()
    for nombre, fn in ETAPAS.items():
        if a.etapa in (None, nombre):
            fn(a)
