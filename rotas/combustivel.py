"""Estimativas com margem aplicada aos litros e ao custo, uma única vez."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Combustivel:
    litros_base: float
    litros_reserva: float
    custo_base: float
    custo_reserva: float


def estimar(km: float, consumo_km_l: float, preco_litro: float) -> Combustivel:
    if not all(isfinite(v) for v in (km, consumo_km_l, preco_litro)):
        raise ValueError("Informe valores numéricos finitos.")
    if km < 0 or consumo_km_l <= 0 or preco_litro <= 0:
        raise ValueError("Distância deve ser não negativa; consumo e preço devem ser positivos.")
    litros = km / consumo_km_l
    return Combustivel(litros, litros * 1.10, litros * preco_litro, litros * preco_litro * 1.10)
