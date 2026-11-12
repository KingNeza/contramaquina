"""Descarga comunicados oficiales de fiscalías sobre feminicidio y los guarda como .txt
en corpus/raw/, con el nombre que la célula necesita:  AAAA-MM-DD_fuente_descripcion.txt

Uso (con el entorno activado):
    python descargar_corpus.py

El texto se guarda TAL CUAL aparece en el sitio oficial (sin resumir ni reescribir),
porque el verificador de citas compara palabra por palabra contra este archivo.
Al final se genera corpus/fuentes.csv con la URL de origen de cada archivo.
"""
import csv
import io
import re
import shutil
import time
import unicodedata
from pathlib import Path

import requests
import trafilatura

# (fuente, URL) · Todas son páginas o PDF publicados por las propias fiscalías.
URLS = [
    # Fiscalía General de Justicia de la Ciudad de México
    ("fgjcdmx", "https://www.fgjcdmx.gob.mx/comunicacion/nota/CS2025-179"),
    ("fgjcdmx", "https://www.fgjcdmx.gob.mx/comunicacion/nota/CS2024-1376"),
    # Fiscalía General del Estado de Querétaro
    ("fgeqro", "https://fiscaliageneralqro.gob.mx/CSnoticias/wp-content/uploads/2024/07/Comunicado-40-2024.pdf"),
    ("fgeqro", "https://fiscaliageneralqro.gob.mx/CSnoticias/wp-content/uploads/2024/06/Comunicado-36-2024.pdf"),
    ("fgeqro", "https://fiscaliageneralqro.gob.mx/CSnoticias/wp-content/uploads/2023/05/COMUNICADO-56-2023.pdf"),
    ("fgeqro", "https://fiscaliageneralqro.gob.mx/CSnoticias/wp-content/uploads/2022/07/COMUNICADO-73-2022.pdf"),
    ("fgeqro", "https://fiscaliageneralqro.gob.mx/CSnoticias/2020/06/27/fiscalia-obtiene-sentencia-condenatoria-para-imputados-por-feminicidio-en-tequisquiapan/"),
    ("fgeqro", "https://fiscaliageneralqro.gob.mx/CSnoticias/2021/12/13/detenido-imputado-de-feminicidio-ocurrido-en-huimilpan/"),
    ("fgeqro", "https://fiscaliageneralqro.gob.mx/CSnoticias/2022/04/10/fiscalia-general-detiene-con-orden-de-aprehension-a-feminicida-de-victoria-guadalupe/"),
    ("fgeqro", "https://fiscaliageneralqro.gob.mx/CSnoticias/2022/10/01/en-prision-posible-interviniente-en-feminicidio-ocurrido-en-colonia-satelite/"),
    ("fgeqro", "https://fiscaliageneralqro.gob.mx/CSnoticias/2023/03/09/fiscalia-obtiene-sentencia-condenatoria-de-50-anos-de-prision-para-feminicida-de-nina-en-el-marques/"),
    # Fiscalía General del Estado de Chihuahua
    ("fgechih", "https://chihuahua.gob.mx/sites/default/atach2/noticias/adjuntos/2024-10/FEM%20NORTE-%20Enfrentar%C3%A1%20proceso%20penal%20por%20feminicidio%20y%20asaltar%20tienda%20de%20abarrotes%20en%20Ciudad%20Ju%C3%A1rez.pdf"),
    ("fgechih", "https://chihuahua.gob.mx/sites/default/atach2/noticias/adjuntos/2024-10/Lo%20vinculan%20a%20proceso%20penal%20por%20delito%20de%20feminicidio%20de%20su%20madre%20en%20Chihuahua.pdf"),
    ("fgechih", "https://chihuahua.gob.mx/prensa/obtiene-fem-sentencia-ejemplar-de-70-anos-de-prision-por-feminicidio-de-nina-de-tres-anos"),
    ("fgechih", "https://fiscalia.chihuahua.gob.mx/logra-fem-vinculacion-a-proceso-de-acusado-por-feminicidio-en-ciudad-juarez/"),
    ("fgechih", "https://fiscalia.chihuahua.gob.mx/formula-fem-imputacion-a-hombre-por-probable-participacion-en-feminicidio-en-chihuahua/"),
    ("fgechih", "https://fiscalia.chihuahua.gob.mx/obtiene-fem-sentencia-de-43-anos-y-8-meses-de-prision-por-feminicidio-de-su-pareja-en-chihuahua/"),
    ("fgechih", "https://fiscalia.chihuahua.gob.mx/obtiene-fem-sentencia-de-mas-de-27-anos-de-carcel-contra-feminicida-en-ciudad-juarez-2/"),
    ("fgechih", "https://fiscalia.chihuahua.gob.mx/obtiene-fem-sentencia-de-70-anos-de-prision-contra-doble-feminicida/"),
    ("fgechih", "https://fiscalia.chihuahua.gob.mx/logra-fem-sentencia-de-41-anos-de-prision-en-contra-de-feminicida-del-panoramico/"),
    ("fgechih", "https://fiscalia.chihuahua.gob.mx/logra-fem-sentencia-de-27-anos-contra-feminicida-y-de-20-anos-para-su-complice-en-crimen-cometido-en-delicias/"),
    ("fgechih", "https://fiscalia.chihuahua.gob.mx/purgara-pena-de-30-anos-de-prision-por-feminicidio-en-chihuahua/"),
    ("fgechih", "https://fiscalia.chihuahua.gob.mx/obtiene-fem-fallo-condenatorio-contra-pareja-por-feminicidio-agravado-en-chihuahua/"),
    # Fiscalía General del Estado de Oaxaca
    ("fgeo", "https://portal.fgeo.gob.mx/index.php/archivos/noticias/fiscalia-logra-sentencia-de-20-anos-contra-feminicida"),
    ("fgeo", "https://portal.fgeo.gob.mx/index.php/archivos/noticias/logra-fiscalia-general-sentencia-de-66-anos-de-prision-por-el-delito-de-feminicidio"),

    # ---------------- Segunda tanda: 53 comunicados de otras 10 fiscalías ----------------
    # Fiscalía General de Justicia del Estado de México
    ("fgjem", "https://www.fiscaliaedomex.gob.mx/wp-content/uploads/2023/10/comunicado539-2021-210422183507.pdf"),
    ("fgjem", "https://sintesis.yoporlajusticia.gob.mx/2026/10/23/por-feminicidio-cometido-en-agravio-de-una-menor-fgjem-consigue-sentencia-de-62-anos-de-prision-en-contra-de-dos-responsables/"),
    # Fiscalía General del Estado de Veracruz
    ("fgever", "https://comunicacion.fiscaliaveracruz.gob.mx/imputado-como-probable-responsable-del-delito-de-feminicidio-14/"),
    ("fgever", "https://comunicacion.fiscaliaveracruz.gob.mx/imputado-como-probable-responsable-del-delito-de-feminicidio-en-grado-de-tentativa-2/"),
    ("fgever", "https://comunicacion.fiscaliaveracruz.gob.mx/imputado-como-probable-responsable-de-los-delitos-de-feminicidio-y-violacion/"),
    ("fgever", "https://comunicacion.fiscaliaveracruz.gob.mx/detenido-como-probable-responsable-del-delito-de-feminicidio-en-veracruz/"),
    ("fgever", "https://comunicacion.fiscaliaveracruz.gob.mx/detenido-como-probable-responsable-del-delito-de-feminicidio-6/"),
    ("fgever", "https://comunicacion.fiscaliaveracruz.gob.mx/prision-preventiva-contra-probable-responsable-del-delito-de-feminicidio-en-santiago-tuxtla/"),
    ("fgever", "http://comunicacion.fiscaliaveracruz.gob.mx/vinculado-a-proceso-por-los-presuntos-delitos-de-feminicidio-y-desaparicion-de-personas-en-su-modalidad-de-ocultamiento/"),
    ("fgever", "https://comunicacion.fiscaliaveracruz.gob.mx/sentenciado-a-62-anos-de-prision-como-responsable-del-delito-de-feminicidio-2/"),
    ("fgever", "https://comunicacion.fiscaliaveracruz.gob.mx/vinculado-a-proceso-como-probable-responsable-de-los-delitos-de-feminicidio-y-delito-vinculado-a-la-desaparicion/"),
    # Fiscalía General del Estado de Yucatán
    ("fgeyuc", "https://fge.yucatan.gob.mx/noticias/6694"),
    ("fgeyuc", "https://fge.yucatan.gob.mx/noticias/vinculado-a-proceso-por-intento-de-feminicidio-en-tekax"),
    ("fgeyuc", "https://fge.yucatan.gob.mx/noticias/imputado-y-tras-las-rejas-por-tentativa-de-feminicidio"),
    ("fgeyuc", "https://fge.yucatan.gob.mx/noticias/vinculado-a-proceso-por-feminicidio-en-chemax"),
    ("fgeyuc", "https://fge.yucatan.gob.mx/noticias/tras-las-rejas-por-tentativa-de-feminicidio-en-hunucma"),
    ("fgeyuc", "https://fge.yucatan.gob.mx/noticias/imputado-por-intento-de-feminicidio-contra-su-madre"),
    ("fgeyuc", "https://fge.yucatan.gob.mx/noticias/formulan-acusacion-por-intento-de-feminicidio-6541"),
    ("fgeyuc", "https://fge.yucatan.gob.mx/noticias/tras-las-rejas-imputado-por-feminicidio-en-motul"),
    ("fgeyuc", "https://fge.yucatan.gob.mx/noticias/formulan-imputacion-a-involucrado-en-feminicidio"),
    # Fiscalía General del Estado de Quintana Roo
    ("fgeqroo", "https://www.fgeqroo.gob.mx/comunicados/detalle/logra-fiscalia-condena-de-33-anos-y-4-meses-de-prision-para-un-sujeto-por-feminicidio-en-grado-de-tentativa-y-homicidio-calificado-en-grado-de-tentativa"),
    ("fgeqroo", "https://www.fgeqroo.gob.mx/comunicados/detalle/captura-fge-quintana-roo-dos-personas-por-feminicidio-en-benito-juarez"),
    ("fgeqroo", "https://www.fgeqroo.gob.mx/comunicados/detalle/obtiene-fge-de-quintana-roo-vinculacion-proceso-de-una-persona-por-feminicidio-de-una-menor-en-benito-juarez"),
    ("fgeqroo", "https://www.fgeqroo.gob.mx/comunicados/detalle/fge-de-quintana-roo-subsana-irregularidades-de-la-pasada-administracion-y-logra-vinculacion-proceso-de-una-mujer-por-feminicidio-en-playa-del-carmen"),
    ("fgeqroo", "https://www.fgeqroo.gob.mx/comunicados/detalle/obtiene-fge-quintana-roo-sentencia-de-50-anos-de-prision-para-un-sujeto-por-feminicidio-ocurrido-en-isla-mujeres"),
    # Fiscalía General del Estado de Michoacán
    ("fgemich", "https://comunicacion.fiscaliamichoacan.gob.mx/articulos/20241115-26862024-fiscalia-general-en-primer-lugar-en-combate-a-la-impunidad-en-feminicidio-y-otros-delitos-en-agravio-de-las-mujeres"),
    # Fiscalía General de Justicia del Estado de Zacatecas
    ("fgezac", "https://www.fiscaliazacatecas.gob.mx/la-fiscalia-general-informa-mas-avances-en-la-investigacion-y-sancion-del-delito-de-feminicidio-en-la-entidad/"),
    ("fgezac", "https://www.fiscaliazacatecas.gob.mx/se-obtiene-sentencia-condenatoria-por-el-delito-de-feminicidio/"),
    # Fiscalía General del Estado de Baja California
    ("fgebc", "https://www.fgebc.gob.mx/boletines/12135-obtiene-fiscalia-estatal-sentencia-de-24-anos-de-prision-para-acusados-de-feminicidio-en-grado-de-tentativa"),
    ("fgebc", "https://www.fgebc.gob.mx/boletines/13944-inicia-proceso-contra-sujeto-acusado-de-feminicidio"),
    ("fgebc", "https://www.fgebc.gob.mx/boletines/13547-fiscalia-de-baja-california-obtiene-sentencia-de-53-anos-de-prision-por-tentativa-de-feminicidio-y-violacion"),
    ("fgebc", "https://www.fgebc.gob.mx/boletines/12953-fiscalia-general-del-estado-logra-vinculacion-a-proceso-por-tentativa-de-feminicidio-y-privacion-de-libertad"),
    ("fgebc", "https://www.fgebc.gob.mx/boletines/13189-logra-la-fiscalia-general-del-estado-vinculacion-a-proceso-para-mujer-imputada-por-homicidio-calificado-y-feminicidio"),
    ("fgebc", "https://www.fgebc.gob.mx/boletines/15189-inicia-proceso-penal-contra-presuntos-responsables-de-feminicidio-agravado"),
    ("fgebc", "https://fgebc.gob.mx/boletines/12680-en-proceso-penal-imputados-en-homicidio-calificado-y-feminicidio"),
    ("fgebc", "https://www.fgebc.gob.mx/boletines/17491-inicia-proceso-penal-contra-imputado-por-feminicidio-agravado"),
    ("fgebc", "https://www.fgebc.gob.mx/boletines/13814-agencia-estatal-de-investigacion-captura-a-mujer-implicada-en-feminicidio"),
    # Fiscalía General del Estado de San Luis Potosí
    ("fgeslp", "https://fiscaliaslp.gob.mx/vi/fiscalia-de-feminicidios-detiene-a-dos-personas-por-muerte-de-mujer-suscitada-en-la-capital-potosina/"),
    ("fgeslp", "https://fiscaliaslp.gob.mx/vi/fiscalia-de-slp-logra-20-anos-de-prision-para-acusado-de-feminicidio-en-tamazunchale/"),
    ("fgeslp", "https://fiscaliaslp.gob.mx/vi/dan-14-anos-de-carcel-a-imputado-de-feminicidio-en-slp-fiscalia-potosina/"),
    ("fgeslp", "https://fiscaliaslp.gob.mx/vi/captura-fiscalia-a-hombre-por-probable-feminicidio-en-colonia-las-flores-de-slp/"),
    ("fgeslp", "https://fiscaliaslp.gob.mx/vi/fiscalia-de-slp-captura-a-sujeto-relacionado-con-el-deceso-de-una-mujer/"),
    ("fgeslp", "https://fiscaliaslp.gob.mx/vi/agentes-fiscales-obtienen-fallo-condenatorio-por-feminicidio-en-grado-de-tentativa-en-ciudad-valles/"),
    ("fgeslp", "https://fiscaliaslp.gob.mx/vi/en-slp-fiscalia-de-feminicidios-logra-mas-de-13-anos-de-carcel-para-acusado-de-disparar-contra-una-mujer/"),
    ("fgeslp", "https://fiscaliaslp.gob.mx/vi/litigadores-de-fgeslp-obtienen-prision-para-senalados-por-el-deceso-de-una-mujer-en-centro-nocturno/"),
    # Fiscalía General del Estado de Guerrero
    ("fgegro", "https://fiscaliaguerrero.gob.mx/index.php/2026/08/30/fgeguerrero-detiene-en-iguala-a-un-hombre-por-feminicidio-ocurrido-en-huitzuco/"),
    ("fgegro", "https://fiscaliaguerrero.gob.mx/index.php/2026/07/09/fge-guerrero-logra-sentencia-de-50-anos-de-prision-por-feminicidio-en-acapulco/"),
    ("fgegro", "https://fiscaliaguerrero.gob.mx/index.php/2026/08/12/fge-guerrero-logra-sentencia-de-mas-de-67-anos-por-feminicidio-en-alcozauca/"),
    ("fgegro", "https://fiscaliaguerrero.gob.mx/index.php/2026/08/16/fgeguerrero-cumplimenta-orden-de-aprehension-por-el-delito-de-feminicidio-en-ayutla-de-los-libres/"),
    ("fgegro", "https://fiscaliaguerrero.gob.mx/index.php/2026/08/12/fge-guerrero-logra-sentencia-de-mas-de-21-anos-de-prision-por-feminicidio-en-grado-de-tentativa-robo-de-motocicleta-y-danos-con-motivo-de-transito-vehicular-en-iguala/"),
    ("fgegro", "https://fiscaliaguerrero.gob.mx/index.php/2026/08/12/fgeguerrero-logra-sentencia-de-mas-de-66-anos-por-los-delitos-de-feminicidio-y-homicidio-en-tlacoapa/"),
    # Fiscalía General del Estado de Aguascalientes
    ("fgeags", "https://www.fiscalia-aguascalientes.gob.mx/noticia/2463/m%C3%A1xima-sentencia-por-tentativa-de-feminicidio"),
]

