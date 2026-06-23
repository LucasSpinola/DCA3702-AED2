# Trabalho 3 (Projeto Final): RideSmart

Disciplina: DCA3702, Algoritmos e Estrutura de Dados II (UFRN).
Unidade 03, projeto final.

---

## 1. Integrantes

- Lucas Augusto Spinola Pinto
- João Pedro Araújo Ramalho
- Kiev Luiz Freitas Guedes
- Maria Eduarda Silva da Costa

## 2. Link do dashboard online

- Dashboard consolidado: https://lucasspinola.github.io/DCA3702-AED2/T3/results/index.html
- Mapa interativo com folium: https://lucasspinola.github.io/DCA3702-AED2/T3/results/rota_interativa.html

---

## 3. Problema abordado

O RideSmart é uma simulação inspirada em aplicativos de mobilidade urbana. Dado um ponto de origem A, um ponto de destino B e uma distância máxima X que o usuário aceita caminhar, o sistema escolhe o melhor ponto de embarque P, tal que P esteja a no máximo X metros de caminhada da origem A. A rota completa tem dois trechos:

```
A -> P  caminhando
P -> B  de carro
```

A pergunta de pesquisa é se vale a pena caminhar alguns metros para pegar o transporte em uma via mais rápida, ou se é melhor embarcar exatamente onde estamos. Para responder, o aluno precisa modelar o problema como grafo, definir pesos coerentes, comparar algoritmos de caminhos mínimos e analisar criticamente os resultados.

**Cenário escolhido:**
- Origem A: Setor de Aulas IV (UFRN, Lagoa Nova, Natal/RN).
- Destino B: Comando do 3o Distrito Naval (R. Cel. Flamínio, s/n, Santos Reis, Natal/RN, 59010-500).
- Distância máxima X: sweep em [0, 200, 500, 800, 1000] metros.

---

## 4. Modelagem do problema

### 4.1 Grafo

Usamos a biblioteca OSMnx para baixar a malha viária de Natal a partir do OpenStreetMap. A região coberta é um círculo de 10 km de raio em torno do ponto médio entre A e B, suficiente para englobar toda a rota viável e os candidatos a P.

Dois grafos são derivados do mesmo download:

- `G_drive`: rede de vias para carro (`network_type='drive'`), usada no trecho P para B.
- `G_walk`: rede de caminhada (`network_type='walk'`), usada no trecho A para P.

Cada nó tem coordenadas `(x, y)` (longitude e latitude). Cada aresta tem `length` em metros e `highway` indicando o tipo de via.

### 4.2 Pesos (funções de custo)

Em `G_drive`, cada aresta recebe três atributos de peso:

1. **length**: distância em metros (peso original do OSMnx).
2. **travel_time**: tempo em segundos sem trânsito, calculado por `length / speed_kph * 3,6`. Quando `maxspeed` está ausente, usamos defaults por tipo de via:
   - residential = 30 km/h
   - secondary = 50 km/h
   - primary = 60 km/h
   - trunk = 70 km/h
   - motorway = 80 km/h
3. **travel_time_synth**: tempo em segundos com trânsito sintético, igual ao `travel_time` multiplicado por um fator que depende do tipo de via.

### 4.3 Trânsito sintético correlacionado com tipo de via

Para simular um cenário de congestionamento realista, cada aresta recebe um fator multiplicativo amostrado de uma distribuição uniforme cuja faixa depende do `highway`:

| Tipo de via | Faixa do fator |
| --- | --- |
| motorway, trunk, primary | 1,5 a 2,5 |
| secondary, tertiary | 1,2 a 1,8 |
| residential, unclassified | 1,0 a 1,3 |

Avenidas e rodovias urbanas, que tendem a engarrafar primeiro, recebem fatores mais altos. Ruas residenciais mantêm velocidade próxima da nominal. A seed do gerador aleatório é fixa (`seed=42`) para garantir reprodutibilidade.

### 4.4 Pipeline RideSmart

Dado o par `(A, B)` e um valor `X`:

1. Encontrar o nó mais próximo de A em `G_walk` (chamado `no_a_walk`) e o nó mais próximo de B em `G_drive` (`no_b_drive`).
2. Calcular as distâncias de caminhada de `no_a_walk` para todos os outros nós de `G_walk`, usando Dijkstra com heap e o peso `length`. Filtrar os que estão a distância menor ou igual a X. Esses são os candidatos P.
3. Para cada candidato P:
   - Tempo a pé: `t_walk = d_walk / 5 km/h`.
   - Projetar P para `G_drive` (nó mais próximo) e calcular o caminho de carro de P para B.
   - Tempo de carro: `t_drive` (peso `travel_time` ou `travel_time_synth`).
   - Tempo total: `t_total = t_walk + t_drive`.
