import json
from pathlib import Path
from django.conf import settings

def cargar_regiones_comunas():
    """
    Carga el JSON con regiones y comunas desde core/data/
    """
    ruta = Path(settings.BASE_DIR) / "core" / "data" / "chile_regiones_comunas.json"

    try:
        if ruta.exists():
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            print("⚠️ Archivo JSON NO encontrado en:", ruta)
    except Exception as e:
        print("⚠️ Error leyendo JSON:", e)

    return {}  # fallback
