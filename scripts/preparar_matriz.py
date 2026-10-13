"""Consulta pontual OSRM; o app usa somente o JSON salvo (sem rede).

Executar manualmente apenas ao revisar o catálogo. Não agenda atualizações.
"""
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]

def main():
    catalogo = json.loads((ROOT / 'dados/catalogo.json').read_text(encoding='utf-8'))
    pontos = catalogo['pontos']
    coords = ';'.join(f"{p['lon']},{p['lat']}" for p in pontos)
    url = f'https://router.project-osrm.org/table/v1/driving/{coords}'
    response = requests.get(url, params={'annotations': 'distance,duration'}, timeout=50,
                            headers={'User-Agent': 'RotasDahruj-Simulacao/1.0'})
    response.raise_for_status()
    raw = response.json()
    if raw.get('code') != 'Ok':
        raise ValueError(f"OSRM não calculou a matriz: {raw.get('code')}")
    if any(x is None for key in ('distances', 'durations') for row in raw[key] for x in row):
        raise ValueError('Há pontos sem conexão rodoviária. Matriz anterior preservada.')
    matriz = {'ids': [p['id'] for p in pontos], 'coordenadas': [[p['lat'], p['lon']] for p in pontos],
              'data_preparacao': '2026-10-13', 'provedor': 'OSRM / OpenStreetMap',
              'nota': 'Distâncias rodoviárias dos caminhos de menor tempo do perfil driving do OSRM, sem trânsito em tempo real. O otimizador minimiza a soma dessas distâncias. Não garante o menor caminho por todas as ruas possíveis. Pontos aproximados estão identificados no catálogo.',
              'fonte': 'https://project-osrm.org/docs/v26.5.0/http',
              'distancias_km': [[v / 1000 for v in row] for row in raw['distances']],
              'tempos_min': [[v / 60 for v in row] for row in raw['durations']],
              'pontos_ajustados': [{'nome': p['name'], 'distancia_ajuste_m': p['distance'], 'lon_lat': p['location']} for p in raw['sources']]}
    (ROOT / 'dados/matriz.json').write_text(json.dumps(matriz, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Matriz salva:',len(pontos),'x',len(pontos))
    print('Ajustes à malha (m):',[round(p['distance']) for p in raw['sources']])

if __name__ == '__main__':
    main()
