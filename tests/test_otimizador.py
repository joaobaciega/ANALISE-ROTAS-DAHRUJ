from itertools import combinations, permutations
from math import ceil
import random

import pytest

from rotas.otimizador import Regras, agenda, otimizar


def brute_force(d, t, regras):
    """Oráculo independente para carteiras pequenas: toda ordem e todo corte."""
    n = len(d) - 1
    best = (float('inf'), float('inf'))
    for order in permutations(range(1, n + 1)):
        for cuts_mask in range(1 << (n - 1)):
            ends = [i + 1 for i in range(n - 1) if cuts_mask & (1 << i)] + [n]
            start, km, feasible = 0, 0.0, True
            for end in ends:
                group = order[start:end]
                if len(group) > 4:
                    feasible = False
                    break
                if agenda(group, t, regras)[-1]['fim'] > regras.fim:
                    feasible = False
                    break
                path = (0,) + group + (0,)
                km += sum(d[a][b] for a, b in zip(path, path[1:]))
                start = end
            if feasible:
                best = min(best, (len(ends), km))
    return best


@pytest.mark.parametrize('limite', [1080, 720])
def test_otimo_direcional_igual_busca_exaustiva(limite):
    rng = random.Random(42)
    d = [[0 if i == j else rng.randint(1, 40) for j in range(6)] for i in range(6)]
    t = [[v / 2 for v in row] for row in d]
    regras = Regras(fim=limite, abertura=480, fator_tempo=1)
    dias = otimizar(d, t, regras)
    expected = brute_force(d, t, regras)
    assert len(dias) == expected[0]
    assert sum(dia.km for dia in dias) == pytest.approx(expected[1])
    assert sorted(i for dia in dias for i in dia.ordem) == list(range(1, 6))
    for dia in dias:
        assert len(dia.ordem) <= 4
        assert agenda(dia.ordem, t, regras)[-1]['fim'] == pytest.approx(dia.retorno)


def test_jornada_pode_exigir_mais_dias():
    d = [[0 if i == j else 10 for j in range(5)] for i in range(5)]
    regras = Regras(fim=720, abertura=480, fator_tempo=1)
    dias = otimizar(d, d, regras)
    assert len(dias) == 2
    assert all(d.retorno <= 720 for d in dias)


def test_dia_impossivel_e_matriz_invalida():
    with pytest.raises(ValueError, match='Não existe'):
        otimizar([[0, 300], [300, 0]], [[0, 300], [300, 0]])
    with pytest.raises(ValueError, match='ausentes'):
        otimizar([[0, None], [10, 0]], [[0, 5], [5, 0]])
    assert otimizar([[0]], [[0]]) == []


def test_espera_almoco_retorno_e_consumo():
    from rotas.combustivel import estimar
    regras = Regras()
    eventos = agenda((1,), [[0, 10], [20, 0]], regras)
    assert any(e['tipo'] == 'Espera pela abertura' for e in eventos)
    almoco = [e for e in eventos if e['tipo'] == 'Almoço']
    assert len(almoco) == 1 and almoco[0]['fim'] - almoco[0]['inicio'] == 60
    assert eventos[-1]['fim'] == 690
    c = estimar(120, 12, 6.34)
    assert c.litros_reserva == 11
    assert c.custo_reserva == pytest.approx(69.74)
    with pytest.raises(ValueError):
        estimar(10, 0, 6)
