from typing import Optional

from pydantic import BaseModel


class OperacionesResumen(BaseModel):
    total: int
    por_estado: dict[str, int]
    tiempo_promedio_ciclo_minutos: Optional[float]  # creada -> finalizada
    tiempo_promedio_operativo_minutos: Optional[float]  # iniciada -> finalizada


class CalidadResumen(BaseModel):
    total_inspecciones: int
    tasa_aceptacion_pct: Optional[float]
    proveedores_en_reforzado: int


class FinancieroResumen(BaseModel):
    total_liquidado_historico: float
    total_pendiente_cobro: float


class DashboardOut(BaseModel):
    operaciones: OperacionesResumen
    calidad: CalidadResumen
    financiero: FinancieroResumen