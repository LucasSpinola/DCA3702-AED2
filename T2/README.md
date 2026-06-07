# Trabalho 2: Análise Estrutural da Rede Viária de Ponta Negra (Natal/RN)

Disciplina: DCA3702, Algoritmos e Estrutura de Dados II (UFRN)
Semanas 5 e 6, Hubs e Core Decomposition.

---

## 1. Identificação

- **Região analisada:** Ponta Negra, Natal/RN. Círculo de raio 2 km em torno do ponto `(-5.8730, -35.1750)` (Praia de Ponta Negra).
- **Tipo de rede:** `drive` (vias trafegáveis por automóveis).
- **Fonte dos dados:** OpenStreetMap, via OSMnx.
- **Vídeo de apresentação (Loom):**
  - Parte 1: https://www.loom.com/share/403f7461257f48a7b2dd737cb40db5d2
  - Parte 2: https://www.loom.com/share/375d26553d7c40fb81517853157a05d5
  - Parte 3: https://www.loom.com/share/1b67ec668ab74e609d0650b9fde55f8a

### Por que Ponta Negra?

Ponta Negra é um bairro icônico de Natal, com uma malha viária heterogênea. A Avenida Engenheiro Roberto Freire concentra grande fluxo, as ruas paralelas à orla formam uma malha quase regular e a parte alta do bairro (próxima à UFRN e a Capim Macio) tem ruas mais irregulares. Esse contraste é o que torna interessante comparar `grau`, `betweenness centrality` e `k-core`, que são métricas que respondem a perguntas diferentes sobre a mesma rede.

A escolha por ponto + raio (em vez de `graph_from_place`) garante uma área bem definida e reproduzível: o polígono administrativo retornado pelo Nominatim para "Ponta Negra" estava incompleto e não retornava nós.

---

## 2. Objetivo

Modelar a malha viária de Ponta Negra como um grafo e identificar:

- Hubs (nós de alto grau).
- Pontos críticos de fluxo (alto `betweenness centrality`).
- Regiões estruturalmente densas via `k-core decomposition`.
- Diferenças entre as visões geográfica e topológica da rede.

---

## 3. Metodologia

| Etapa | Ferramenta | O que faz |
| --- | --- | --- |
| 1. Download da rede | `osmnx.graph_from_point` | Baixa o `MultiDiGraph` direcionado da malha viária |
| 2. Pré-processamento | `osmnx.convert.to_undirected` + `nx.Graph` | Converte para grafo simples não direcionado |
| 3. Métricas | `networkx` | grau, betweenness, closeness, core number |
| 4. Visualização | `matplotlib` + `osmnx.plot_graph` | Distribuições, mapas e subgrafos |
| 5. Exportação | `nx.write_graphml` | Gera `.graphml` com atributos para o Gephi |
| 6. Visualização avançada | Gephi + plugin Geo Layout | Visualização geográfica no mapa real |

### Decisões metodológicas

- **Simplificação para grafo não direcionado:** a direção das vias não importa para a topologia do bairro, e arestas paralelas (sentido duplo) inflavam o grau dos nós. Por isso todas as métricas são calculadas sobre o grafo simples não direcionado `G_simple`.
- **`betweenness centrality` exata:** o grafo tem cerca de 800 nós, então o cálculo exato é viável (uns poucos segundos). Em redes maiores eu usaria a versão aproximada com amostragem (parâmetro `k` do `nx.betweenness_centrality`).
- **`x`, `y` preservados nos nós:** mantenho `x` (longitude) e `y` (latitude) como atributos e duplico como `longitude` e `latitude` para garantir compatibilidade com o plugin Geo Layout do Gephi.

---

## 4. Métricas calculadas

| Métrica | Valor |
| --- | --- |
| Número de nós | 805 |
| Número de arestas (simples) | 1.178 |
| Componentes conexas | 1 |
| Densidade | 0,003640 |
| Grau médio | 2,93 |
| Grau mínimo / máximo | 1 / 4 |
| `k_max` (maior core number) | 2 |
| Nós no main core | 723 (cerca de 89,8%) |

> O grau máximo igual a 4 é característico de malhas viárias: quase toda interseção tem 3 ou 4 ruas convergindo. Não existem "super-hubs" como em redes sociais. A rede é homogênea em grau, mas a centralidade está concentrada em um conjunto pequeno de eixos.

