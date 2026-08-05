"""
Cálculo de planes de muestreo AQL (ANSI/ASQ Z1.4 - ISO 2859-1, equivalente a
MIL-STD-105E). Módulo sin dependencias de base de datos, para que la lógica
de la norma se pueda probar de forma aislada del resto de la app.

Fuente verificada: Tabla A (código de letra por tamaño de lote y nivel de
inspección general I/II/III) y Tabla II-A (plan de muestreo simple,
inspección NORMAL) de ANSI/ASQ Z1.4.

LIMITACIÓN CONOCIDA: esta versión solo tiene los valores Ac/Re verificados
para inspección NORMAL. Los niveles "reforzado" y "reducido" de la norma
usan sus propias tablas (II-B y II-C) con Ac/Re distintos -- por ahora,
cuando el proveedor está en reforzado/reducido, este módulo reutiliza los
mismos Ac/Re de la tabla normal como aproximación (TODO: incorporar II-B
y II-C verificadas -- no se agregaron todavía porque las únicas fuentes
disponibles eran PDFs escaneados con columnas ilegibles, y prefiero dejar
el TODO explícito a transcribir números sin poder confirmarlos).

Las REGLAS DE CAMBIO de severidad sí están completas y verificadas contra
dos fuentes independientes (incluyendo 7 CFR 42.108, que reproduce la
misma lógica de switching rules de la norma).
"""

from dataclasses import dataclass

AQL_VALORES_VALIDOS = (0.065, 0.10, 0.15, 0.25, 0.40, 0.65, 1.0, 1.5, 2.5, 4.0, 6.5)
NIVELES_INSPECCION_GENERAL = ("I", "II", "III")
SEVERIDADES = ("normal", "reforzado", "reducido")

# Tabla A -- (lote_min, lote_max, {nivel: codigo_letra}). lote_max=None significa "en adelante".
_TABLA_A = [
    (2, 8,           {"I": "A", "II": "A", "III": "B"}),
    (9, 15,          {"I": "A", "II": "B", "III": "C"}),
    (16, 25,         {"I": "B", "II": "C", "III": "D"}),
    (26, 50,         {"I": "C", "II": "D", "III": "E"}),
    (51, 90,         {"I": "C", "II": "E", "III": "F"}),
    (91, 150,        {"I": "D", "II": "F", "III": "G"}),
    (151, 280,       {"I": "E", "II": "G", "III": "H"}),
    (281, 500,       {"I": "F", "II": "H", "III": "J"}),
    (501, 1200,      {"I": "G", "II": "J", "III": "K"}),
    (1201, 3200,     {"I": "H", "II": "K", "III": "L"}),
    (3201, 10000,    {"I": "J", "II": "L", "III": "M"}),
    (10001, 35000,   {"I": "K", "II": "M", "III": "N"}),
    (35001, 150000,  {"I": "L", "II": "N", "III": "P"}),
    (150001, 500000, {"I": "M", "II": "P", "III": "Q"}),
    (500001, None,   {"I": "N", "II": "Q", "III": "R"}),
]

# Tabla II-A (inspección NORMAL) -- codigo_letra: (tamaño_muestra, {aql: (Ac, Re)})
_TABLA_B_NORMAL = {
    "A": (2,    {2.5: (0, 1), 4.0: (0, 1), 6.5: (1, 2)}),
    "B": (3,    {1.5: (0, 1), 2.5: (0, 1), 4.0: (0, 1), 6.5: (1, 2)}),
    "C": (5,    {1.0: (0, 1), 1.5: (0, 1), 2.5: (0, 1), 4.0: (1, 2), 6.5: (2, 3)}),
    "D": (8,    {0.65: (0, 1), 1.0: (0, 1), 1.5: (0, 1), 2.5: (1, 2), 4.0: (2, 3), 6.5: (3, 4)}),
    "E": (13,   {0.40: (0, 1), 0.65: (0, 1), 1.0: (0, 1), 1.5: (1, 2), 2.5: (2, 3), 4.0: (3, 4), 6.5: (5, 6)}),
    "F": (20,   {0.25: (0, 1), 0.40: (0, 1), 0.65: (0, 1), 1.0: (1, 2), 1.5: (2, 3), 2.5: (3, 4), 4.0: (5, 6), 6.5: (7, 8)}),
    "G": (32,   {0.15: (0, 1), 0.25: (0, 1), 0.40: (0, 1), 0.65: (1, 2), 1.0: (2, 3), 1.5: (3, 4), 2.5: (5, 6), 4.0: (7, 8), 6.5: (10, 11)}),
    "H": (50,   {0.10: (0, 1), 0.15: (0, 1), 0.25: (0, 1), 0.40: (1, 2), 0.65: (2, 3), 1.0: (3, 4), 1.5: (5, 6), 2.5: (7, 8), 4.0: (10, 11), 6.5: (14, 15)}),
    "J": (80,   {0.065: (0, 1), 0.10: (0, 1), 0.15: (0, 1), 0.25: (1, 2), 0.40: (2, 3), 0.65: (3, 4), 1.0: (5, 6), 1.5: (7, 8), 2.5: (10, 11), 4.0: (14, 15), 6.5: (21, 22)}),
    "K": (125,  {0.065: (0, 1), 0.10: (0, 1), 0.15: (1, 2), 0.25: (2, 3), 0.40: (3, 4), 0.65: (5, 6), 1.0: (7, 8), 1.5: (10, 11), 2.5: (14, 15), 4.0: (21, 22)}),
    "L": (200,  {0.065: (0, 1), 0.10: (1, 2), 0.15: (2, 3), 0.25: (3, 4), 0.40: (5, 6), 0.65: (7, 8), 1.0: (10, 11), 1.5: (14, 15), 2.5: (21, 22)}),
    "M": (315,  {0.065: (1, 2), 0.10: (2, 3), 0.15: (3, 4), 0.25: (5, 6), 0.40: (7, 8), 0.65: (10, 11), 1.0: (14, 15), 1.5: (21, 22)}),
    "N": (500,  {0.065: (2, 3), 0.10: (3, 4), 0.15: (5, 6), 0.25: (7, 8), 0.40: (10, 11), 0.65: (14, 15), 1.0: (21, 22)}),
    "P": (800,  {0.065: (3, 4), 0.10: (5, 6), 0.15: (7, 8), 0.25: (10, 11), 0.40: (14, 15), 0.65: (21, 22)}),
    "Q": (1250, {0.065: (5, 6), 0.10: (7, 8), 0.15: (10, 11), 0.25: (14, 15), 0.40: (21, 22)}),
    "R": (2000, {0.065: (7, 8), 0.10: (10, 11), 0.15: (14, 15), 0.25: (21, 22)}),
}


