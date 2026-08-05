# CargoFlow — Backend

[![CI](https://github.com/kurtd18/cargoflow-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/kurtd18/cargoflow-backend/actions/workflows/ci.yml)

API REST para gestión de operaciones logísticas en centros de distribución (cargue, descargue, picking): control de cuadrillas, tarifas, evidencias obligatorias, inspección de calidad por muestreo (AQL), facturación y liquidación de operaciones — con aislamiento completo entre empresas (multi-tenant) garantizado a nivel de motor de base de datos.

Construida con **FastAPI + PostgreSQL**, usando Row-Level Security nativo de Postgres, no solo lógica de aplicación.

## 🔗 Demo en vivo

- **API**: https://cargoflow-backend-production.up.railway.app
- **Documentación interactiva (Swagger)**: https://cargoflow-backend-production.up.railway.app/docs
- **Healthcheck**: https://cargoflow-backend-production.up.railway.app/health

Desplegado en Railway, con CI/CD desde GitHub Actions — cada push a `main` corre la suite de pruebas y, si pasa, se despliega automáticamente.

**Credenciales de prueba** (10 empresas demo precargadas, todas con la misma contraseña):

| Email | Password |
|---|---|
| `supervisor@colgate.demo` | `cargoflow123` |

Para probar: entra a `/docs` → botón **Authorize** → `POST /auth/login` con esas credenciales → copia el `access_token` → pégalo en Authorize → prueba cualquier endpoint autenticado, incluyendo `GET /reportes/dashboard`, que ya tiene datos de ejemplo cargados.

## Stack

- **FastAPI** — framework web, validación con Pydantic
- **PostgreSQL 16** — con Row-Level Security nativo para aislamiento multiempresa
- **SQLAlchemy 2.0** (estilo `Mapped`/`mapped_column`) + **Alembic** para migraciones
- **JWT** (python-jose) para autenticación
- **pytest** — 47 pruebas de integración contra Postgres real (no SQLite)
- **Docker Compose** — API + base de datos con un solo comando
- **GitHub Actions** — CI corriendo la suite completa en cada push
- **Railway** — despliegue en producción

## Arquitectura: aislamiento multiempresa

Cada tabla de negocio tiene una política de **Row-Level Security** en PostgreSQL que exige `empresa_id = current_setting('app.current_tenant')`. Antes de cualquier consulta, la sesión de base de datos fija ese valor a partir del `empresa_id` codificado en el JWT del usuario autenticado.

El aislamiento entre empresas lo garantiza **PostgreSQL**, no una condición `WHERE` que alguien podría olvidar agregar en un endpoint nuevo — un error de programación no puede filtrar datos de una empresa a otra.

## Módulos

| Módulo | Qué hace |
|---|---|
| **Auth** | Login JWT, dos formatos (JSON para apps, form para Swagger) |
| **Operaciones** | Ciclo completo: crear → asignar cuadrilla/tarifa → iniciar → cerrar y liquidar |
| **Evidencias** | Fotos/documentos obligatorios (factura, pedido) antes de poder iniciar una operación |
| **Incidencias** | Reportes de novedades durante una operación (foto opcional) |
| **Tarifas** | Versionado automático — nunca se edita un precio en sitio, se cierra la vigencia anterior y se crea una nueva |
| **AQL** | Inspección de calidad por muestreo estadístico, norma real ANSI/ASQ Z1.4 (equivalente MIL-STD-105E) |
| **Facturación** | Cartera pendiente de cobro y marcado de pagos, a partir de los cierres de operación |
| **Reportes** | Dashboard consolidado: operaciones por estado y tiempos, calidad, financiero |
| **Clientes / Proveedores** | Alta y consulta — el mínimo necesario para dar de alta el resto de las entidades |

## Endpoints principales

<details>
<summary>Ver tabla completa (33 endpoints)</summary>

| Método | Ruta |
|---|---|
| POST | /auth/login, /auth/token |
| POST / GET / PATCH | /operaciones, /operaciones/{id}, /operaciones/{id}/asignar |
| POST | /operaciones/{id}/iniciar, /operaciones/{id}/cerrar |
| POST / GET | /operaciones/{id}/evidencias, /operaciones/{id}/evidencias/estado |
| POST / GET | /operaciones/{id}/incidencias |
| POST / GET / PATCH | /tarifas, /tarifas/{id}, /tarifas/{id}/vencer |
| GET | /aql/plan (calculadora, no persiste) |
| POST / GET | /aql/inspecciones, /aql/inspecciones/{id} |
| GET / PATCH | /facturacion/pendientes, /facturacion/resumen, /facturacion/pagos/{id}/marcar-pagado |
| GET | /reportes/dashboard |
| POST / GET | /clientes, /clientes/{id} |
| POST / GET | /proveedores, /proveedores/{id} |
| GET | /health |

</details>

Documentación interactiva completa (con esquemas de cada request/response) en `/docs`.

## Reglas de negocio clave (y sus tests)

- Una operación **no puede iniciar** sin evidencias de `factura` y `pedido` ya cargadas → `412`.
- Una operación **no puede cerrarse** si no pasó por `iniciar` primero → `400`.
- La liquidación **siempre** se calcula con `cantidad_real`, nunca con `cantidad_estimada`.
- Cerrar con `forma_pago: credito` exige que el cliente esté registrado con esa condición → `400` si no.
- Las tarifas se **versionan**, nunca se editan en sitio: crear una nueva para el mismo cliente+servicio cierra automáticamente la anterior.
- AQL usa las tablas reales de la norma (código de letra por lote, Ac/Re verificados) para decidir aceptado/rechazado, y actualiza automáticamente la severidad del proveedor según las reglas de cambio oficiales.

Todas estas reglas están cubiertas por la suite de pytest (47 pruebas) y se validan automáticamente en cada push vía CI.

## Cómo correrlo

### Con Docker (recomendado)

```
docker compose up --build
```

Levanta la API y PostgreSQL juntos, corre las migraciones automáticamente al arrancar, disponible en http://localhost:8000.

### Local, sin Docker

```
docker compose up -d db
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

### Sembrar datos de prueba

```
python scripts/seed_demo.py
python scripts/seed_demo_produccion.py
```

## Correr las pruebas

```
pytest tests/ -v
```

Corre contra una base de datos Postgres real y separada (el nombre de tu base + `_test`, se crea sola) — los modelos usan UUID nativo y Row-Level Security de Postgres, que no existen en SQLite.

## Variables de entorno

| Variable | Descripción | Default |
|---|---|---|
| DATABASE_URL | Cadena de conexión a Postgres | — |
| JWT_SECRET | Secreto para firmar tokens | — (el arranque falla si sigue en el valor de ejemplo con ENVIRONMENT=production) |
| JWT_ALGORITHM | Algoritmo del JWT | HS256 |
| JWT_EXPIRE_MINUTES | Expiración del token | 480 |
| ENVIRONMENT | development \| production | development |
| ALLOWED_ORIGINS | Dominios permitidos por CORS, separados por coma, o * | * |
| EXPOSE_DOCS | Expone /docs, /redoc, /openapi.json | false |

## Estructura del proyecto

```
app/
  api/
    deps.py            (autenticacion, RLS por tenant, control de roles)
    routers/            (auth, operaciones, evidencias, incidencias, tarifas,
                          aql, facturacion, reportes, clientes, proveedores)
  core/                  (settings, database con RLS, security JWT)
  models/                (plataforma, recursos, operaciones, calidad)
  schemas/               (Pydantic: request/response por modulo)
  services/aql.py        (tablas ANSI Z1.4 y logica de muestreo, sin DB)
  storage/                (abstraccion de almacenamiento de archivos subidos)
alembic/                  (migraciones, incluye las politicas RLS)
tests/                    (pytest, contra Postgres real, 47 pruebas)
scripts/                  (seed_demo.py, seed_demo_produccion.py)
.github/workflows/         (CI)
```

## Roadmap

- Portal del cliente (que el cliente vea sus propias operaciones/pagos)
- Tablas Ac/Re verificadas para inspección reforzada y reducida (hoy AQL reutiliza la tabla normal como aproximación en esos dos estados)
- Migración de almacenamiento local (uploads/) a object storage (S3 o similar) para despliegue multi-instancia
- Facturación electrónica real (integración DIAN)