4. Escolher `P* = argmin(t_total)`.

---

## 5. Algoritmos implementados

Implementamos quatro algoritmos de caminho mínimo em `src/algorithms.py`. Todos têm a mesma assinatura e retornam o caminho, o custo, o número de nós expandidos e o tempo de execução em ms.

### 5.1 Dijkstra simples

Implementação didática com busca linear pelo nó com menor distância (sem heap). Complexidade O(V²). Serve para mostrar o trade-off contra a versão com fila de prioridade.

### 5.2 Dijkstra com fila de prioridade (heap)

Usa `heapq` da biblioteca padrão. Complexidade O(E log V). Marca nós visitados para não reexpandir.

### 5.3 A* com heurística geográfica (Haversine)

Mesma estrutura do Dijkstra com heap, mas a chave da fila é `f(n) = g(n) + h(n)`, onde:
- `g(n)`: tempo acumulado até n.
- `h(n) = haversine(n, target) / vmax_kph * 3,6`. A distância em metros do Haversine é convertida em segundos pela velocidade máxima do grafo, o que garante que a heurística é admissível (nunca superestima o custo real).

### 5.4 Dijkstra Bidirecional (algoritmo adicional)

Avança duas buscas em paralelo: uma a partir de `source`, outra a partir de `target` no grafo reverso. Para quando a soma dos topos das duas filas atinge o melhor candidato encontrado. Em grafos grandes, costuma expandir aproximadamente metade dos nós do Dijkstra unidirecional.

---

## 6. Experimentos e principais resultados

### 6.1 Comparação dos 4 algoritmos (A para B sem caminhada, peso `travel_time`)

| Algoritmo | Custo (s) | Nós expandidos | Tempo (ms) |
| --- | ---: | ---: | ---: |
| Dijkstra simples | 714,37 | 11.885 | 14.321,6 |
| Dijkstra com heap | 714,37 | 11.886 | 37,3 |
| A* | 714,37 | 4.799 | 50,9 |
| Dijkstra Bidirecional | 714,37 | 5.079 | 17,2 |

Todos chegam ao mesmo custo ótimo (714 segundos, ou 11,9 minutos), o que confirma que estão corretos. O Dijkstra simples leva mais de 14 segundos para um par (custa caro pelo O(V²)). As outras três versões rodam em menos de 60 ms.

### 6.2 Cenário com trânsito sintético

Usando `travel_time_synth` (peso multiplicado pelo fator de trânsito):

- Tempo A para B: 1.211,8 segundos (cerca de 20,2 minutos).
- O trânsito sintético deixou a rota cerca de 70% mais lenta do que sem trânsito (714 s para 1.212 s).
- O caminho ótimo escolhido é praticamente igual (113 nós, distância de 10,6 km), mas o tempo total muda.

### 6.3 Sweep em X (RideSmart)

| X (m) | Cenário | Tempo total (s) | Ganho percentual |
| ---: | --- | ---: | ---: |
| 0 | sem trânsito | 714,4 | 0,00 |
| 200 | sem trânsito | 714,4 | 0,00 |
| 500 | sem trânsito | 714,4 | 0,00 |
| 800 | sem trânsito | 714,4 | 0,00 |
| 1000 | sem trânsito | 714,4 | 0,00 |
| 0 | com trânsito | 1.211,8 | 0,00 |
| 200 | com trânsito | 1.211,8 | 0,00 |
| 500 | com trânsito | 1.211,8 | 0,00 |
| 800 | com trânsito | 1.211,8 | 0,00 |
| 1000 | com trânsito | 1.211,8 | 0,00 |

Resultado interessante: para esse cenário específico, caminhar não melhora o tempo total da rota. A explicação é simples. O Setor de Aulas IV (UFRN) está colado na BR-101 e na Avenida Senador Salgado Filho, que são justamente as vias mais rápidas da região. O nó projetado de A em `G_drive` cai já em uma via principal. Qualquer P alternativo dentro de 1 km cai em vias secundárias ou residenciais mais lentas, e o ganho na velocidade do carro não compensa o tempo gasto andando até lá.

### 6.4 Imagens geradas

Em [imagens/](imagens/):

