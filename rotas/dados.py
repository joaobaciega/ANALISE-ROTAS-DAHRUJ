"""Leitura e conferência da base estática; nenhuma chamada de rede."""
import json
from pathlib import Path
from rotas.otimizador import validar_matriz

ROOT = Path(__file__).resolve().parents[1]


def carregar():
    catalogo = json.loads((ROOT / 'dados/catalogo.json').read_text(encoding='utf-8'))
    matriz = json.loads((ROOT / 'dados/matriz.json').read_text(encoding='utf-8'))
    pontos = {p['id']: p for p in catalogo['pontos']}
    if len(set(matriz['ids'])) != len(matriz['ids']) or matriz['ids'][0] != 'base':
        raise ValueError('Identificadores inválidos na matriz salva.')
    for identifier, coords in zip(matriz['ids'], matriz['coordenadas'], strict=True):
        if identifier not in pontos or coords != [pontos[identifier]['lat'], pontos[identifier]['lon']]:
            raise ValueError('Catálogo e matriz incompatíveis. Prepare a matriz novamente após alterar coordenadas.')
    for key in ('distancias_km', 'tempos_min'):
        validar_matriz(matriz[key], len(matriz['ids']))
    return catalogo, matriz


def selecionar(clientes, catalogo, matriz):
    ids = ['base'] + [c.id for c in clientes]
    cadastro = {p['id']: p for p in catalogo['pontos']}
    missing = [c.nome for c in clientes if c.id not in cadastro or c.id not in matriz['ids']]
    if missing:
        raise ValueError('Lojas sem localização/matriz estática: ' + ', '.join(missing) + '. Cadastre-as antes de simular; nenhuma loja será omitida.')
    indices = [matriz['ids'].index(identifier) for identifier in ids]
    return ([cadastro[identifier] for identifier in ids],
            [[matriz['distancias_km'][i][j] for j in indices] for i in indices],
            [[matriz['tempos_min'][i][j] for j in indices] for i in indices])
