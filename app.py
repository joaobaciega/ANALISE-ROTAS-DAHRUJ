"""Simulador de visitas comerciais. Executar: python -m streamlit run app.py."""
from dataclasses import asdict
from datetime import time
from hashlib import sha256
from math import ceil
from pathlib import Path

import pandas as pd
import streamlit as st

from rotas.combustivel import estimar
from rotas.dados import ROOT, carregar, selecionar
from rotas.otimizador import Regras, otimizar
from rotas.planilha import filtrar, ler_clientes
from rotas.relatorios import excel, hora, html, numero, tabelas


st.set_page_config(page_title='Rotas · Planejamento comercial', page_icon='🚗', layout='wide')
st.markdown('''<style>
.block-container{padding-top:2.2rem;max-width:1450px}
h1{letter-spacing:-1.5px;font-weight:750!important}
[data-testid="stMetric"]{background:white;border:1px solid #e2e9ed;border-radius:14px;padding:18px}
[data-testid="stMetricLabel"]{color:#526b7a}
[data-testid="stSidebar"]{border-right:1px solid #e0e8eb}
.eyebrow{color:#087f72;font-size:12px;letter-spacing:2px;font-weight:700}
.base{background:#eaf3f1;border:1px solid #d2e7e0;border-radius:12px;padding:16px 20px;color:#214b45;margin-bottom:22px}
</style>''', unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def resolver_cache(distancias, tempos, regras):
    return otimizar(distancias, tempos, regras)


def minutos(value):
    return value.hour * 60 + value.minute


def mostrar_mapa(dias, pontos, dia_escolhido):
    registros = []
    for i, dia in enumerate(dias, 1):
        if dia_escolhido != 'Todos os dias' and dia_escolhido != f'Dia {i}':
            continue
        caminho = (0,) + dia.ordem + (0,)
        for ordem, j in enumerate(caminho):
            p = pontos[j]
            registros.append({'Longitude': p['lon'], 'Latitude': p['lat'], 'Dia': f'Dia {i}', 'Ordem': ordem,
                              'Loja': p['nome'], 'Parada': 'Base' if j == 0 else str(ordem), 'Endereço': p['endereco']})
    if not registros:
        return
    spec = {
        'height': 410,
        'encoding': {'x': {'field': 'Longitude', 'type': 'quantitative', 'scale': {'zero': False}, 'axis': {'format': '.2f'}},
                     'y': {'field': 'Latitude', 'type': 'quantitative', 'scale': {'zero': False}, 'axis': {'format': '.2f'}},
                     'color': {'field': 'Dia', 'type': 'nominal', 'scale': {'range': ['#087f72', '#317ac1', '#a06ac2', '#d58929', '#dd6270', '#5d7182']}},
                     'tooltip': [{'field': 'Dia'}, {'field': 'Parada'}, {'field': 'Loja'}, {'field': 'Endereço'}]},
        'layer': [{'mark': {'type': 'line', 'strokeWidth': 2, 'opacity': 0.5}, 'encoding': {'order': {'field': 'Ordem', 'type': 'quantitative'}}},
                  {'mark': {'type': 'point', 'filled': True, 'size': 150}},
                  {'mark': {'type': 'text', 'dy': -15, 'fontSize': 12}, 'encoding': {'text': {'field': 'Parada'}}}]
    }
    st.vega_lite_chart(pd.DataFrame(registros), spec, use_container_width=True)
    st.caption('Esquema geográfico offline. As linhas mostram a sequência das visitas, não o traçado das ruas. Os quilômetros vêm da matriz rodoviária salva. Passe o mouse pelos pontos para ver as lojas.')


def main():
    try:
        catalogo, matriz = carregar()
    except (OSError, ValueError, KeyError) as exc:
        st.error(f'Não foi possível carregar os dados locais: {exc}')
        st.stop()
    with st.sidebar:
        st.markdown('### ROTAS / COMERCIAL')
        st.caption('Simulação para apresentação ao representante')
        with st.expander('Planilha de clientes'):
            upload = st.file_uploader('Substituir planilha nesta sessão', type=['xlsx'])
            st.caption('Usa Endereço Clientes.xlsx por padrão. Novos CNPJs precisam de localização e matriz cadastradas. O arquivo original é preservado.')
        try:
            arquivo = upload.getvalue() if upload is not None else (ROOT / 'Endereço Clientes.xlsx').read_bytes()
            clientes = ler_clientes(arquivo)
        except Exception as exc:
            st.error(f'Falha ao ler a planilha: {exc}')
            st.stop()
        with st.form('configuracao'):
            st.markdown('#### Carteira de clientes')
            segmentos = sorted({c.segmento for c in clientes})
            marcas = sorted({c.marca for c in clientes})
            escolhidos = st.multiselect('Segmento', segmentos, default=segmentos)
            marcas_escolhidas = st.multiselect('Marca', marcas, default=marcas)
            incluir_ceasa = st.checkbox('Incluir Ceasa?', value=False,
                                        help='Identificada pelo preenchimento amarelo na planilha. Cada loja conta como uma visita, mesmo no mesmo endereço.')
            st.divider()
            st.markdown('#### Veículo e combustível')
            st.caption('Ford Fiesta 2012 · 1.0 Rocam · gasolina')
            consumo = st.number_input('Consumo médio (km/L)', 1.0, 30.0, float(catalogo['consumo_km_l']), 0.5)
            preco = st.number_input('Gasolina (R$/L)', 0.01, 30.0, float(catalogo['preco_gasolina']), 0.10, format='%.2f')
            st.caption('Reserva de 10% aplicada aos litros e ao custo.')
            with st.expander('Jornada e deslocamento'):
                inicio = st.time_input('Saída da base', time(8, 0))
                fim = st.time_input('Retorno máximo', time(18, 0))
                abertura = st.time_input('Visitas a partir de', time(9, 0), help='Premissa comum editável; várias lojas abrem o showroom às 9h. Não representa agendamento confirmado.')
                visita = st.number_input('Minutos por visita', 5, 240, 60, 5)
                almoco = st.number_input('Minutos de almoço', 0, 180, 60, 5)
                fator = st.slider('Fator sobre o tempo de deslocamento', 1.0, 3.0, 1.5, 0.1,
                                  help='1,5 significa 50% a mais sobre o tempo estático do OSRM. Premissa de simulação, sem previsão de trânsito. Não altera a quilometragem.')
                st.caption('Máximo fixo: 4 lojas/dia. Almoço após a segunda visita, ou após a única visita do dia.')
            calcular = st.form_submit_button('Calcular melhor roteiro', type='primary', use_container_width=True)
        st.caption('Dados locais · sem rastreamento · sem chave de API')

    st.markdown('<div class="eyebrow">PLANEJAMENTO DE VISITAS</div>', unsafe_allow_html=True)
    st.title('Menos deslocamento. Mais visitas.')
    st.write('Organize a carteira no menor número de dias e reduza os quilômetros entre as lojas.')
    st.markdown('<div class="base"><b>Saída e retorno todos os dias</b><br>SP-270, 8760 · Raposo Tavares · São Paulo – SP · 05576-100</div>', unsafe_allow_html=True)

    selecionados = filtrar(clientes, escolhidos, incluir_ceasa, marcas_escolhidas)
    if not selecionados:
        st.info('Nenhuma loja selecionada. Escolha pelo menos um segmento e uma marca, e clique em Calcular melhor roteiro.')
        st.stop()
    regras = Regras(minutos(inicio), minutos(fim), visita, almoco, minutos(abertura), fator)
    try:
        regras.validar()
        pontos, distancias, tempos = selecionar(selecionados, catalogo, matriz)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    assinatura = repr((sha256(arquivo).hexdigest(), [c.id for c in selecionados], regras, consumo, preco, distancias, tempos))
    if calcular or 'resultado' not in st.session_state:
        try:
            with st.spinner('Comparando os dias possíveis e a ordem das visitas…'):
                dias = resolver_cache(distancias, tempos, regras)
            st.session_state.resultado = {'assinatura': assinatura, 'dias': dias}
        except ValueError as exc:
            st.error(str(exc))
            st.stop()
    resultado = st.session_state.resultado
    if resultado['assinatura'] != assinatura:
        st.info('A planilha ou os parâmetros mudaram. Clique em Calcular melhor roteiro para atualizar a simulação.')
        st.stop()
    dias = resultado['dias']
    resumo, trechos, cronograma = tabelas(dias, pontos, distancias, tempos, regras, consumo, preco)
    total_km = sum(d.km for d in dias)
    gas = estimar(total_km, consumo, preco)
    for col, titulo, valor, rodape in zip(st.columns(4),
             ['DIAS DE VISITA', 'LOJAS SELECIONADAS', 'DISTÂNCIA TOTAL', 'GASOLINA COM RESERVA'],
             [str(len(dias)), str(len(selecionados)), numero(total_km) + ' km', 'R$ ' + numero(gas.custo_reserva, 2)],
             [f'Mínimo por capacidade: {ceil(len(selecionados) / 4)}', 'Até 4 visitas por dia', 'Inclui ida e retorno à base', numero(gas.litros_reserva, 2) + ' L · margem de 10%']):
        col.metric(titulo, valor)
        col.caption(rodape)
    st.caption('Ótimo exato para a matriz e as premissas desta simulação: primeiro o menor número de dias viáveis, depois a menor soma de quilômetros. Os dias são intercambiáveis; não há calendário ou rodízio de placa aplicado.')

    aba_rotas, aba_custos, aba_clientes, aba_premissas = st.tabs(['Roteiros por dia', 'Combustível e custos', 'Endereços e fontes', 'Premissas e exportação'])
    with aba_rotas:
        left, right = st.columns([1.45, 1])
        with left:
            st.subheader('Distribuição das visitas')
            escolhido = st.selectbox('Visualizar', ['Todos os dias'] + [f'Dia {i}' for i in range(1, len(dias) + 1)])
            mostrar_mapa(dias, pontos, escolhido)
        with right:
            st.subheader('Visão do ciclo')
            for i, dia in enumerate(dias, 1):
                with st.container(border=True):
                    custo = estimar(dia.km, consumo, preco)
                    st.markdown(f'**Dia {i}** · {len(dia.ordem)} lojas · {numero(dia.km)} km')
                    st.write(' → '.join(pontos[j]['nome'] for j in dia.ordem))
                    st.caption(f'{hora(regras.inicio)}–{hora(dia.retorno)} · Gasolina: R$ {numero(custo.custo_reserva, 2)} com reserva')
        st.subheader('Agenda e trajetos')
        for i, dia in enumerate(dias, 1):
            with st.expander(f'Dia {i} · {numero(dia.km)} km · retorno às {hora(dia.retorno)}', expanded=i == 1):
                st.dataframe(cronograma[cronograma.Dia == i].drop(columns='Dia'), hide_index=True, use_container_width=True)
                st.caption('Distâncias e combustível por trecho, incluindo o retorno:')
                st.dataframe(trechos[trechos.Dia == i].drop(columns='Dia'), hide_index=True, use_container_width=True,
                             column_config={'Distância (km)': st.column_config.NumberColumn(format='%.2f'), 'Direção (min)': st.column_config.NumberColumn(format='%.0f'),
                                            'Gasolina +10% (L)': st.column_config.NumberColumn(format='%.2f'), 'Custo +10% (R$)': st.column_config.NumberColumn(format='R$ %.2f')})
    with aba_custos:
        st.subheader('Orçamento de gasolina')
        st.dataframe(resumo.drop(columns=['Roteiro', 'Saída', 'Retorno', 'Direção (min)']), hide_index=True, use_container_width=True)
        a, b, c = st.columns(3)
        a.metric('Custo sem reserva', 'R$ ' + numero(gas.custo_base, 2))
        b.metric('Reserva adicional de 10%', 'R$ ' + numero(gas.custo_reserva - gas.custo_base, 2))
        c.metric('Orçamento do ciclo', 'R$ ' + numero(gas.custo_reserva, 2))
        st.code('litros = quilômetros ÷ consumo em km/L\nlitros com reserva = litros × 1,10\ncusto com reserva = litros com reserva × preço por litro', language=None)
        st.caption('Valores referentes a um ciclo completo de visitas. Pedágios, estacionamento, manutenção e alimentação não estão incluídos. A margem é aplicada uma única vez; totais são calculados antes do arredondamento.')
    with aba_clientes:
        st.subheader('Carteira e endereços pesquisados')
        cadastro = {p['id']: p for p in catalogo['pontos']}
        registros = []
        for c in clientes:
            p = cadastro.get(c.id, {})
            registros.append({'Loja': p.get('nome', c.nome), 'CNPJ': c.cnpj, 'Segmento': c.segmento, 'Marca': c.marca,
                              'CEASA': c.ceasa, 'No roteiro': c.id in {x.id for x in selecionados},
                              'Endereço pesquisado': p.get('endereco', 'Não cadastrado'), 'Endereço original': c.endereco,
                              'Fonte': p.get('fonte', ''), 'Observações': p.get('observacao', '')})
        st.dataframe(pd.DataFrame(registros), hide_index=True, use_container_width=True, column_config={'Fonte': st.column_config.LinkColumn()})
        st.caption('A planilha original é preservada. Os números e as coordenadas ficam em dados/catalogo.json, associados por CNPJ. Cores amarelas definem CEASA; lojas próximas continuam sendo visitas independentes.')
        for p in pontos:
            if p['observacao']:
                st.markdown(f"**{p['nome']}** — {p['observacao']}")

    premissas = {'Origem e retorno': pontos[0]['endereco'], 'Segmentos': ', '.join(escolhidos), 'Marcas': ', '.join(marcas_escolhidas),
                'Incluir CEASA': 'Sim' if incluir_ceasa else 'Não', 'Máximo de lojas/dia': 4,
                'Jornada': f'{hora(regras.inicio)} às {hora(regras.fim)}', 'Visitas a partir de': hora(regras.abertura),
                'Minutos por visita': visita, 'Almoço (min)': almoco, 'Posição do almoço': 'Após a segunda visita, ou após a única visita do dia',
                'Fator de tempo': fator, 'Consumo km/L': consumo, 'Preço R$/L': preco, 'Reserva combustível': '10%',
                'Método': 'Otimização exata dos agrupamentos e ordens na matriz estática; minimiza dias antes de quilômetros',
                'Matriz': matriz['nota'], 'Dados de ruas': '© OpenStreetMap contributors · ODbL · OSRM',
                'Pesquisa': catalogo['data_pesquisa'], 'Referência consumo': catalogo['consumo_nota'],
                'Fonte consumo': catalogo['consumo_fonte'], 'Referência preço': catalogo['preco_nota'], 'Fonte preço': catalogo['preco_fonte'],
                'Limitações': 'Sem trânsito real, rodízio, pedágios ou agendamentos individuais. Endereços e entradas com divergências estão listados no relatório.'}
    with aba_premissas:
        st.subheader('Pronto para apresentar')
        a, b = st.columns(2)
        a.download_button('Baixar Excel completo', excel(resumo, trechos, cronograma, pontos, premissas), 'roteiros_visitas.xlsx',
                          'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)
        b.download_button('Baixar apresentação / imprimir PDF', html(resumo, trechos, cronograma, pontos, premissas), 'plano_visitas.html', 'text/html', use_container_width=True)
        st.caption('Abra o HTML no navegador e use “Imprimir / salvar como PDF”. A apresentação também funciona sem internet.')
        st.markdown('**Combustível**')
        st.write(catalogo['consumo_nota'])
        st.markdown(f"[Ficha consultada do Fiesta]({catalogo['consumo_fonte']})")
        st.write(catalogo['preco_nota'])
        st.markdown(f"[Boletim ANP, semana de 04 a 10/10/2026]({catalogo['preco_fonte']})")
        st.markdown('**Distâncias e horários**')
        st.write(matriz['nota'])
        st.write('O fator de tempo padrão de 1,5 é uma hipótese de planejamento, não uma previsão de congestionamento. A abertura comum às 9h é editável. Não foram impostas janelas específicas por loja.')
        st.markdown('[OSRM — metodologia da matriz](https://project-osrm.org/docs/v26.5.0/http) · [© OpenStreetMap contributors](https://www.openstreetmap.org/copyright)')
        st.dataframe(pd.DataFrame(list(premissas.items()), columns=['Premissa', 'Valor']).astype(str), hide_index=True, use_container_width=True)
    st.divider()
    st.caption('SIMULAÇÃO COMERCIAL · Dados pesquisados em 13/10/2026 · Processamento local em Python e Streamlit')


if __name__ == '__main__':
    main()
