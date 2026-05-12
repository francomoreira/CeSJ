#!/usr/bin/env python3
"""
Extrae el árbol completo de categorías de CompraEnSanJuan.com
y lo imprime como JSON por stdout.

Uso:
    python3 extraer-arbol.py > arbol-categorias.json

Dependencias: curl, Python 3 stdlib (sin libs externas)
"""

import json
import re
import subprocess
import sys
import time

import os

# URL del sitio: prioridad 1) variable de entorno SITIO_URL, 2) ~/.cesj/env, 3) fallback
_SITIO_ENV = os.environ.get("SITIO_URL")
if _SITIO_ENV:
    BASE = _SITIO_ENV
else:
    _env_path = os.path.expanduser("~/.cesj/env")
    if os.path.exists(_env_path):
        with open(_env_path) as _f:
            for _line in _f:
                _line = _line.strip()
                if _line.startswith("SITIO_URL="):
                    BASE = _line.split("=", 1)[1].strip()
                    break
            else:
                BASE = "https://www.example.com"
    else:
        BASE = "https://www.example.com"

def curl(url, timeout=30):
    """curl wrapper - returns text as str, handles iso-8859-1 encoding."""
    try:
        r = subprocess.run(
            ["curl", "-sL", "--max-time", str(timeout), url],
            capture_output=True, timeout=timeout+5
        )
        # The site uses iso-8859-1 encoding
        return r.stdout.decode("iso-8859-1", errors="replace")
    except Exception as e:
        print(f"  ⚠ Error fetching {url}: {e}", file=sys.stderr)
        return ""


def extraer_subcats(html):
    """Extrae subcategorías del sidebar de una página."""
    subs = []
    for m in re.finditer(r'cat=(\d{3,})[^"]*"[^>]*>\s*([^<]+?)\s*\((\d+)\)\s*</a>', html):
        cat_id = m.group(1)
        nombre = re.sub(r'\s+', ' ', m.group(2)).strip()
        try:
            count = int(m.group(3))
        except ValueError:
            count = 0
        if len(cat_id) >= 4:
            subs.append({"cat": cat_id, "nombre": nombre, "anuncios": count})
    return subs


def extraer_autos_populares(html):
    """Extrae modelos de autos de la página /vehiculos."""
    modelos = []
    for m in re.finditer(
        r'href="[^"]*cat=(2\d{4,})[^"]*"[^>]*class="[^"]*"[^>]*>\s*([^<]+?)\s*\((\d+)\)\s*</a>',
        html
    ):
        cat_id = m.group(1)
        nombre = re.sub(r'\s+', ' ', m.group(2)).strip()
        try:
            count = int(m.group(3))
        except ValueError:
            count = 0
        modelos.append({"cat": cat_id, "nombre": nombre, "anuncios": count})
    return modelos