RAIZ = Path(__file__).parent
DESTINO = RAIZ / "corpus" / "raw"
CABECERAS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 "
                           "(KHTML, like Gecko) Version/17.0 Safari/605.1.15"}
MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
         "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}


def descargar(url: str) -> requests.Response:
    try:
        r = requests.get(url, headers=CABECERAS, timeout=30)
    except requests.exceptions.SSLError:
        # Algunos sitios de gobierno tienen certificados mal configurados.
        print("    (certificado del sitio inválido; se descarga sin verificarlo)")
        requests.packages.urllib3.disable_warnings()
        r = requests.get(url, headers=CABECERAS, timeout=30, verify=False)
    r.raise_for_status()
    return r


def texto_de_pdf(contenido: bytes) -> str:
    from pypdf import PdfReader
    return "\n\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(contenido)).pages)


def texto_de_html(html: str, url: str) -> tuple[str, str | None, str | None]:
    """Devuelve (texto del cuerpo, título, fecha) usando trafilatura."""
    datos = trafilatura.bare_extraction(html, url=url, include_comments=False,
                                        include_tables=False, with_metadata=True)
    if not datos:
        return "", None, None
    if not isinstance(datos, dict):          # versiones recientes devuelven un objeto
        datos = datos.as_dict()
    return datos.get("text") or "", datos.get("title"), datos.get("date")


