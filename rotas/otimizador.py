"""Solução exata: enumeração de dias e particionamento por programação dinâmica.

O ótimo se refere à matriz fornecida, não a todas as ruas da cidade.
Matrizes direcionais preservam diferenças entre ida e volta.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations, permutations
from math import ceil, inf, isfinite


@dataclass(frozen=True)
class Regras:
    inicio: int = 480
    fim: int = 1080
    visita: int = 60
    almoco: int = 60
    abertura: int = 540
    fator_tempo: float = 1.5
    max_lojas: int = 4

    def validar(self):
        if not 0 <= self.inicio < self.fim <= 1440:
            raise ValueError("O fim da jornada deve ser posterior ao início, no mesmo dia.")
        if self.visita <= 0 or self.almoco < 0 or not 1 <= self.max_lojas <= 4:
            raise ValueError("Duração inválida ou limite de lojas fora de 1 a 4.")
        if not isfinite(self.fator_tempo) or self.fator_tempo <= 0:
            raise ValueError("O fator de deslocamento deve ser positivo.")


@dataclass(frozen=True)
class Dia:
    ordem: tuple[int, ...]
    km: float
    minutos_direcao: float
    retorno: float


def agenda(ordem, tempos, regras: Regras) -> list[dict]:
    """Almoço após a segunda visita (ou após a última em dias de uma loja)."""
    agora = regras.inicio
    anterior = 0
    eventos = [{"tipo": "Saída da base", "ponto": 0, "inicio": agora, "fim": agora}]
    for pos, loja in enumerate(ordem):
        chegada = agora + tempos[anterior][loja] * regras.fator_tempo
        eventos.append({"tipo": "Deslocamento", "ponto": loja, "inicio": agora, "fim": chegada})
        inicio = max(chegada, regras.abertura)
        if inicio > chegada:
            eventos.append({"tipo": "Espera pela abertura", "ponto": loja, "inicio": chegada, "fim": inicio})
        agora = inicio + regras.visita
        eventos.append({"tipo": "Visita", "ponto": loja, "inicio": inicio, "fim": agora})
        if pos == min(1, len(ordem) - 1) and regras.almoco:
            eventos.append({"tipo": "Almoço", "ponto": loja, "inicio": agora, "fim": agora + regras.almoco})
            agora += regras.almoco
        anterior = loja
    retorno = agora + tempos[anterior][0] * regras.fator_tempo
    eventos.append({"tipo": "Retorno à base", "ponto": 0, "inicio": agora, "fim": retorno})
    return eventos


def validar_matriz(matriz, tamanho):
    if len(matriz) != tamanho or any(len(row) != tamanho for row in matriz):
        raise ValueError("Matriz com dimensões inválidas.")
    if any(v is None or not isfinite(v) or v < 0 for row in matriz for v in row):
        raise ValueError("A matriz contém distâncias/tempos ausentes ou inválidos.")
    if any(abs(matriz[i][i]) > 1e-8 for i in range(tamanho)):
        raise ValueError("A diagonal da matriz deve ser zero.")


def otimizar(distancias, tempos, regras: Regras = Regras()) -> list[Dia]:
    regras.validar()
    n = len(distancias) - 1
    if n < 0:
        raise ValueError("Inclua o ponto de partida na matriz.")
    if n > 20:
        raise ValueError("A otimização exata suporta até 20 lojas por simulação. Use os filtros.")
    validar_matriz(distancias, n + 1)
    validar_matriz(tempos, n + 1)
    if n == 0:
        return []
    candidatos = {}
    por_primeiro = [[] for _ in range(n)]
    for tamanho in range(1, min(regras.max_lojas, n) + 1):
        for grupo in combinations(range(1, n + 1), tamanho):
            melhor = None
            for ordem in permutations(grupo):
                caminho = (0,) + ordem + (0,)
                km = sum(distancias[a][b] for a, b in zip(caminho, caminho[1:]))
                if melhor is not None and km > melhor.km + 1e-9:
                    continue
                # Mesmo modelo de agenda, sem criar objetos para cada permutação.
                agora = regras.inicio
                anterior = 0
                for loja in ordem:
                    agora = max(agora + tempos[anterior][loja] * regras.fator_tempo, regras.abertura) + regras.visita
                    anterior = loja
                retorno = agora + regras.almoco + tempos[anterior][0] * regras.fator_tempo
                if retorno > regras.fim + 1e-8:
                    continue
                direcao = sum(tempos[a][b] for a, b in zip(caminho, caminho[1:])) * regras.fator_tempo
                dia = Dia(ordem, km, direcao, retorno)
                if melhor is None or (km, retorno, ordem) < (melhor.km, melhor.retorno, melhor.ordem):
                    melhor = dia
            if melhor is not None:
                mask = sum(1 << (i - 1) for i in grupo)
                candidatos[mask] = melhor
                por_primeiro[grupo[0] - 1].append((mask, melhor.km))
    # Toda partição tem exatamente um grupo contendo a menor loja restante.
    # Tenta o limite inferior de dias; aumenta apenas se a jornada o exigir.
    escolhas = {}
    @lru_cache(maxsize=None)
    def resolver(mask, dias):
        if not mask:
            return 0.0 if dias == 0 else inf
        count = mask.bit_count()
        if dias <= 0 or count > dias * regras.max_lojas or count < dias:
            return inf
        first = (mask & -mask).bit_length() - 1
        melhor = inf
        for subset, custo in por_primeiro[first]:
            if mask & subset != subset:
                continue
            restante = mask ^ subset
            if not dias - 1 <= restante.bit_count() <= (dias - 1) * regras.max_lojas:
                continue
            total = custo + resolver(restante, dias - 1)
            if total < melhor:
                melhor = total
                escolhas[mask, dias] = subset
        return melhor
    full = (1 << n) - 1
    for dias in range(ceil(n / regras.max_lojas), n + 1):
        if isfinite(resolver(full, dias)):
            resultado = []
            mask = full
            while mask:
                subset = escolhas[mask, dias]
                resultado.append(candidatos[subset])
                mask ^= subset
                dias -= 1
            return resultado
    raise ValueError("Não existe roteiro que atenda todas as lojas dentro da jornada. Aumente a jornada ou reduza a duração das visitas/deslocamentos.")