def main():
    arbol = {
        "generado": time.strftime("%Y-%m-%d %H:%M:%S"),
        "categorias": []
    }

    # =====================================================
    # 1. Vehículos, Inmuebles, Servicios (desde homepage)
    # =====================================================
    html = curl(BASE)
    if not html:
        print(json.dumps(arbol, indent=2, ensure_ascii=False))
        return

    # Categorías principales del dropdown
    principales = [
        ("Vehículos", [
            (200, "Autos"), (208, "Camiones"), (225, "Camionetas, Utilitarios, SUV"),
            (226, "Motos, Cuatriciclos"), (227, "Náutica"),
            (224, "Otros vehículos"), (220, "Planes de Ahorro")
        ]),
        ("Inmuebles", [
            (100, "Casas"), (111, "Cocheras"), (102, "Departamentos"),
            (108, "Fincas, Campos, Quintas"), (112, "Galpones"),
            (106, "Locales, Salones, Oficinas, Consultorios"),
            (110, "Negocios, Industrias"), (113, "Parcelas, Nichos"),
            (104, "Terrenos, Lotes"), (109, "Transferencias, Carpetas")
        ]),
        ("Servicios", [
            (302, "Capacitaciones"), (300, "Cuidado personal"),
            (399, "Empleos"), (304, "Fiestas, Eventos"),
            (306, "Imprenta"), (308, "Mantenimiento de Vehiculos"),
            (310, "Mantenimiento del Hogar"), (398, "Otros servicios"),
            (312, "Profesionales"), (314, "Servicio Técnico"),
            (316, "Transporte General"), (318, "Viajes, Turismo")
        ])
    ]

    for grupo, cats in principales:
        cat_data = {"nombre": grupo, "slug": None, "cat_base": None, "subcategorias": []}
        for cid, cname in cats:
            cat_data["subcategorias"].append({
                "cat": str(cid), "nombre": cname, "anuncios": 0
            })
        arbol["categorias"].append(cat_data)

    # Modelos populares de vehículos (desde /vehiculos)
    html_vehiculos = curl(BASE + "/vehiculos")
    if html_vehiculos:
        modelos = extraer_autos_populares(html_vehiculos)
        if modelos:
            # Ubicarlos dentro de Vehículos
            for cat in arbol["categorias"]:
                if cat["nombre"] == "Vehículos":
                    cat["modelos_populares"] = modelos
                    break

    # =====================================================
    # 2. Artículos (por slug)
    # =====================================================
    articulos = [
        ("celulares-telefonia", "Celulares, Telefonía"),
        ("computacion", "Computación"),
        ("consolas-videojuegos", "Consolas, Videojuegos"),
        ("deportes", "Deportes"),
        ("camping", "Camping"),
        ("electrodomesticos", "Electrodomésticos"),
        ("electronica-audio-video", "Electrónica, Audio, Video"),
        ("hogar-muebles-jardin", "Hogar, Muebles, Jardín"),
        ("ropa-y-accesorios", "Ropa y Accesorios"),
        ("industrias-oficinas", "Industrias, Oficinas"),
        ("instrumentos-musicales", "Instrumentos Musicales"),
        ("joyas-relojes", "Joyas, Relojes"),
        ("juegos-juguetes", "Juegos, Juguetes"),
        ("musica-peliculas-libros-revistas", "Música, Películas, Libros, Revistas"),
        ("salud-belleza-cuidado-personal", "Salud, Belleza, Cuidado Personal"),
        ("arte-artesania-antiguedades", "Arte, Artesanía, Antiguedades"),
        ("comestibles-bebidas-delicatessen", "Comestibles, Bebidas, Delicatessen"),
        ("fiestas-y-eventos", "Fiestas y Eventos"),
        ("anuncios-de-compra", "Anuncios de Compra"),
        ("repuestos-y-acc-para-vehiculos", "Repuestos y Acc. para Vehiculos"),
        ("camaras-fotograficas-accesorios", "Cámaras fotograficas, Accesorios"),
        ("animales-mascotas", "Animales, Mascotas"),
        ("articulos-para-bebes", "Articulos para Bebes"),
    ]

    for slug, nombre in articulos:
        print(f"  Extrayendo: {slug}...", file=sys.stderr)
        html_art = curl(f"{BASE}/{slug}")
        subs = extraer_subcats(html_art)

        if subs:
            # El cat base es el prefijo de 3 dígitos
            cat_base = subs[0]["cat"][:3]
        else:
            cat_base = "???"

        cat_data = {
            "nombre": nombre,
            "slug": slug,
            "cat_base": cat_base,
            "subcategorias": subs
        }
        arbol["categorias"].append(cat_data)

        time.sleep(0.5)  # pausa entre requests para no saturar

    # =====================================================
    # Salida
    # =====================================================
    print(json.dumps(arbol, indent=2, ensure_ascii=False))
    print(f"\n✅ {len(arbol['categorias'])} categorías extraídas", file=sys.stderr)


if __name__ == "__main__":
    main()