### Top 5 nós por grau

| Nó (OSM id) | Grau |
| --- | --- |
| 501888552 | 4 |
| 501888818 | 4 |
| 501889047 | 4 |
| 501903002 | 4 |
| 501925921 | 4 |

(Vários nós empatados em grau 4, que são as interseções típicas de 4 vias.)

### Top 5 nós por betweenness

| Nó (OSM id) | Betweenness |
| --- | --- |
| 505026738 | 0,3149 |
| 501888552 | 0,3057 |
| 505026745 | 0,3039 |
| 501888818 | 0,2971 |
| 11402845515 | 0,2735 |

> Esses nós ficam sobre a Av. Engenheiro Roberto Freire e nos cruzamentos imediatos, que é o eixo que estrutura o bairro.

### Top 5 nós por closeness

| Nó (OSM id) | Closeness |
| --- | --- |
| 505026477 | 0,0680 |
| 501733911 | 0,0677 |
| 501889056 | 0,0676 |
| 501733922 | 0,0675 |
| 505026745 | 0,0674 |

---

## 5. Principais visualizações

### 5.1 Visualizações geradas em Python

Todas em [imagens/](imagens/):

1. [01_distribuicao_grau.png](imagens/01_distribuicao_grau.png), histograma e log-log do grau.
2. [02_mapa_grau.png](imagens/02_mapa_grau.png), mapa geográfico colorido por grau.
3. [03_mapa_betweenness.png](imagens/03_mapa_betweenness.png), mapa geográfico colorido por betweenness.
4. [04_mapa_core_number.png](imagens/04_mapa_core_number.png), mapa geográfico colorido por core number.
5. [05_main_core.png](imagens/05_main_core.png), destaque do main core (`k = k_max`).
6. [06_top10_grau.png](imagens/06_top10_grau.png), top 10% dos nós por grau destacados.
7. [07_grau_vs_betweenness.png](imagens/07_grau_vs_betweenness.png), scatter grau × betweenness.

### 5.2 Visualizações geradas no Gephi

- **Geográfica** (Geo Layout): preserva a forma real do bairro. Nós dimensionados por `degree`, coloridos por `core_number`, com destaque por `betweenness`.
- **Filtros:** subgrafo dos top 10% por grau e subgrafo com `core_number ≥ 2`.

---

## 6. Respostas às questões obrigatórias

### 6.1 Os nós com maior grau coincidem com os nós de maior betweenness?

Parcialmente. Há sobreposição: o nó `501888552` é simultaneamente top 1 em grau (4) e top 2 em betweenness (0,306), e o `501888818` também aparece nos dois. Mas os top 1 e top 3 em betweenness (`505026738` e `505026745`) não estão no top 10 por grau. Eles têm grau 3, mas são posições de "gargalo" por onde passam muitas rotas mínimas.

Conclusão: alto grau ajuda, mas não basta para alta centralidade de intermediação. Há cruzamentos de grau 3 mais críticos para a mobilidade do que cruzamentos de grau 4 em ruas periféricas.

### 6.2 O núcleo identificado pelo k-core coincide com os principais hubs?

Não exatamente. O `k_max = 2` é baixo (típico de redes planares como as malhas viárias), e o main core contém 89,8% dos nós. Ou seja, basicamente toda a rede menos os becos sem saída e as ramificações terminais. O k-core sozinho não é discriminativo nessa rede: ele só separa "ruas que fazem parte de algum ciclo" (main core) de "ruas que são apêndices" (folhas).

Conclusão: o k-core mede coesão local (cada nó tem pelo menos `k` vizinhos no subgrafo) e funciona bem em redes densas (sociais, web). Em redes viárias planares ele tende a colapsar quase tudo no mesmo nível. Para esta rede, a betweenness é muito mais discriminativa que o core number para identificar hubs estruturais.

### 6.3 O que a métrica de betweenness revela que o grau não revela?

A betweenness revela pontos de estrangulamento: nós por onde passam muitas rotas mínimas entre quaisquer dois pontos da rede. O grau só diz quantas ruas se conectam num cruzamento; a betweenness diz o quanto a circulação do bairro como um todo depende daquele cruzamento.