def fecha_en_texto(texto: str) -> str | None:
    m = re.search(r"(\d{1,2})\s+de\s+([a-záé]+)\s+(?:de|del)\s+(\d{4})", texto[:600].lower())
    if m and m.group(2) in MESES:
        return f"{m.group(3)}-{MESES[m.group(2)]:02d}-{int(m.group(1)):02d}"
    return None


def fecha_en_url(url: str) -> str | None:
    m = re.search(r"/(20\d{2})/(\d{2})/(\d{2})/", url)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"/(20\d{2})-(\d{2})/", url) or re.search(r"/uploads/(20\d{2})/(\d{2})/", url)
    if m:
        return f"{m.group(1)}-{m.group(2)}-01"
    return None


def slug(texto: str, maximo: int = 60) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t[:maximo].rstrip("-") or "comunicado"


def apartar_ficticios():
    """Mueve las notas ficticias de prueba fuera de corpus/raw para no mezclarlas."""
    otra = RAIZ / "corpus" / "ejemplos_ficticios"
    for f in DESTINO.glob("*ficti*"):
        otra.mkdir(exist_ok=True)
        shutil.move(str(f), otra / f.name)
        print(f"  · {f.name} movido a corpus/ejemplos_ficticios/")


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    apartar_ficticios()
    # Lo que ya se descargó en una corrida anterior no se vuelve a descargar.
    previos = {}
    ruta_registro = RAIZ / "corpus" / "fuentes.csv"
    if ruta_registro.exists():
        with open(ruta_registro, encoding="utf-8-sig") as f:
            for fila in csv.DictReader(f):
                if fila["estado"] == "ok" and (DESTINO / fila["archivo"]).exists():
                    previos[fila["url"]] = fila

    registro, ok = [], 0
    for i, (fuente, url) in enumerate(URLS, start=1):
        print(f"[{i:02d}/{len(URLS)}] {url[:90]}")
        if url in previos:
            print(f"    = ya descargado: {previos[url]['archivo']}")
            registro.append(previos[url])
            ok += 1
            continue
        try:
            r = descargar(url)
            es_pdf = url.lower().endswith(".pdf") or "pdf" in r.headers.get("Content-Type", "")
            if es_pdf:
                texto, titulo, fecha = texto_de_pdf(r.content), None, None
            else:
                texto, titulo, fecha = texto_de_html(r.text, url)
            texto = texto.strip()
            if len(texto) < 200:
                raise ValueError("no se encontró el cuerpo del comunicado (texto demasiado corto)")
            fecha = fecha or fecha_en_texto(texto) or fecha_en_url(url) or "0000-00-00"
            titulo = titulo or texto.splitlines()[0]
            nombre = f"{fecha}_{fuente}_{slug(titulo)}.txt"
            encabezado = f"Fuente: {url}\nDescargado: {time.strftime('%Y-%m-%d')}\n\n"
            if titulo and titulo not in texto[:300]:
                encabezado += titulo + "\n\n"
            (DESTINO / nombre).write_text(encabezado + texto + "\n", encoding="utf-8")
            print(f"    ✓ {nombre}")
            registro.append({"archivo": nombre, "fuente": fuente, "fecha": fecha, "url": url, "estado": "ok"})
            ok += 1
        except Exception as e:
            print(f"    ✗ {e}")
            registro.append({"archivo": "", "fuente": fuente, "fecha": "", "url": url, "estado": f"error: {e}"})
        time.sleep(1)  # pausa de cortesía entre descargas

    with open(ruta_registro, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["archivo", "fuente", "fecha", "url", "estado"])
        w.writeheader()
        w.writerows(registro)
    print(f"\nListo: {ok} de {len(URLS)} comunicados guardados en corpus/raw/")
    print("Registro de fuentes: corpus/fuentes.csv")
    if ok < len(URLS):
        print("Los que fallaron pueden copiarse a mano desde el navegador (ver fuentes.csv).")


if __name__ == "__main__":
    main()