class AQLError(ValueError):
    """Combinación de lote/nivel/AQL no válida o no cubierta por la tabla."""


@dataclass
class PlanMuestreo:
    codigo_letra: str
    tamano_muestra: int
    limite_aceptacion: int
    limite_rechazo: int


def obtener_codigo_letra(tamano_lote: int, nivel_inspeccion_general: str) -> str:
    if nivel_inspeccion_general not in NIVELES_INSPECCION_GENERAL:
        raise AQLError(f"Nivel de inspección general inválido: {nivel_inspeccion_general}")
    if tamano_lote < 2:
        raise AQLError("El tamaño de lote debe ser de al menos 2 unidades")

    for lote_min, lote_max, codigos in _TABLA_A:
        if tamano_lote >= lote_min and (lote_max is None or tamano_lote <= lote_max):
            return codigos[nivel_inspeccion_general]

    raise AQLError(f"No se encontró código de letra para el tamaño de lote {tamano_lote}")


def calcular_plan_muestreo(tamano_lote: int, nivel_inspeccion_general: str, aql: float) -> PlanMuestreo:
    if aql not in AQL_VALORES_VALIDOS:
        raise AQLError(f"AQL debe ser uno de: {', '.join(str(v) for v in AQL_VALORES_VALIDOS)}")

    codigo_letra = obtener_codigo_letra(tamano_lote, nivel_inspeccion_general)
    tamano_muestra, tabla_aql = _TABLA_B_NORMAL[codigo_letra]

    if aql not in tabla_aql:
        raise AQLError(
            f"La norma no define un plan para código de letra '{codigo_letra}' con AQL {aql} "
            f"(prueba con otro valor de AQL)"
        )

    ac, re = tabla_aql[aql]
    return PlanMuestreo(codigo_letra=codigo_letra, tamano_muestra=tamano_muestra, limite_aceptacion=ac, limite_rechazo=re)


def evaluar_resultado(defectos_encontrados: int, limite_aceptacion: int, limite_rechazo: int) -> str:
    if defectos_encontrados <= limite_aceptacion:
        return "aceptado"
    if defectos_encontrados >= limite_rechazo:
        return "rechazado"
    raise AQLError("El número de defectos cae en una zona indefinida entre Ac y Re")  # no debería pasar: Re = Ac + 1


def recalcular_severidad(resultados_recientes: list[str], severidad_actual: str) -> str:
    """Reglas de cambio (switching rules) de la norma, aplicadas sobre el
    historial reciente de resultados ('aceptado'/'rechazado'), del más
    reciente al más antiguo. Verificadas contra 7 CFR 42.108, que reproduce
    la misma lógica de switching rules de ANSI/ASQ Z1.4.

    - normal -> reforzado: si 2 de los últimos 5 lotes fueron rechazados.
    - reforzado -> normal: si los últimos 5 lotes bajo reforzado fueron aceptados.
    - normal -> reducido: si los últimos 10 lotes fueron aceptados (la norma también
      exige estabilidad de producción, que este sistema no modela todavía).
    - reducido -> normal: si el lote más reciente fue rechazado.
    """
    ultimos_5 = resultados_recientes[:5]
    ultimos_10 = resultados_recientes[:10]
    rechazados_en_5 = ultimos_5.count("rechazado")

    if severidad_actual == "reducido":
        if ultimos_5 and ultimos_5[0] == "rechazado":
            return "normal"
        return "reducido"

    if severidad_actual == "reforzado":
        if len(ultimos_5) == 5 and rechazados_en_5 == 0:
            return "normal"
        return "reforzado"

    if len(ultimos_10) == 10 and ultimos_10.count("rechazado") == 0:
        return "reducido"
    if rechazados_en_5 >= 2:
        return "reforzado"
    return "normal"