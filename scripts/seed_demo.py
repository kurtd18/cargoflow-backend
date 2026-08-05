"""
Script de siembra (seed) para pruebas: crea 10 empresas de ejemplo,
cada una con un usuario supervisor de prueba para poder hacer login.

Uso (desde la raíz del proyecto, con el entorno virtual activado):

    python scripts/seed_demo.py

Requiere que ya hayas corrido `alembic upgrade head` antes.

Nota sobre seguridad: la tabla `usuarios` tiene Row-Level Security activa
(ver Arquitectura Técnica, Sección 1.2), así que no basta con abrir una
sesión y hacer INSERT — hay que fijar `app.current_tenant` a la empresa
correspondiente ANTES de insertar su usuario, exactamente como lo haría
un request real autenticado. Por eso el script crea primero la empresa
(tabla sin RLS) y luego, en una transacción aparte, fija el tenant y
crea su usuario.
"""

"""
Script de siembra (seed) para pruebas: crea 10 empresas de ejemplo, y para
cada una: un usuario supervisor, un servicio, un cliente, un tipo de vehículo,
un vehículo, una cuadrilla y una tarifa vigente — lo mínimo para poder probar
el flujo completo de una operación (crear -> asignar -> iniciar -> cerrar)
sin tropezar con datos faltantes.

Uso (desde la raíz del proyecto, con el entorno virtual activado):

    python scripts/seed_demo.py

Requiere que ya hayas corrido `alembic upgrade head` antes.

Nota sobre seguridad: todas estas tablas tienen Row-Level Security activa
(ver Arquitectura Técnica, Sección 1.2), así que el script fija
`app.current_tenant` a la empresa correspondiente ANTES de insertar
cualquiera de sus datos, exactamente como lo haría un request real autenticado.
"""

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.plataforma import Empresa, Usuario, Cliente  # noqa: E402
from app.models.recursos import TipoVehiculo, Vehiculo, Cuadrilla, Servicio, Tarifa  # noqa: E402

EMPRESAS_DEMO = [
    "Colgate",
    "Nutresa",
    "Procter and Gamble",
    "Harinera del Valle",
    "Condimar",
    "Incubadora Santander",
    "Nestlé de Colombia",
    "Productos Familia",
    "Johnson y Johnson",
    "Huevos Santa Anita",
]

PASSWORD_DEMO = "cargoflow123"


def slugify(nombre: str) -> str:
    reemplazos = str.maketrans("áéíóúñ", "aeioun")
    return nombre.lower().translate(reemplazos).replace(" ", "").replace(".", "")


def fijar_tenant(db, empresa_id):
    # SET LOCAL no acepta parámetros bindeados (:tid); set_config() sí, y con
    # el tercer argumento en true se comporta igual (solo dura la transacción actual).
    db.execute(text("SELECT set_config('app.current_tenant', :tid, true)"), {"tid": str(empresa_id)})


def main():
    db = SessionLocal()
    resumen = []

    try:
        for nombre in EMPRESAS_DEMO:
            # 1. Empresa (tabla sin RLS)
            empresa = Empresa(nombre=nombre, plan="trial", estado="activa")
            db.add(empresa)
            db.commit()
            db.refresh(empresa)

            slug = slugify(nombre)
            email = f"supervisor@{slug}.demo"

            # 2. A partir de aquí, todo lo de esta empresa en una sola transacción con tenant fijado
            fijar_tenant(db, empresa.id)

            usuario = Usuario(
                empresa_id=empresa.id,
                nombre=f"Supervisor {nombre}",
                email=email,
                password_hash=hash_password(PASSWORD_DEMO),
                rol="supervisor",
                tipo_acceso="movil",
                activo=True,
            )
            db.add(usuario)

            servicio = Servicio(empresa_id=empresa.id, nombre="Descargue")
            db.add(servicio)

            cliente = Cliente(
                empresa_id=empresa.id,
                nombre=f"Cliente Demo {nombre}",
                nit="900000000-1",
                condicion_pago="contado",
                activo=True,
            )
            db.add(cliente)

            tipo_vehiculo = TipoVehiculo(empresa_id=empresa.id, nombre="Turbo", tarifa_base=620000)
            db.add(tipo_vehiculo)

            cuadrilla = Cuadrilla(empresa_id=empresa.id, nombre="Cuadrilla A", estado="disponible")
            db.add(cuadrilla)

            # flush para tener los IDs generados antes de crear las filas que dependen de ellos
            db.flush()

            vehiculo = Vehiculo(empresa_id=empresa.id, placa="TEST123", tipo_vehiculo_id=tipo_vehiculo.id)
            db.add(vehiculo)

            tarifa = Tarifa(
                empresa_id=empresa.id,
                cliente_id=cliente.id,
                servicio_id=servicio.id,
                criterio="cajas",
                valor=1850,
                vigente_desde=date.today(),
            )
            db.add(tarifa)

            db.commit()

            resumen.append(
                {
                    "empresa": nombre,
                    "email": email,
                    "password": PASSWORD_DEMO,
                    "cliente_id": str(cliente.id),
                    "servicio_id": str(servicio.id),
                    "cuadrilla_id": str(cuadrilla.id),
                    "tarifa_id": str(tarifa.id),
                }
            )

        salida = Path(__file__).resolve().parent / "seed_data.json"
        salida.write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"\n{len(resumen)} empresas creadas con datos de prueba completos.\n")
        print(f"{'Empresa':<22} {'Email de login':<35} {'Password'}")
        print("-" * 72)
        for r in resumen:
            print(f"{r['empresa']:<22} {r['email']:<35} {PASSWORD_DEMO}")

        print("\nIDs de prueba para Colgate:\n")
        colgate = resumen[0]
        print(f"  cliente_id : {colgate['cliente_id']}")
        print(f"  servicio_id: {colgate['servicio_id']}")
        print(f"  cuadrilla_id: {colgate['cuadrilla_id']}")
        print(f"  tarifa_id  : {colgate['tarifa_id']}")
        print(f"\nGuardado en {salida} para uso automático.")
        print("Siguiente paso: python scripts/test_flujo_operacion.py")

    except Exception as e:
        db.rollback()
        print(f"Error durante la siembra: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