Visualmente, no mapa [03_mapa_betweenness.png](imagens/03_mapa_betweenness.png) os nós quentes formam um eixo contínuo ao longo da Av. Roberto Freire e nos cruzamentos que conectam a orla à parte alta. Já no mapa por grau ([02_mapa_grau.png](imagens/02_mapa_grau.png)) os nós quentes aparecem espalhados pelo bairro inteiro, sem distinguir corredor principal de via secundária.

### 6.4 O que muda entre visualização geográfica e estrutural?

Usei o Geo Layout do Gephi para fazer a visualização geográfica. Nela os nós são posicionados pelas coordenadas reais (latitude e longitude), então a rede preserva a forma do bairro: dá pra reconhecer a orla curvada de Ponta Negra, as ruas paralelas e o miolo denso da parte alta. Essa visão é útil porque permite validar resultados olhando para o mapa real (por exemplo: "esse hub vermelho é mesmo o cruzamento X?").

A visualização estrutural seria a alternativa, usando um layout de força como o ForceAtlas 2. Nele as coordenadas reais são abandonadas: nós muito conectados se agrupam e nós periféricos vão para a borda. Em redes viárias planares como esta, o resultado esperado seria um "blob" relativamente uniforme, porque o grafo é quase regular (grau máximo 4). O ganho teórico desse layout seria realçar regiões com mais ciclos curtos, como a malha densa da parte alta, mas a perda da geografia tira boa parte da informação que torna a análise fácil de interpretar. Por isso optei por focar na visualização geográfica, que casa melhor com o tema do trabalho.

### 6.5 Existem regiões críticas para mobilidade urbana?

Sim. A Av. Engenheiro Roberto Freire é o principal corredor que conecta a parte alta de Ponta Negra (e o trânsito vindo do centro de Natal e de Lagoa Nova) à orla. Todos os top 10 nós por betweenness estão sobre essa avenida ou em cruzamentos imediatos. Uma interdição parcial dela (obras, evento, acidente) impactaria todo o bairro de forma desproporcional, porque não há rota alternativa de capacidade equivalente.

### 6.6 A rede parece homogênea ou apresenta concentração estrutural?

- Em grau: homogênea. A distribuição se concentra em 2, 3 e 4, sem cauda longa.
- Em betweenness: muito concentrada. Poucos nós com valores acima de 0,2, e a maioria abaixo de 0,01. Os top 10 sozinhos respondem por uma fração desproporcional do fluxo total.

A rede é, ao mesmo tempo, uniforme em conectividade local e concentrada em fluxo global. Esse padrão é típico de bairros lineares organizados em torno de uma avenida-tronco.

### 6.7 Os resultados fazem sentido para o conhecimento urbano da região?

Sim. Quem conhece Natal sabe que a Av. Roberto Freire é o eixo estruturador de Ponta Negra e que qualquer engarrafamento ali se propaga rápido. O algoritmo identifica exatamente esse eixo como o conjunto de maior betweenness, sem ter qualquer informação prévia sobre hierarquia viária. Isso bate com o que se espera.

---

## 7. Conclusões

1. A malha viária de Ponta Negra é homogênea em grau (média 2,93 e máximo 4) mas concentrada em fluxo: poucos nós sobre a Av. Roberto Freire respondem pela maior parte da betweenness alta.
2. O k-core é pouco discriminativo em redes viárias planares. 89,8% dos nós estão no main core (`k = 2`). Para esse tipo de rede, betweenness e closeness identificam hubs estruturais com mais clareza que o core number.
3. Grau e betweenness não coincidem totalmente. Existem cruzamentos de grau 3 com betweenness muito maior do que cruzamentos de grau 4 em ruas secundárias. O grau mede conectividade local, a betweenness mede importância global de fluxo.
4. A vulnerabilidade da mobilidade do bairro está concentrada em um único eixo. O que o algoritmo identifica corresponde ao conhecimento empírico de quem circula em Ponta Negra.
5. Grafos ajudam a extrair informação útil de sistemas urbanos sem precisar de hipóteses prévias. Só a partir da topologia, o algoritmo redescobre o papel estruturador da Av. Roberto Freire.
