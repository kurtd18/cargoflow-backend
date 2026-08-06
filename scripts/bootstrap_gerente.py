"""
Crea el PRIMER usuario gerente de Colgate, directo en la base de datos --
necesario porque POST /usuarios exige ya ser gerente para crear a otros
(huevo y gallina). Úsalo solo una vez; después, el gerente crea a los
demás (administrador, supervisor, operario) desde /docs con POST /usuarios.

Uso:
    $env:DATABASE_URL = "postgresql+psycopg://postgres:<password>@<host_proxy>:<puerto>/railway"
    python scripts/bootstrap_gerente.py
"""

import os
import sys

import bcrypt
import psycopg

EMAIL_GERENTE = "gerente@colgate.demo"
PASSWORD_GERENTE = "cargoflow123"
EMAIL_REFERENCIA = "supervisor@colgate.demo"


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Define $env:DATABASE_URL con la cadena de conexión pública de Railway antes de correr esto.")
        sys.exit(1)

    conn = psycopg.connect(database_url.replace("postgresql+psycopg://", "postgresql://"))
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT empresa_id FROM usuarios WHERE email = %s", (EMAIL_REFERENCIA,))
    row = cur.fetchone()
    if not row:
        print(f"No encontré ningún usuario con email {EMAIL_REFERENCIA}. Corre primero scripts/seed_demo.py.")
        sys.exit(1)
    empresa_id = row[0]

    cur.execute("SELECT 1 FROM usuarios WHERE email = %s", (EMAIL_GERENTE,))
    if cur.fetchone():
        print(f"Ya existe un usuario con email {EMAIL_GERENTE}. No se creó nada nuevo.")
        return

    password_hash = bcrypt.hashpw(PASSWORD_GERENTE.encode(), bcrypt.gensalt()).decode()

    cur.execute(
        """
        INSERT INTO usuarios (id, empresa_id, nombre, email, password_hash, rol, tipo_acceso, activo, creado_en)
        VALUES (uuid_generate_v4(), %s, %s, %s, %s, 'gerente', 'movil', true, now())
        """,
        (empresa_id, "Gerente Colgate", EMAIL_GERENTE, password_hash),
    )
    print(f"Usuario gerente creado: {EMAIL_GERENTE} / {PASSWORD_GERENTE}")


if __name__ == "__main__":
    main()