1. [01_rede_estudo.png](imagens/01_rede_estudo.png), mapa da rede de estudo com A e B marcados.
2. [02_rotas_comparadas.png](imagens/02_rotas_comparadas.png), três rotas no mesmo mapa: menor distância, menor tempo sem trânsito, menor tempo com trânsito.
3. [03_candidatos_P.png](imagens/03_candidatos_P.png), candidatos P dentro do raio X = 500 m.
4. [04_tempo_vs_X.png](imagens/04_tempo_vs_X.png), tempo total da rota em função de X.
5. [05_nodes_expanded.png](imagens/05_nodes_expanded.png), comparação de nós expandidos por algoritmo.
6. [06_runtime_algoritmos.png](imagens/06_runtime_algoritmos.png), tempo de execução de cada algoritmo.

E em [results/](results/):

- [grafo.graphml](results/grafo.graphml), grafo final com pesos.
- [rota_interativa.html](results/rota_interativa.html), mapa folium com A, B e as rotas escolhidas em diferentes X.
- [index.html](results/index.html), dashboard consolidado.
- [comparacao_algoritmos.csv](results/comparacao_algoritmos.csv), tabela dos 4 algoritmos.
- [comparacao_X.csv](results/comparacao_X.csv), tabela do sweep em X com e sem trânsito.
- [metricas.json](results/metricas.json), agregado das métricas.

---

## 7. Discussão

### 7.1 Como o problema foi modelado como grafo?

Cada nó representa uma interseção ou ponto de captura do OpenStreetMap. Cada aresta representa um trecho de via. Os pesos (length, travel_time, travel_time_synth) transformam o problema de "qual rota escolher" em "qual caminho mínimo no grafo ponderado".

### 7.2 O que representam os nós e as arestas?

Os nós são pontos da malha viária (interseções, mudanças de via, fins de rua). As arestas são os trechos de via entre dois nós consecutivos, com atributos como `length` (metros), `highway` (tipo da via, ex.: primary, residential), `maxspeed` (km/h, quando disponível) e nossos pesos derivados (`travel_time`, `travel_time_synth`).

### 7.3 Quais pesos foram usados?

Três pesos por aresta de `G_drive`:
- `length` em metros, para minimizar distância.
- `travel_time` em segundos sem trânsito.
- `travel_time_synth` em segundos com trânsito sintético (correlacionado com tipo de via).

Em `G_walk`, usamos só `length` em metros, porque o tempo a pé é simplesmente `length / 5 km/h`.

### 7.4 Como o trânsito sintético alterou as rotas?

O tempo total subiu cerca de 70%, de 714 segundos para 1.212 segundos. O caminho ótimo escolhido permaneceu o mesmo neste cenário UFRN para Marinha, porque a melhor alternativa continua sendo a BR-101 / Av. Senador Salgado Filho mesmo com trânsito (todas as alternativas razoáveis também receberam fator alto, já que são vias principais). Em outro cenário, com vias secundárias mais competitivas, esperamos que o trânsito sintético desloque a rota para vias menores.

### 7.5 Caminhar alguns metros melhorou a solução?

Não, em nenhum dos valores testados (200, 500, 800, 1000 m). O melhor X foi sempre 0 (não caminhar). A razão é a localização específica de A.

### 7.6 Em quais casos caminhar atrapalhou?

Em todos. Para esse cenário, qualquer caminhada acrescenta tempo sem reduzir o tempo de carro. O nó de A em `G_drive` já está sobre a via mais rápida da região (BR-101 / Av. Senador Salgado Filho). Caminhar para um candidato P leva o usuário para uma via mais lenta antes de embarcar, e o tempo a pé não é compensado.

### 7.7 A menor distância foi também a rota mais rápida?

Quase. A rota de menor distância (peso `length`) e a rota de menor tempo sem trânsito (peso `travel_time`) costumam coincidir na maior parte do trajeto, mas podem divergir em pequenos desvios (rotas mais curtas em ruas internas vs. rotas levemente mais longas em avenidas rápidas). Já a rota de menor tempo com trânsito (peso `travel_time_synth`) pode escolher caminhos diferentes para fugir de avenidas congestionadas, embora neste cenário UFRN para Marinha o ganho de fugir tenha sido pequeno.

### 7.8 O A* expandiu menos nós que o Dijkstra?

Sim. Dijkstra simples e Dijkstra com heap expandiram cerca de 11.886 nós cada. A* expandiu 4.799 nós, aproximadamente 40% do Dijkstra. O ganho vem da heurística de Haversine convertida em segundos, que antecipa quais nós provavelmente ficam fora do caminho ótimo.

