"""Métricas: las calcula Python, no el modelo.

Genera:
  salidas/hallazgos.xlsx                      tabla completa para revisar en Excel / Numbers
  salidas/prevalencia.xlsx                    conteo por categoría, fuente y mes
  salidas/resumen.md                          resumen legible
  validacion/muestra_para_codificar.xlsx      muestra para codificación humana (kappa)
"""
from pathlib import Path

import pandas as pd

ETAPAS = ["04_hallazgos_evaluados.jsonl", "03_hallazgos_n2.jsonl", "02_hallazgos_n1.jsonl"]


def _ultima_etapa(salidas: Path) -> Path:
    """Toma el archivo de hallazgos MÁS RECIENTE, no el de la etapa más avanzada."""
    existentes = [salidas / n for n in ETAPAS if (salidas / n).exists()]
    if not existentes:
        raise FileNotFoundError("No hay hallazgos todavía. Corre primero la etapa n1.")
    elegido = max(existentes, key=lambda p: p.stat().st_mtime)
    print(f"  (usando {elegido.name})")
    return elegido


def _excel(df: pd.DataFrame, ruta: Path):
    """Guarda en Excel con columnas de ancho legible y texto ajustado."""
    from openpyxl.styles import Alignment
    with pd.ExcelWriter(ruta, engine="openpyxl") as w:
        df.to_excel(w, index=False)
        hoja = w.sheets["Sheet1"]
        for i, col in enumerate(df.columns, start=1):
            letra = hoja.cell(row=1, column=i).column_letter
            ancho = 60 if col in ("cita", "justificacion", "pasaje_real", "justificacion_n2") else 18
            hoja.column_dimensions[letra].width = ancho
        for fila in hoja.iter_rows(min_row=2):
            for celda in fila:
                celda.alignment = Alignment(wrap_text=True, vertical="top")


def generar_reporte(salidas: Path, tam_muestra: int = 30):
    print("[05] Reporte")
    df = pd.read_json(_ultima_etapa(salidas), lines=True)
    if df.empty:
        print("  (sin hallazgos)")
        return
    df["mes"] = pd.to_datetime(df["fecha"], errors="coerce").dt.to_period("M").astype(str)
    _excel(df, salidas / "hallazgos.xlsx")

    lineas = ["# Resumen de la célula", "", f"Hallazgos verificados: **{len(df)}**", ""]
    lineas += ["## Prevalencia por mecanismo (N1)", "", df["categoria"].value_counts().to_markdown(), ""]

    tabla = df.groupby(["categoria", "fuente", "mes"]).size().reset_index(name="n")
    _excel(tabla, salidas / "prevalencia.xlsx")
    lineas += ["## Por fuente", "", pd.crosstab(df["fuente"], df["categoria"]).to_markdown(), ""]
    lineas += ["## Evolución temporal", "", pd.crosstab(df["mes"], df["categoria"]).to_markdown(), ""]

    if "categoria_n2" in df:
        lineas += ["## Cruce N1 × N2", "", pd.crosstab(df["categoria"], df["categoria_n2"]).to_markdown(), ""]
    if "importancia" in df:
        lineas += ["## Importancia (Evaluador)", "", df["importancia"].value_counts().to_markdown(), ""]

    desc = salidas / "02_descartes_alucinacion.jsonl"
    if desc.exists():
        n_desc = sum(1 for l in desc.open(encoding="utf-8") if l.strip())
        lineas += [f"Citas descartadas por no existir en la fuente: **{n_desc}**", ""]

    (salidas / "resumen.md").write_text("\n".join(lineas), encoding="utf-8")
    print("  → salidas/resumen.md, hallazgos.xlsx, prevalencia.xlsx")

    # Muestra ciega para validación humana: sin la categoría del modelo a la vista.
    val = Path("validacion")
    val.mkdir(exist_ok=True)
    muestra = df.sample(n=min(tam_muestra, len(df)), random_state=42)
    _excel(muestra[["doc_id", "cita"]].assign(categoria_humana=""), val / "muestra_para_codificar.xlsx")
    muestra[["doc_id", "cita", "categoria"]].to_json(val / "muestra_modelo.json", orient="records",
                                                     force_ascii=False, indent=2)
    print(f"  → validacion/muestra_para_codificar.xlsx ({len(muestra)} citas para codificar a mano)")
