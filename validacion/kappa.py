"""Acuerdo entre la codificación humana y la de la célula (kappa de Cohen).

1. Abre validacion/muestra_para_codificar.xlsx y llena la columna `categoria_humana`
   con un id del libro de códigos (o NINGUNA si la cita no debió marcarse). Guarda.
2. Corre:  python validacion/kappa.py

Lectura orientativa (Landis y Koch): <0.40 débil · 0.41–0.60 moderado ·
0.61–0.80 sustancial · >0.80 casi perfecto.
"""
from collections import Counter
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).parent


def kappa_cohen(a: list, b: list) -> float:
    n = len(a)
    observado = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    esperado = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return 1.0 if esperado == 1 else (observado - esperado) / (1 - esperado)


if __name__ == "__main__":
    humano = pd.read_excel(AQUI / "muestra_para_codificar.xlsx")
    modelo = pd.read_json(AQUI / "muestra_modelo.json")
    df = humano.merge(modelo, on=["doc_id", "cita"])
    df["categoria_humana"] = df["categoria_humana"].fillna("").astype(str).str.strip().str.upper()
    df = df[df["categoria_humana"] != ""]
    if df.empty:
        raise SystemExit("Primero llena la columna categoria_humana en el Excel y guárdalo.")
    k = kappa_cohen(df["categoria_humana"].tolist(), df["categoria"].tolist())
    print(f"Citas comparadas: {len(df)}")
    print(f"Acuerdo simple:   {(df['categoria_humana'] == df['categoria']).mean():.0%}")
    print(f"Kappa de Cohen:   {k:.2f}")
    print("\nMatriz de confusión (filas = humano, columnas = célula):")
    print(pd.crosstab(df["categoria_humana"], df["categoria"]))