### 7.9 O Dijkstra com Heap foi mais eficiente que o Dijkstra simples?

Sim, e por muito. Dijkstra simples levou 14,3 segundos para um par. Dijkstra com heap levou 37 ms. A diferença é aproximadamente 380×, o que confirma o ganho esperado entre O(V²) e O(E log V) para um grafo com 21 mil nós e 56 mil arestas.

### 7.10 O algoritmo da literatura trouxe algum ganho?

Sim. O Dijkstra Bidirecional expandiu 5.079 nós (43% do Dijkstra com heap) e rodou em 17 ms, ficando como o algoritmo mais rápido em tempo de execução, à frente até do Heap puro. O ganho vem de cortar o problema ao meio: cada lado expande aproximadamente metade do grafo.

### 7.11 Quais limitações existem na modelagem proposta?

- O trânsito sintético é uma simplificação. Trânsito real depende de hora, dia da semana, eventos, semáforos. Aqui usamos apenas um fator por tipo de via, fixo após sortear.
- A escolha do P assume que o usuário caminha em linha reta na malha de pedestres e embarca instantaneamente. Não modela tempo de espera, disponibilidade de carro/uber, ou número de baldeações.
- A projeção de P de `G_walk` para `G_drive` usa `nearest_nodes`, que pode mapear vários candidatos diferentes em poucos nós únicos de `G_drive`, limitando a diversidade de P avaliados.
- A heurística do A* assume admissibilidade (`vmax` é a velocidade máxima do grafo), o que pode deixar a busca conservadora demais. Heurísticas mais agressivas poderiam expandir ainda menos nós às custas de perder garantia de otimalidade.

### 7.12 Como o modelo poderia ser aproximado de um aplicativo real de mobilidade?

- Usar dados reais de trânsito (Google Traffic API, Waze, sensores municipais) em vez de fatores sintéticos.
- Considerar custo financeiro (tarifa do app) e disponibilidade de carros próximos.
- Modelar trade-offs personalizados (usuários com pressa vs. com tempo).
- Atualizar o grafo dinamicamente conforme eventos (obras, acidentes).
- Pré-computar contraction hierarchies ou ALT para queries em milissegundos em redes nacionais.

---

## 8. Conclusões

O projeto mostra que, mesmo com uma modelagem relativamente simples (OSMnx + NetworkX + algoritmos próprios), é possível resolver um problema de planejamento de rota multimodal com qualidade. Os quatro algoritmos confirmam a teoria: Dijkstra simples funciona mas é lento, heap acelera muito, A* economiza nós graças à heurística geográfica, e Dijkstra Bidirecional bate todos os outros em runtime ao cortar o grafo pela metade.

O resultado mais interessante foi descobrir que, para o cenário UFRN para Marinha, caminhar não compensa. Isso não é uma falha do RideSmart, é uma resposta do modelo. A origem escolhida já está na via mais rápida da região, e desviar para uma via secundária só piora. O modelo provavelmente identificaria ganhos reais com caminhadas para origens em ruas residenciais internas, onde a malha de caminhada acessa avenidas próximas que o nó de carro original não alcança diretamente.

---

## 9. Como reproduzir

```powershell
cd T3
pip install -r requirements.txt

python -m nbconvert --to notebook --execute notebooks/analise_ridesmart.ipynb --output analise_ridesmart.ipynb
```

Saídas geradas em `data/` (cache do OSMnx), `imagens/` e `results/`.

## 10. Estrutura do projeto

```
T3/
├── README.md                     (este arquivo)
├── requirements.txt
├── data/
│   └── cache/                    (cache do OSMnx, gitignored)
├── src/
│   ├── graph.py                  (download da rede + pesos)
│   ├── traffic.py                (transito sintetico por tipo de via)
│   ├── algorithms.py             (Dijkstra simples, Heap, A*, Bidirecional)
│   ├── ridesmart.py              (pipeline RideSmart com sweep em X)
│   ├── metrics.py                (medicoes e exportacoes)
│   ├── visualization.py          (matplotlib + folium)
│   └── dashboard.py              (HTML estatico autossuficiente)
├── notebooks/
│   └── analise_ridesmart.ipynb   (pipeline orquestrado)
├── imagens/                       (6 PNGs)
└── results/
    ├── grafo.graphml
    ├── rota_interativa.html       (mapa folium)
    ├── index.html                 (dashboard consolidado)
    ├── comparacao_algoritmos.csv
    ├── comparacao_X.csv
    └── metricas.json
```
