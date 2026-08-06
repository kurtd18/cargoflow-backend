"""
Siembra las tarifas reales de Víveres/Electro (por tipo de vehículo) y
Fruver (por canastilla/tonelada) contra la API en producción.

Uso:
    python scripts/seed_tarifas_viveres_electro_fruver.py
"""

import json
import os
import sys
from pathlib import Path

import requests

BASE_URL = os.environ.get("API_BASE_URL", "https://cargoflow-backend-production.up.railway.app")
SEED_FILE = Path(__file__).resolve().parent / "seed_data.json"

# (nombre, TOTAL con IVA -- tabla "CUADRILLA VIVERES - ELECTRO")
VEHICULOS = [
    ("Vehiculo 200", 55702),
    ("Vehiculo 300", 74270),
    ("Turbo pequeño", 102120),
    ("Turbo largo", 148540),
    ("Sencillo", 167148),
    ("Sencillo extendido", 185673),
    ("Doble troque", 204241),
    ("Contenedor de 40", 352780),
    ("Contenedor de 20", 204241),
    ("Mula", 352780),
    ("Mula larga", 408483),
    ("Mula extralarga", 464185),
]

# (concepto, criterio, valor -- tabla "OPERACION FRUVER", columna Tarifa 2026)
FRUVER_ITEMS = [
    ("canastilla", "unidades", 380),
    ("descargue_tonelada", "toneladas", 19188),
    ("trasvaseo_tonelada", "toneladas", 23025),
    ("canastilla_ifco", "unidades", 196),
]


def cargar_colgate():
    if not SEED_FILE.exists():
        print(f"No se encontró {SEED_FILE}. Corre primero scripts/seed_demo.py.")
        sys.exit(1)
    empresas = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    return empresas[0]


def login(email, password):
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    resp.raise_for_status()
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def obtener_o_crear_servicio(headers, nombre):
    resp = requests.get(f"{BASE_URL}/servicios", headers=headers)
    resp.raise_for_status()
    for s in resp.json():
        if s["nombre"].strip().lower() == nombre.strip().lower():
            return s["id"]
    resp = requests.post(f"{BASE_URL}/servicios", json={"nombre": nombre}, headers=headers)
    resp.raise_for_status()
    return resp.json()["id"]


def crear_tipo_vehiculo(headers, nombre, tarifa_base):
    resp = requests.post(f"{BASE_URL}/tipos-vehiculo", json={"nombre": nombre, "tarifa_base": tarifa_base}, headers=headers)
    resp.raise_for_status()
    return resp.json()["id"]


def crear_tarifa(headers, **body):
    resp = requests.post(f"{BASE_URL}/tarifas", json=body, headers=headers)
    if resp.status_code != 201:
        print(f"  ERROR creando tarifa: {resp.status_code} {resp.text}")
        return None
    return resp.json()["id"]


def main():
    colgate = cargar_colgate()
    print(f"Usando la API en: {BASE_URL}")
    headers = login(colgate["email"], colgate["password"])

    print("\nUsando/creando servicios...")
    servicio_descargue_id = obtener_o_crear_servicio(headers, "Descargue")
    servicio_trasvaseo_id = obtener_o_crear_servicio(headers, "Trasvaseo")
    print(f"  Descargue: {servicio_descargue_id}")
    print(f"  Trasvaseo: {servicio_trasvaseo_id}")

    print("\nCreando tipos de vehículo y tarifas (Víveres + Electro)...")
    for nombre, total in VEHICULOS:
        tipo_id = crear_tipo_vehiculo(headers, nombre, total)
        for categoria in ("viveres", "electro"):
            tid = crear_tarifa(
                headers,
                servicio_id=servicio_descargue_id,
                criterio="vehiculo",
                valor=total,
                tipo_vehiculo_id=tipo_id,
                categoria_mercancia=categoria,
            )
            if tid:
                print(f"  {nombre} ({categoria}): ${total:,} -> tarifa {tid}")

    print("\nCreando tarifas de Fruver...")
    for concepto, criterio, valor in FRUVER_ITEMS:
        servicio_id = servicio_trasvaseo_id if concepto == "trasvaseo_tonelada" else servicio_descargue_id
        tid = crear_tarifa(
            headers,
            servicio_id=servicio_id,
            criterio=criterio,
            valor=valor,
            categoria_mercancia="fruver",
            concepto=concepto,
        )
        if tid:
            print(f"  {concepto} ({criterio}): ${valor:,} -> tarifa {tid}")

    print("\nListo. Revisa GET /tarifas?categoria_mercancia=fruver en /docs para confirmar.")


if __name__ == "__main__":
    main()