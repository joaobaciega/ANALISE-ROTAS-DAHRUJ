# Simulador de rotas comerciais

Aplicativo local em **Python e Streamlit** para simular visitas da carteira da planilha `Endereço Clientes.xlsx`. Não rastreia o representante e não consulta mapas, preço de combustível ou trânsito durante a utilização.

## Abrir

Neste computador, as dependências já estão disponíveis. Dê dois cliques em **`iniciar.bat`**, mantenha a janela aberta e acesse **http://localhost:8501** no navegador.

Também pode iniciar pelo terminal, dentro desta pasta:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Em outra máquina, instale Python 3.11 ou superior e as dependências. A instalação inicial exige internet; as simulações e os relatórios usam arquivos locais. O projeto foi verificado com Python 3.14 e Streamlit 1.58.

## Usar

1. Selecione segmentos e marcas na lateral.
2. Marque **Incluir Ceasa?** apenas quando quiser incluir as lojas amarelas. O padrão é desmarcado.
3. Ajuste consumo, preço e, se necessário, as premissas da jornada.
4. Clique em **Calcular melhor roteiro**. Na primeira abertura, o cenário padrão é calculado automaticamente.
5. Consulte sequência, agenda, quilômetros e combustível por dia e por trecho.
6. Em **Premissas e exportação**, baixe o Excel ou a apresentação HTML. Abra o HTML no navegador e use o botão de impressão para salvar como PDF.

O filtro de segmento lê os valores reais do Excel, atualmente DAHRUJ e DEALER. O filtro de marca reconhece BYD, Fiat, Jeep, Honda e Nissan. Cada CNPJ é uma visita independente, inclusive em endereços compartilhados.

## Regras da simulação

- Base diária: SP-270, 8760 - Raposo Tavares, São Paulo - SP, 05576-100.
- Saída às 8h e retorno até 18h, editáveis.
- Máximo de quatro lojas por dia.
- Uma hora por visita e uma hora de almoço, editáveis.
- Almoço após a segunda visita; em dias de uma visita, após essa visita. Não há janela fixa de almoço ao meio-dia.
- Início das visitas às 9h como premissa comum editável, pois várias lojas publicam abertura do showroom nesse horário. Não é confirmação de atendimento/agendamento individual.
- Tempo de condução padrão: tempo estático OSRM × 1,5. Os 50% são uma hipótese de planejamento, não medição ou previsão de trânsito.
- Consumo inicial: **12 km/L**, referência urbana de ficha técnica secundária do Fiesta hatch 1.0 Rocam 2011–2013. Não é medição do carro do representante; diminua o valor para testar consumo mais alto.
- Gasolina inicial: **R$ 6,34/L**, média da cidade de São Paulo no boletim ANP de 04 a 10/10/2026. O preço fica congelado até ser editado.
- Litros e custo recebem reserva de **10% uma única vez**. Os quilômetros não recebem essa margem.

```text
litros base = distância total / consumo
litros com reserva = litros base × 1,10
custo com reserva = litros com reserva × preço do litro
```

O custo inclui a saída e a volta à base. Não inclui pedágios, estacionamento, alimentação ou manutenção. Não há rodízio de placa, calendário, feriados nem restrições de atendimento por loja.

## Otimização e limites

O programa enumera todos os grupos de até quatro lojas e todas as ordens possíveis dentro de cada grupo. Descarta os dias que não cabem na jornada e usa programação dinâmica para encontrar uma partição da carteira que minimiza **primeiro o número de dias**, **depois a soma dos quilômetros**. O resultado é exato **para a matriz e as premissas informadas**, com suporte a até 20 lojas por simulação.

A matriz é direcional: ida e volta podem ter distâncias diferentes. Foi preparada uma única vez com OSRM/OpenStreetMap e salva em `dados/matriz.json`. As distâncias são dos caminhos de menor tempo do perfil rodoviário do provedor; não representam uma busca por todas as alternativas de menor distância da malha urbana. O aplicativo não faz novas chamadas ao provedor.

O gráfico offline mostra a ordem dos pontos, com linhas esquemáticas, não o desenho das ruas. Os quilômetros são rodoviários, não distâncias em linha reta.

## Endereços e ressalvas

A planilha original é preservada. Os endereços pesquisados, fontes, coordenadas e ressalvas ficam em `dados/catalogo.json`, associados por **CNPJ**, não pela posição das linhas. A carteira atual tem 19 lojas, incluindo duas DEALER; sem CEASA, são 14 visitas. A Nissan Braz Leme foi removida após informação de fechamento pelo usuário e não integra o catálogo, a matriz nem os roteiros.

**BYD Santo Amaro:** adotado o endereço comercial de pós-vendas publicado pela BYD na Av. Santo Amaro, 354, coerente com a avenida da planilha. Há cadastro do CNPJ na Rua Clodomiro Amazonas, 964; confira qual acesso deve ser visitado.

Outras diferenças de entradas e números estão indicadas na aba **Endereços e fontes**. BYD Aeroporto e Jeep Interlagos têm o mesmo ponto no material cartográfico publicado; ainda assim são duas visitas.

Upload de Excel vale apenas para a sessão. Uma loja sem localização/matriz provoca uma mensagem explícita; o app não a remove silenciosamente. Reordenar as linhas não altera a associação. Alterar um endereço para outro local físico exige revisar catálogo e matriz, pois o vínculo por CNPJ permanece.

Para revisar os dados, há scripts separados de preparação. Eles **não são executados pelo aplicativo**:

```powershell
python scripts/preparar_catalogo.py
python scripts/preparar_matriz.py
```

O primeiro reproduz os dados pesquisados e substitui o catálogo; edite seu dicionário por CNPJ para mudanças permanentes. O segundo exige internet e salva uma nova matriz após validação. Atualize as datas de preparação quando fizer uma nova pesquisa. O carregamento recusa catálogo com coordenadas diferentes das usadas na matriz.

## Fontes

- [BYD Dahruj](https://www.byddahruj.com.br/contato/fale-conosco)
- [Fiat Ventuno](https://www.ventuno.com.br/institucional/entre-em-contato)
- [Jeep Dahruj](https://www.jeepdahruj.com.br/)
- [Honda Forte](https://www.hondaforte.com.br/)
- [Nissan Dahruj](https://www.nissandahruj.com.br/fale-conosco/)
- [BYD Grupo Dealer](https://www.dealerbyd.com.br/contato/fale-conosco)
- [Ficha técnica consultada do Fiesta](https://www.shopcar.com.br/fichatecnica.php?id=76)
- [ANP — boletim 41/2026, página 3](https://www.gov.br/anp/pt-br/assuntos/precos-e-defesa-da-concorrencia/precos/arq-sintese-semanal/2026/sintese-precos-41.pdf)
- [OSRM — documentação da matriz](https://project-osrm.org/docs/v26.5.0/http)
- Dados rodoviários: [© OpenStreetMap contributors, licença ODbL](https://www.openstreetmap.org/copyright).

## Verificação

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Os testes comparam o otimizador com busca exaustiva independente em carteiras pequenas, verificam jornada inviável, assimetria, cobertura de todas as lojas, filtros e cores do Excel, aplicação da reserva, exportação e interação da interface sem chamadas de rede.

Arquivos principais: `app.py` (interface), `rotas/otimizador.py` (cálculo), `rotas/planilha.py` (Excel), `rotas/relatorios.py` (exportação), `dados/` (base estática).
