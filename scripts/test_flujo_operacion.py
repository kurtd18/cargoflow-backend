"""
Prueba automática del flujo completo de una operación, sin tocar Swagger UI.

Requiere:
  1. El servidor corriendo: uvicorn app.main:app --reload
  2. Haber corrido antes: python scripts/seed_demo.py
     (esto genera scripts/seed_data.json, que este script lee)

Uso:
    python scripts/test_flujo_operacion.py

Qué hace, paso a paso, imprimiendo el resultado de cada uno:
  1. Login como el supervisor de Colgate -> obtiene el token
  2. Crea una operación
  3. Le asigna cuadrilla y tarifa
  4. Intenta iniciarla -> esto DEBE fallar con 412, porque todavía no hemos
     implementado el endpoint de subida de evidencias (pedido/factura son
     obligatorias antes de iniciar). Ese error esperado confirma que la regla
     de negocio sí está siendo aplicada por el backend.
"""

import json
import sys
from pathlib import Path

import requests

BASE_URL = "http://localhost:8000"
SEED_FILE = Path(__file__).resolve().parent / "seed_data.json"


def paso(titulo):
    print(f"\n{'=' * 60}\n{titulo}\n{'=' * 60}")


def mostrar(respuesta):
    print(f"Status: {respuesta.status_code}")
    try:
        print(json.dumps(respuesta.json(), indent=2, ensure_ascii=False))
    except ValueError:
        print(respuesta.text)


def main():
    if not SEED_FILE.exists():
        print("No existe scripts/seed_data.json todavía.")
        print("Corre primero: python scripts/seed_demo.py")
        sys.exit(1)

    empresas = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    colgate = empresas[0]  # la primera empresa sembrada (Colgate)

    # 1. Login
    paso("1. Login como supervisor de Colgate")
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": colgate["email"], "password": colgate["password"]},
    )
    mostrar(resp)
    if resp.status_code != 200:
        print("\nEl login falló, no se puede continuar. Revisa que el servidor esté corriendo.")
        sys.exit(1)
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Crear operación
    paso("2. Crear operación")
    resp = requests.post(
        f"{BASE_URL}/operaciones",
        headers=headers,
        json={"cliente_id": colgate["cliente_id"], "servicio_id": colgate["servicio_id"], "muelle": "Muelle 1"},
    )
    mostrar(resp)
    if resp.status_code != 201:
        print("\nNo se pudo crear la operación, deteniendo la prueba.")
        sys.exit(1)
    operacion_id = resp.json()["id"]

    # 3. Asignar cuadrilla y tarifa
    paso("3. Asignar cuadrilla y tarifa")
    resp = requests.patch(
        f"{BASE_URL}/operaciones/{operacion_id}/asignar",
        headers=headers,
        json={
            "cuadrilla_id": colgate["cuadrilla_id"],
            "tarifa_id": colgate["tarifa_id"],
            "criterio_cobro": "cajas",
            "cantidad_estimada": 500,
        },
    )
    mostrar(resp)

    # 4. Intentar iniciar (debe fallar con 412: faltan evidencias)
    paso("4. Intentar iniciar operación (se espera error 412: faltan fotos obligatorias)")
    resp = requests.post(f"{BASE_URL}/operaciones/{operacion_id}/iniciar", headers=headers)
    mostrar(resp)
    if resp.status_code == 412:
        print("\nCorrecto: el backend bloqueó el inicio porque faltan las evidencias")
        print("obligatorias (pedido y factura), tal como está definido en el PRD y el UX Spec.")
    else:
        print(f"\nResultado inesperado (se esperaba 412, llegó {resp.status_code}).")

    print(f"\nID de la operación de prueba creada: {operacion_id}")
    print("Prueba terminada.")


if __name__ == "__main__":
    main()
