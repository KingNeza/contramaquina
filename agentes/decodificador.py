"""[01] DECODIFICADOR — convierte archivos crudos en texto limpio + metadatos.

Principio: aquí NO interviene el LLM. La fidelidad al original se logra con
herramientas deterministas (extracción de PDF, Whisper para audio/video).

Convención de nombres para que el metadato temporal salga solo:
    AAAA-MM-DD_fuente_descripcion.ext
    ej. 2015-08-01_pgjdf_conferencia.pdf  ->  fecha=2015-08-01, fuente=pgjdf
"""
import json
import re
import unicodedata
from pathlib import Path

PATRON_NOMBRE = re.compile(r"^(\d{4}-\d{2}-\d{2})_([^_]+)_?(.*)$")
AUDIO_VIDEO = {".mp3", ".wav", ".m4a", ".mp4", ".mov", ".ogg"}


def metadatos_desde_nombre(ruta: Path) -> dict:
    m = PATRON_NOMBRE.match(ruta.stem)
    if not m:
        return {"fecha": None, "fuente": "desconocida", "descripcion": ruta.stem}
    return {"fecha": m.group(1), "fuente": m.group(2), "descripcion": m.group(3).replace("_", " ")}


def extraer_texto(ruta: Path) -> str:
    ext = ruta.suffix.lower()
    if ext in {".txt", ".md"}:
        return ruta.read_text(encoding="utf-8", errors="replace")
    if ext == ".pdf":
        from pypdf import PdfReader
        paginas = [p.extract_text() or "" for p in PdfReader(str(ruta)).pages]
        texto = "\n\n".join(paginas)
        if len(texto.strip()) < 50:
            print(f"  ⚠ {ruta.name}: casi sin texto. ¿PDF escaneado? Requiere OCR (pendiente).")
        return texto
    if ext in AUDIO_VIDEO:
        return transcribir(ruta)
    raise ValueError(f"Formato no soportado todavía: {ext}")


def transcribir(ruta: Path) -> str:
    """Transcripción local con Whisper. En Mac Apple Silicon, mlx-whisper es el más rápido."""
    try:
        import mlx_whisper
        r = mlx_whisper.transcribe(str(ruta), path_or_hf_repo="mlx-community/whisper-large-v3-turbo", language="es")
        return r["text"]
    except ImportError:
        pass
    try:
        from faster_whisper import WhisperModel
        segmentos, _ = WhisperModel("large-v3", compute_type="int8").transcribe(str(ruta), language="es")
        return "\n".join(s.text.strip() for s in segmentos)
    except ImportError:
        raise RuntimeError("Instala mlx-whisper (Mac) o faster-whisper para transcribir audio/video.")


def limpiar(texto: str) -> str:
    """Limpieza mínima y reversible: normaliza Unicode y espacios. No reescribe nada."""
    texto = unicodedata.normalize("NFC", texto)
    texto = texto.replace("\r\n", "\n").replace("­", "")      # guiones suaves de PDF
    texto = re.sub(r"(\w)-\n(\w)", r"\1\2", texto)                    # palabras cortadas por renglón
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def decodificar(dir_crudo: str, dir_limpio: str) -> list[dict]:
    salida = Path(dir_limpio)
    salida.mkdir(parents=True, exist_ok=True)
    documentos = []
    for ruta in sorted(Path(dir_crudo).iterdir()):
        if ruta.name.startswith(".") or ruta.is_dir():
            continue
        print(f"  · {ruta.name}")
        try:
            texto = limpiar(extraer_texto(ruta))
        except Exception as e:
            print(f"  ✗ {ruta.name}: {e}")
            continue
        doc = {"doc_id": ruta.stem, "archivo": ruta.name, **metadatos_desde_nombre(ruta)}
        (salida / f"{ruta.stem}.txt").write_text(texto, encoding="utf-8")
        (salida / f"{ruta.stem}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        documentos.append({**doc, "texto": texto})
    return documentos
