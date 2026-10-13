"""Reproduz o catálogo pesquisado em 13/10/2026. Não acessa a internet."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from rotas.planilha import ler_clientes

BYD = 'https://www.byddahruj.com.br/contato/fale-conosco'
JEEP = 'https://www.jeepdahruj.com.br/'
FIAT = 'https://www.ventuno.com.br/institucional/entre-em-contato'
NISSAN = 'https://www.nissandahruj.com.br/fale-conosco/'
# Referência histórica da pesquisa: endereço, latitude, longitude, fonte, ressalva.
# A associação com a planilha atual é feita por CNPJ abaixo.
PONTOS = {
 2: ('Av. Dr. Gastão Vidigal, 2351 - Vila Leopoldina', -23.5366667, -46.7316667, 'https://www.hondaforte.com.br/', ''),
 3: ('Av. Washington Luís, 3155 - Santo Amaro', -23.6503665, -46.6780125, BYD, 'O link oficial BYD aponta para o mesmo ponto do complexo Jeep/Fiat Aeroporto. Conferir a entrada específica; os números das fachadas diferem.'),
 4: ('Av. Aricanduva, 5555 - Jardim Santa Terezinha', -23.5649672, -46.5011287, BYD, ''),
 5: ('Av. Dr. Gastão Vidigal, 1687 - Vila Leopoldina', -23.5318098, -46.7358566, BYD, ''),
 6: ('Av. Santo Amaro, 354 - Vila Nova Conceição', -23.5871481, -46.6716849, BYD, 'Adotado o pós-vendas publicado pela BYD na avenida informada na planilha. Cadastro CNPJ também aparece na Rua Clodomiro Amazonas, 964. Conferir unidade antes de uso operacional.'),
 7: ('Praça Stélio Machado Loureiro, 111 - Vila Guilherme', -23.5162854, -46.6090159, BYD, ''),
 8: ('Av. Dr. Gastão Vidigal, 1703 - Vila Leopoldina', -23.5319747, -46.7358496, JEEP, 'Site da loja usa 1703; cadastro da montadora menciona 1687, setor B. Adotada a entrada comercial.'),
 9: ('Av. Aricanduva, 5555 - Jardim Santa Terezinha', -23.565932, -46.5006822, FIAT, ''),
 10: ('Av. Dr. Gastão Vidigal, 1725 - Vila Leopoldina', -23.5318086, -46.7359655, FIAT, ''),
 11: ('Av. das Nações Unidas, 22665 - Vila Almeida', -23.6781249, -46.6961277, FIAT, ''),
 12: ('Av. dos Autonomistas, 1473 - Vila Yara', -23.5415248, -46.7678871, FIAT, ''),
 13: ('Av. Aricanduva, 5555 - Jardim Santa Terezinha', -23.5664964, -46.5002245, JEEP, ''),
 14: ('Av. Guarulhos, 1814 - Gopoúva', -23.4832229, -46.543209, JEEP, ''),
 15: ('Av. Washington Luís, 3561 - Santo Amaro', -23.6503665, -46.6780125, JEEP, 'Interlagos na planilha corresponde à unidade comercial Aeroporto; número confirmado por cadastro CNPJ do Banco Alfa.'),
 16: ('Av. Sumaré, 611 - Perdizes', -23.5338989, -46.6742914, JEEP, ''),
 17: ('Av. Joaquina Ramalho, 8 - Vila Guilherme', -23.5166973, -46.6094551, 'https://www.jeep.com.br/servicos-financeiros/next-jeep.html', 'Endereço do CNPJ preservado. Coordenada do diretório Locais do Brasil, próxima à entrada comercial Norte, Praça Stélio Machado Loureiro, 51.'),
 19: ('Av. Dr. Gastão Vidigal, 1655 - Vila Leopoldina', -23.5321971, -46.735564, NISSAN, 'Site oficial usa 1655; comunicação da loja também cita 1687. Adotados endereço e ponto do site oficial.'),
 20: ('Av. Alcântara Machado, 576 - Mooca', -23.553013, -46.619383, 'https://www.dealerbyd.com.br/contato/fale-conosco', ''),
 21: ('Av. das Nações Unidas, 21599 - Vila Almeida', -23.6706016, -46.7029445, 'https://www.dealerbyd.com.br/contato/fale-conosco', 'Adotada entrada comercial 21599 do site oficial. Cadastro CNPJ menciona 21621.'),
}
IDS = ['07023175000163', '46621491001594', '46621491001160', '46621491000199',
       '46621491000431', '46621491001080', '05026792001240', '05026792000359',
       '05026792000197', '05026792000863', '05026792002211', '05026792001592',
       '05026792001754', '05026792001916', '05026792001320', '05026792002130',
       '07950180000383', '51919345000265', '51919345000184']
POR_CNPJ = {identifier: PONTOS[ref] for identifier, ref in zip(IDS, sorted(PONTOS), strict=True)}

def main():
    clientes = ler_clientes(ROOT / 'Endereço Clientes.xlsx')
    pontos = [{'id': 'base', 'nome': 'Base · Raposo Tavares', 'endereco': 'SP-270, 8760 - Raposo Tavares, São Paulo - SP, 05576-100',
               'lat': -23.5891066, 'lon': -46.795513, 'fonte': 'https://www.waze.com/live-map/directions/brazil/state-of-sao-paulo/sao-paulo/condominio-green-park?to=place.ChIJlXwQWRJVzpQRtubKijsdc0c', 'observacao': ''}]
    for c in clientes:
        endereco, lat, lon, fonte, nota = POR_CNPJ[c.id]
        nome = c.nome.rsplit(' - ', 1)[-1]
        if '(' in nome:
            nome = nome.split('(')[-1].rstrip(')') + ' · DEALER'
        pontos.append({'id': c.id, 'nome': nome, 'endereco': f'{endereco}, {c.cidade} - SP',
                       'lat': lat, 'lon': lon, 'fonte': fonte, 'observacao': nota})
    data = {'data_pesquisa': '2026-10-13', 'pontos': pontos,
            'consumo_km_l': 12.0, 'preco_gasolina': 6.34,
            'consumo_fonte': 'https://www.shopcar.com.br/fichatecnica.php?id=76',
            'consumo_nota': 'Referência de ficha técnica secundária para Fiesta hatch 1.0 Rocam 2011–2013: 12 km/l na cidade. Não é medição deste veículo. Ajuste para o consumo real; reserva adicional de 10% aplicada separadamente.',
            'preco_fonte': 'https://www.gov.br/anp/pt-br/assuntos/precos-e-defesa-da-concorrencia/precos/arq-sintese-semanal/2026/sintese-precos-41.pdf',
            'preco_nota': 'ANP, gasolina C comum, município de São Paulo, semana de 04 a 10/10/2026: R$ 6,34/l. Valor histórico fixo, editável.'}
    (ROOT / 'dados').mkdir(exist_ok=True)
    (ROOT / 'dados/catalogo.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Catálogo: {len(clientes)} lojas e uma base.')

if __name__ == '__main__':
    main()
