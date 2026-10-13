"""Gera os relatórios padrão sem precisar abrir a interface."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rotas.dados import carregar, selecionar
from rotas.planilha import ler_clientes, filtrar
from rotas.otimizador import Regras, otimizar
from rotas.relatorios import tabelas, excel, html


def main():
    catalogo, matriz = carregar()
    todos = ler_clientes(ROOT / 'Endereço Clientes.xlsx')
    regras = Regras()
    destino = ROOT / 'saidas'
    destino.mkdir(exist_ok=True)
    for ceasa in [False, True]:
        clientes = filtrar(todos, sorted({c.segmento for c in todos}), ceasa)
        pontos, d, t = selecionar(clientes, catalogo, matriz)
        dias = otimizar(d, t, regras)
        resumo, trechos, cronograma = tabelas(dias, pontos, d, t, regras, catalogo['consumo_km_l'], catalogo['preco_gasolina'])
        premissas = {'Data da pesquisa': catalogo['data_pesquisa'], 'Base diária': pontos[0]['endereco'],
                    'Segmentos': ', '.join(sorted({c.segmento for c in clientes})), 'Marcas': 'Todas',
                    'CEASA': 'Incluída' if ceasa else 'Excluída', 'Jornada': '8h às 18h; visitas a partir das 9h',
                    'Visitas': '60 minutos; máximo 4 lojas/dia', 'Almoço': '60 minutos após a segunda visita (ou após a única visita)',
                    'Tempo de deslocamento': 'OSRM × 1,5; hipótese de simulação sem trânsito real',
                    'Consumo km/L': catalogo['consumo_km_l'], 'Gasolina R$/L': catalogo['preco_gasolina'], 'Reserva': '10%',
                    'Matriz': matriz['nota'], 'Método': 'Ótimo exato para a matriz: menor número de dias e depois menor quilometragem',
                    'Referência consumo': catalogo['consumo_nota'], 'Fonte consumo': catalogo['consumo_fonte'],
                    'Referência preço': catalogo['preco_nota'], 'Fonte preço': catalogo['preco_fonte'],
                    'Dados rodoviários': '© OpenStreetMap contributors · ODbL · OSRM',
                    'Limitações': 'Não inclui rodízio, pedágios, estacionamento ou agendamentos. Ver ressalvas dos endereços.'}
        nome = 'roteiro_com_ceasa' if ceasa else 'roteiro_sem_ceasa'
        (destino / (nome + '.xlsx')).write_bytes(excel(resumo, trechos, cronograma, pontos, premissas))
        (destino / (nome + '.html')).write_bytes(html(resumo, trechos, cronograma, pontos, premissas))
        print(nome, len(clientes), 'lojas;', len(dias), 'dias;', round(resumo['Distância (km)'].sum(), 2), 'km;', round(resumo['Custo +10% (R$)'].sum(), 2), 'reais')


if __name__ == '__main__':
    main()
