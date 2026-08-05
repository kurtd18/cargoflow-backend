"""
Siembra datos de ejemplo para AQL y Facturación CONTRA LA API EN PRODUCCIÓN
(no toca la base de datos directamente) -- usa las credenciales de Colgate
que ya generó scripts/seed_demo.py, guardadas en scripts/seed_data.json.

Uso:
    python scripts/seed_demo_produccion.py

Por defecto le pega a la URL pública de Railway. Para probar contra tu
servidor local en cambio:
    $env:API_BASE_URL = "http://localhost:8000"
    python scripts/seed_demo_produccion.py
"""

import json
import os
import sys
from pathlib import Path

import requests

BASE_URL = os.environ.get("API_BASE_URL", "https://cargoflow-backend-production.up.railway.app")
SEED_DATA_PATH = Path(__file__).resolve().parent / "seed_data.json"


def cargar_colgate():
    if not SEED_DATA_PATH.exists():
        print(f"No se encontró {SEED_DATA_PATH}. Corre primero scripts/seed_demo.py.")
        sys.exit(1)
    empresas = json.loads(SEED_DATA_PATH.read_text(encoding="utf-8"))
    return empresas[0]  # Colgate es la primera


def login(email, password):
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    resp.raise_for_status()
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def crear_proveedor(headers, nombre):
    resp = requests.post(f"{BASE_URL}/proveedores", json={"nombre": nombre, "nit": "900999999-1"}, headers=headers)
    resp.raise_for_status()
    return resp.json()["id"]


def registrar_inspeccion(headers, proveedor_id, defectos):
    resp = requests.post(
        f"{BASE_URL}/aql/inspecciones",
        json={
            "proveedor_id": proveedor_id,
            "tamano_lote": 300,
            "nivel_inspeccion_general": "II",
            "aql": 2.5,
            "defectos_encontrados": defectos,
        },
        headers=headers,
    )
    resp.raise_for_status()
    return resp.json()


def crear_cliente_credito(headers, nombre):
    resp = requests.post(
        f"{BASE_URL}/clientes",
        json={"nombre": nombre, "nit": "900888888-2", "condicion_pago": "credito", "cupo_credito": 10000000},
        headers=headers,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def crear_tarifa(headers, cliente_id, servicio_id, valor):
    resp = requests.post(
        f"{BASE_URL}/tarifas",
        json={"cliente_id": cliente_id, "servicio_id": servicio_id, "criterio": "cajas", "valor": valor},
        headers=headers,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def flujo_completo_operacion(headers, cliente_id, servicio_id, cuadrilla_id, tarifa_id, forma_pago, cantidad_real):
    operacion = requests.post(
        f"{BASE_URL}/operaciones", json={"cliente_id": cliente_id, "servicio_id": servicio_id}, headers=headers
    )
    operacion.raise_for_status()
    operacion_id = operacion.json()["id"]

    requests.patch(
        f"{BASE_URL}/operaciones/{operacion_id}/asignar",
        json={
            "cuadrilla_id": cuadrilla_id, "tarifa_id": tarifa_id,
            "criterio_cobro": "cajas", "cantidad_estimada": cantidad_real,
        },
        headers=headers,
    ).raise_for_status()

    for tipo in ("factura", "pedido"):
        requests.post(
            f"{BASE_URL}/operaciones/{operacion_id}/evidencias",
            data={"tipo": tipo},
            files={"archivo": (f"{tipo}.png", b"contenido-demo", "image/png")},
            headers=headers,
        ).raise_for_status()

    requests.post(f"{BASE_URL}/operaciones/{operacion_id}/iniciar", headers=headers).raise_for_status()

    medio_pago = "transferencia" if forma_pago == "credito" else "efectivo"
    cierre = requests.post(
        f"{BASE_URL}/operaciones/{operacion_id}/cerrar",
        json={"cantidad_real": cantidad_real, "forma_pago": forma_pago, "medio_pago": medio_pago},
        headers=headers,
    )
    cierre.raise_for_status()
    return operacion_id


def main():
    colgate = cargar_colgate()
    print(f"Usando la API en: {BASE_URL}")
    print(f"Login como: {colgate['email']}")

    headers = login(colgate["email"], colgate["password"])

    print("\nCreando proveedor de ejemplo y registrando inspecciones AQL...")
    proveedor_id = crear_proveedor(headers, "Proveedor Demo AQL")
    for defectos in (0, 1, 8, 0, 0):  # mezcla: la mayoría pasa, una se rechaza
        inspeccion = registrar_inspeccion(headers, proveedor_id, defectos)
        print(f"  Inspección: {defectos} defectos -> {inspeccion['resultado']} (severidad proveedor: {inspeccion['severidad']})")

    print("\nCreando cliente a crédito y su tarifa...")
    cliente_credito_id = crear_cliente_credito(headers, "Cliente Demo Crédito")
    tarifa_credito_id = crear_tarifa(headers, cliente_credito_id, colgate["servicio_id"], 1850)

    print("\nCerrando operaciones de ejemplo (contado y crédito)...")
    for cantidad in (120, 340):
        op_id = flujo_completo_operacion(
            headers, colgate["cliente_id"], colgate["servicio_id"], colgate["cuadrilla_id"], colgate["tarifa_id"],
            forma_pago="contado", cantidad_real=cantidad,
        )
        print(f"  Operación {op_id} cerrada a CONTADO por {cantidad} unidades")

    for cantidad in (200, 275):
        op_id = flujo_completo_operacion(
            headers, cliente_credito_id, colgate["servicio_id"], colgate["cuadrilla_id"], tarifa_credito_id,
            forma_pago="credito", cantidad_real=cantidad,
        )
        print(f"  Operación {op_id} cerrada a CRÉDITO por {cantidad} unidades (queda pendiente de cobro)")

    print("\nDashboard resultante:\n")
    dashboard = requests.get(f"{BASE_URL}/reportes/dashboard", headers=headers)
    dashboard.raise_for_status()
    print(json.dumps(dashboard.json(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()