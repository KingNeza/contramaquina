"""Divide documentos largos en fragmentos que caben en la ventana del modelo local.

Corta en saltos de párrafo cuando puede y deja un solapamiento para que una
frase partida no se pierda entre dos fragmentos.
"""


def fragmentar(texto: str, max_caracteres: int = 2500, solapamiento: int = 300) -> list[dict]:
    fragmentos, inicio, n = [], 0, len(texto)
    while inicio < n:
        fin = min(inicio + max_caracteres, n)
        if fin < n:
            corte = texto.rfind("\n\n", inicio + max_caracteres // 2, fin)
            if corte == -1:
                corte = texto.rfind(". ", inicio + max_caracteres // 2, fin)
                corte = corte + 1 if corte != -1 else -1
            if corte != -1:
                fin = corte
        fragmentos.append({"inicio": inicio, "fin": fin, "texto": texto[inicio:fin]})
        if fin >= n:
            break
        inicio = max(fin - solapamiento, inicio + 1)
    for i, f in enumerate(fragmentos):
        f["frag_id"] = i
    return fragmentos
