# CargoFlow — Backend (scaffold inicial)

Punto de partida del backend de CargoFlow en FastAPI + PostgreSQL, generado a partir de:

- `CargoFlow_PRD.docx` — reglas de negocio
- `CargoFlow_UX_Spec.docx` — pantallas y flujos
- `CargoFlow_Arquitectura_Tecnica.docx` — modelo de datos y endpoints completos

Este scaffold **no implementa los 31 endpoints documentados** — implementa el patrón central
(autenticación, aislamiento multiempresa vía Row-Level Security, y el módulo de Operaciones
como ejemplo completo) para que el resto se construya siguiendo el mismo patrón.

## Qué SÍ está implementado aquí

- Estructura de proyecto FastAPI estándar.
- Modelos SQLAlchemy de las tablas núcleo (empresas, usuarios, clientes, proveedores,
  cuadrillas, vehículos, tarifas, operaciones, evidencias, pagos, liquidaciones).
- Mecanismo de aislamiento multiempresa: cada request setea `app.current_tenant` en
  PostgreSQL antes de cualquier consulta, y las políticas RLS de la migración inicial
  hacen el resto (ver `alembic/versions/0001_initial_schema.py`).
- Autenticación JWT (login + verificación de token).
- Router de ejemplo completo: `POST /operaciones`, `PATCH /operaciones/{id}/asignar`,
  `POST /operaciones/{id}/cerrar` — cubriendo el flujo descrito en la Sección 4.1 del UX Spec.
- `docker-compose.yml` con PostgreSQL listo para levantar en local.

## Qué falta (para continuar en Claude Code)

- El resto de los endpoints listados en la Sección 3 de Arquitectura Técnica
  (Tarifas, AQL, Facturación, Dashboard, Portal del cliente, Inteligencia operativa).
- Migraciones Alembic incrementales a medida que se agreguen tablas.
- Tests.
- Lógica real de cálculo de liquidación (aquí está simplificada como ejemplo).

## Cómo continuar

Este scaffold está pensado para abrirse en **Claude Code**, donde es mucho más eficiente
iterar sobre archivos de código reales, correr el servidor, y pedir "implementa el endpoint
de Tarifas siguiendo el mismo patrón que Operaciones" con acceso directo al repo.

### Levantar en local

```bash
docker compose up -d          # levanta PostgreSQL
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head          # crea las tablas + políticas RLS
uvicorn app.main:app --reload
```

La documentación interactiva queda disponible en `http://localhost:8000/docs`.
