import json
from django.conf import settings
from pathlib import Path

def cargar_regiones_comunas():
    """
    Carga el JSON que contiene todas las regiones,
    ciudades y comunas de Chile.
    """
    ruta = Path(settings.BASE_DIR) / "core" / "static" / "core" / "chile_regiones.json"

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
