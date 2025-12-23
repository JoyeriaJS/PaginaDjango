def cargar_regiones_comunas():
    from django.conf import settings
    import os, json

    ruta = os.path.join(settings.BASE_DIR, "core", "data", "chile_regiones_comunas.json")

    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Convertimos el formato del JSON a: { "Region": [comunas] }
    regiones_dict = {}

    for entry in data["Regiones"]:
        nombre_region = entry["region"]
        comunas = entry["comunas"]
        regiones_dict[nombre_region] = comunas

    return regiones_dict
