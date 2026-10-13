"""Relatórios locais em Excel e HTML imprimível, com premissas e fontes."""
from dataclasses import asdict
from html import escape
from io import BytesIO
from math import ceil

import pandas as pd
from rotas.combustivel import estimar
from rotas.otimizador import agenda


def numero(v, casas=1):
    return f'{v:,.{casas}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def hora(minutos):
    total = ceil(minutos - 1e-8)
    return f'{total // 60:02d}:{total % 60:02d}'


def tabelas(dias, pontos, distancias, tempos, regras, consumo, preco):
    resumo, trechos, cronograma = [], [], []
    for i, dia in enumerate(dias, 1):
        combustivel = estimar(dia.km, consumo, preco)
        resumo.append({'Dia': i, 'Lojas': len(dia.ordem), 'Roteiro': ' → '.join(pontos[j]['nome'] for j in dia.ordem),
                       'Distância (km)': dia.km, 'Direção (min)': dia.minutos_direcao,
                       'Saída': hora(regras.inicio), 'Retorno': hora(dia.retorno),
                       'Gasolina base (L)': combustivel.litros_base, 'Gasolina +10% (L)': combustivel.litros_reserva,
                       'Custo base (R$)': combustivel.custo_base, 'Custo +10% (R$)': combustivel.custo_reserva})
        caminho = (0,) + dia.ordem + (0,)
        for etapa, (a, b) in enumerate(zip(caminho, caminho[1:]), 1):
            gas = estimar(distancias[a][b], consumo, preco)
            trechos.append({'Dia': i, 'Trecho': etapa, 'Origem': pontos[a]['nome'], 'Destino': pontos[b]['nome'],
                            'Endereço destino': pontos[b]['endereco'], 'Distância (km)': distancias[a][b],
                            'Direção (min)': tempos[a][b] * regras.fator_tempo,
                            'Gasolina +10% (L)': gas.litros_reserva, 'Custo +10% (R$)': gas.custo_reserva})
        for evento in agenda(dia.ordem, tempos, regras):
            cronograma.append({'Dia': i, 'Atividade': evento['tipo'], 'Local': pontos[evento['ponto']]['nome'],
                               'Início': hora(evento['inicio']), 'Fim': hora(evento['fim'])})
    return pd.DataFrame(resumo), pd.DataFrame(trechos), pd.DataFrame(cronograma)


def excel(resumo, trechos, cronograma, pontos, premissas):
    stream = BytesIO()
    with pd.ExcelWriter(stream, engine='openpyxl') as writer:
        for nome, df in [('Resumo', resumo), ('Trechos', trechos), ('Agenda', cronograma),
                         ('Endereços e fontes', pd.DataFrame(pontos)), ('Premissas', pd.DataFrame(list(premissas.items()), columns=['Parâmetro', 'Valor']))]:
            df.to_excel(writer, sheet_name=nome, index=False)
            sheet = writer.sheets[nome]
            sheet.freeze_panes = 'A2'
            sheet.auto_filter.ref = sheet.dimensions
            for row in sheet.iter_rows():
                for cell in row:
                    # Conteúdo da planilha do usuário nunca vira fórmula no relatório.
                    if cell.data_type == 'f':
                        cell.data_type = 's'
                    if isinstance(cell.value, float):
                        cell.number_format = '0.00'
            for col in sheet.columns:
                sheet.column_dimensions[col[0].column_letter].width = min(65, max(16, max(len(str(c.value or '')) for c in col[:30]) + 2))
    return stream.getvalue()


def html(resumo, trechos, cronograma, pontos, premissas):
    total_km = resumo['Distância (km)'].sum()
    total_rs = resumo['Custo +10% (R$)'].sum()
    partes = ['<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Plano de visitas</title>',
              '<style>body{font:15px Arial,sans-serif;color:#15283a;max-width:1100px;margin:40px auto;padding:0 24px}h1{font-size:36px}h2{margin-top:32px}table{border-collapse:collapse;width:100%;font-size:12px;margin:18px 0}th,td{padding:9px;border-bottom:1px solid #dce4e9;text-align:left}th{background:#edf4f5}.hero{padding:28px;background:#e9f5f1;border-radius:16px}.note{color:#536575}section{break-inside:avoid}@media print{body{margin:0}button{display:none}a{color:inherit}}</style>',
              '<button onclick="window.print()">Imprimir / salvar como PDF</button>',
              f'<div class="hero"><p>PLANEJAMENTO COMERCIAL · SIMULAÇÃO</p><h1>Plano de visitas</h1><p>{len(resumo)} dias · {int(resumo["Lojas"].sum())} lojas · {numero(total_km)} km · R$ {numero(total_rs, 2)} com reserva de 10%</p></div>',
              '<p class="note">Saída e retorno diários à base. Estimativas com dados estáticos; sem acompanhamento de trânsito.</p>']
    for _, row in resumo.iterrows():
        dia = row['Dia']
        partes.extend([f'<section><h2>Dia {dia} · {numero(row["Distância (km)"])} km · R$ {numero(row["Custo +10% (R$)"], 2)}</h2>',
                       f'<p>{escape(row["Roteiro"])}</p>', cronograma[cronograma['Dia'] == dia].drop(columns='Dia').to_html(index=False, escape=True),
                       trechos[trechos['Dia'] == dia].drop(columns='Dia').to_html(index=False, escape=True, float_format=lambda v: numero(v, 2)), '</section>'])
    partes.append('<h2>Premissas</h2><ul>')
    partes.extend(f'<li><b>{escape(str(k))}:</b> {escape(str(v))}</li>' for k, v in premissas.items())
    partes.append('</ul><h2>Endereços e fontes</h2>')
    partes.append(pd.DataFrame(pontos)[['nome', 'endereco', 'fonte', 'observacao']].to_html(index=False, escape=True))
    partes.append('</html>')
    return '\n'.join(partes).encode('utf-8')
