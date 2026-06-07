# Trabalho 1: Rede de Relacionamentos nas Notícias da UFRN

Disciplina: DCA3702, Algoritmos e Estrutura de Dados II (UFRN)
Unidade 01, projeto com NLP, NER, Web Scraping e Teoria dos Grafos.

---

## 1. Integrantes

- Lucas Augusto Spinola Pinto

## 2. Link do vídeo (Loom)

- Parte 1: https://www.loom.com/share/ffb533abf92640238afa3626bb410123
- Parte 2: https://www.loom.com/share/bd1e75133e1c4368b2f5d4e7bfbc9162

---

## 3. Problema abordado

O portal de notícias da UFRN (`https://www.ufrn.br/imprensa/noticias`) publica centenas de matérias por ano sobre pessoas, departamentos, projetos, eventos e parcerias da universidade. Esses textos descrevem como a UFRN se organiza, mas a informação está espalhada em prosa, não em uma tabela ou banco de dados.

**Pergunta de pesquisa:** como pessoas, departamentos, centros, projetos, eventos e organizações se relacionam dentro das notícias publicadas pela UFRN, e quais entidades ocupam posições centrais nessa rede?

## 4. Modelagem proposta

O projeto roda em seis etapas:

```
[scraper] -> [NER spaCy] -> [grafo MultiDiGraph] -> [métricas] -> [visualizações] -> [dashboard]
```

| Etapa | Tecnologia | Saída |
|---|---|---|
| 1. Coleta | `requests` + WP REST API descoberta no JS do portal | `data/raw/noticias.json` |
| 2. NER | `spaCy pt_core_news_lg` + `EntityRuler` com padrões da UFRN | `data/processed/entidades.json` |
| 3. Grafo | `networkx.MultiDiGraph` com co-ocorrência por notícia | `results/grafo.graphml` |
| 4. Métricas | Estruturais + 5 centralidades | `results/metricas.json` + `ranking_top20.csv` |
| 5. Visualização | Matplotlib (5 imagens) + PyVis (interativo) | `imagens/*.png` + `results/grafo_interativo.html` |
| 6. Dashboard | HTML estático autossuficiente | `results/index.html` |

**Modelagem do grafo:** cada entidade nomeada vira um nó (com atributo `tipo` e `frequencia`). Duas entidades que aparecem na mesma notícia geram uma aresta direcionada, e o tipo da relação é inferido pelos tipos dos nós (por exemplo, `PESSOA → DEPARTAMENTO` vira `PERTENCE_A`).

## 5. Atividades realizadas

### 5.1 Coleta de notícias

O portal UFRN é renderizado por JavaScript. Inspecionando o `noticias_service.js`, descobri que existe uma WordPress REST API por trás, em `https://webcache01-producao.info.ufrn.br/admin/portal-ufrn/wp-json/wp/v2/noticias-publicadas/`. Em vez de fazer scraping de HTML, consumo essa API direto e recebo título, data, corpo (no campo `acf.corpo`) e tags em JSON.

Limites usados: `per_page=30`, pausa de 1s entre páginas e `User-Agent` identificável. Coletei 150 notícias recentes (mais ou menos 1 mês).

### 5.2 NER com spaCy + EntityRuler

O modelo `pt_core_news_lg` cobre `PER`, `ORG`, `LOC` e `MISC`. Para entidades específicas da UFRN (siglas como IMD, ECT, DCA, e nomes como `Instituto Metrópole Digital` ou `Centro de Tecnologia`), usei um `EntityRuler` carregado de `src/patterns.json` com 78 padrões manuais. Esses padrões são tipados como `CENTRO`, `DEPARTAMENTO`, `PROJETO`, `EVENTO`, `LABORATORIO`, `SISTEMA` e `ORGANIZACAO`.

Mapeio `PER` para `PESSOA` e `ORG` para `ORGANIZACAO`. `LOC` e `MISC` são descartados porque não respondem à pergunta de pesquisa.

Depois da primeira execução, percebi dois problemas que distorciam o resultado e adicionei duas etapas:

1. **Canonicalização** (`src/canonical.py`): variantes textuais da mesma entidade (`"UFRN"` e `"Universidade Federal do Rio Grande do Norte"`, `"IMD"` e `"Instituto Metrópole Digital"`, `"Agecom"` e `"Assessoria de Comunicação"`) são unificadas em um nome canônico antes de entrar no grafo. Usei um dicionário manual em vez de fuzzy matching porque o domínio é pequeno e bem conhecido.
2. **Filtro de bylines** (`src/bylines.json`): jornalistas da Agecom (Beatriz de Azevedo, Hellen Almeida, etc.) assinam quase todas as matérias e, por isso, co-ocorriam com tudo, inflando o PageRank deles. Eu removo trechos como `Reportagem: X.` e `Texto: Y.` do conteúdo via regex no scraper e ainda tiro esses nomes da lista de entidades depois do NER.

### 5.3 Construção do grafo

Uso `MultiDiGraph` (NetworkX), permitindo múltiplas arestas paralelas com `noticia_id` em cada uma, o que preserva rastreabilidade até a notícia de origem.

Relações tipadas por combinação dos tipos dos nós:

| Tipos | Relação | Direção |
|---|---|---|
| `PESSOA -> DEPARTAMENTO/CENTRO/LABORATORIO` | `PERTENCE_A` | assimétrica |
| `PESSOA -> PROJETO` | `DESENVOLVE` | assimétrica |
| `PESSOA -> EVENTO` | `PARTICIPA_DE` | assimétrica |
| `DEPARTAMENTO -> CENTRO` | `PERTENCE_A` | assimétrica |
| `ORGANIZACAO -> EVENTO` | `ORGANIZA` | assimétrica |
| `ORGANIZACAO <-> ORGANIZACAO` | `COLABORA_COM` | simétrica |
| outros pares | `RELACIONADO_A` | simétrica |

Para co-ocorrência, uso `itertools.combinations` em vez de `permutations`: para cada par único de entidades em uma notícia gero uma aresta. Para relações assimétricas, a aresta vai na direção semântica adequada. Isso reduziu o grafo de cerca de 31 mil arestas para 9,6 mil, sem perder informação.

### 5.4 Métricas e centralidades

Calculadas sobre a versão simples não direcionada do grafo, que é o formato exigido por diâmetro, clustering e eigenvector. Métricas obrigatórias mais cinco centralidades clássicas:

- Estruturais: densidade, componentes, grau médio, diâmetro, comprimento médio dos caminhos, coeficiente de agrupamento médio, transitividade.
- Centralidades: Degree, Betweenness, Closeness, Eigenvector e PageRank.

### 5.5 Visualizações

- Estáticas (Matplotlib): histograma de grau, top entidades por PageRank, distribuição de tipos, tamanho de componentes e grafo estático com os top 60 por PageRank.
- Interativa (PyVis): grafo HTML autossuficiente, cor por tipo, tamanho por PageRank, tooltip com métricas, top 150 por PageRank.

### 5.6 Dashboard HTML

Página única em `results/index.html` com CSS embutido e imagens em `data:image/png;base64,...`. Abre offline em qualquer navegador. Contém resumo, métricas, todas as visualizações, tabela top 20 e um iframe com o grafo interativo.

---

## 6. Principais resultados

### 6.1 Métricas estruturais

| Métrica | Valor |
|---|---:|
| Número de nós | 1.067 |
| Número de arestas (grafo simples) | 8.891 |
| Número de arestas (MultiDiGraph) | 9.610 |
| Densidade | 0,0156 |
| Componentes conectados | 1 (rede totalmente conectada) |
| Grau médio | 16,67 |
| Diâmetro (maior componente) | 4 |
| Comprimento médio dos caminhos | 2,01 |
| Coef. de agrupamento médio | 0,94 |
| Transitividade | 0,173 |

> A rede é altamente conectada (diâmetro 4 significa que qualquer entidade alcança qualquer outra em no máximo quatro passos) e tem clustering local muito alto (0,94). As comunidades são bem densas por dentro, mas a transitividade global modesta (0,173) mostra que esses grupos se ligam entre si por poucas pontes.

### 6.2 Top 5 entidades por PageRank

| # | Entidade | Tipo | PageRank |
|---|---|---|---:|
| 1 | UFRN | ORGANIZACAO | 0,0684 |
| 2 | Agecom | ORGANIZACAO | 0,0217 |
| 3 | José Daniel Diniz Melo *(reitor)* | PESSOA | 0,0067 |
| 4 | Instituto Metrópole Digital | CENTRO | 0,0053 |
| 5 | MEC | ORGANIZACAO | 0,0052 |

> O algoritmo identifica corretamente a UFRN como hub absoluto (PageRank 3 vezes maior que o 2º lugar). Em seguida vêm a Agecom (assessoria de comunicação, que é a origem das notícias), o reitor José Daniel Diniz Melo, o Instituto Metrópole Digital e o MEC. Sem nenhuma informação prévia sobre hierarquia institucional, a rede produzida pelo NER reproduz a hierarquia real: universidade, depois órgão de comunicação, depois reitor, depois centros, depois órgãos parceiros.

### 6.3 Validação small-world (Real vs Erdős-Rényi vs Watts-Strogatz)

Para conferir se a rede é mesmo small-world (e não apenas pequena), comparei com modelos aleatórios de mesma escala:

| Modelo | n | Clustering | Caminho médio |
|---|---:|---:|---:|
| Real | 1.067 | 0,942 | 2,01 |
| Erdős-Rényi (mesma densidade) | 1.067 | 0,015 | 2,77 |
| Watts-Strogatz (k≈grau médio, p=0,1) | 1.067 | 0,512 | 3,38 |

> A rede real tem clustering 63 vezes maior que o Erdős-Rényi equivalente, com caminho médio até 27% menor. Mesmo comparada com o Watts-Strogatz canônico, ela é mais "small-world": clustering 84% maior e caminho médio 41% menor. Conclui-se que há estrutura genuína, e não simplesmente um grafo aleatório.

### 6.4 Distribuição por tipo de relação

| Tipo de relação | Quantidade |
|---|---:|
| RELACIONADO_A (default entre tipos não-modelados) | 6.036 |
| COLABORA_COM (ORGANIZACAO ↔ ORGANIZACAO) | 3.313 |
| PERTENCE_A (PESSOA → DEPARTAMENTO/CENTRO, DEPARTAMENTO → CENTRO) | 261 |

> A predominância de `RELACIONADO_A` é esperada pela granularidade das notícias: a maioria das co-ocorrências envolve pelo menos uma entidade do tipo PESSOA, e nem todo par PESSOA + X tem uma relação semântica clara o suficiente para virar `PERTENCE_A` ou `PARTICIPA_DE`. Os 261 `PERTENCE_A` capturam os vínculos institucionais explícitos, que é o sinal mais limpo do grafo.

### 6.5 Imagens principais

- [imagens/01_hist_grau.png](imagens/01_hist_grau.png), distribuição de grau (cauda longa típica de redes complexas).
- [imagens/02_top_pagerank.png](imagens/02_top_pagerank.png), top entidades por PageRank.
- [imagens/03_distribuicao_tipos.png](imagens/03_distribuicao_tipos.png), composição por tipo (PESSOA, ORGANIZACAO, etc.).
- [imagens/04_componentes.png](imagens/04_componentes.png), tamanho das componentes (uma única gigante).
- [imagens/05_grafo_estatico.png](imagens/05_grafo_estatico.png), subgrafo dos top 60 por PageRank.
- [imagens/06_real_vs_aleatorio.png](imagens/06_real_vs_aleatorio.png), comparação com Erdős-Rényi e Watts-Strogatz.
- [results/grafo_interativo.html](results/grafo_interativo.html), visualização interativa (PyVis).
- [results/index.html](results/index.html), dashboard consolidado.
- [results/grafo.gexf](results/grafo.gexf), formato nativo do Gephi.
- [results/grafo.graphml](results/grafo.graphml), formato padrão.

---

## 7. Análise e discussão dos achados

### 7.1 A rede reproduz a estrutura da UFRN

O top 5 por PageRank reproduz bem a estrutura real da universidade:

1. UFRN (PageRank 0,068) é o hub absoluto. Aparece em quase todas as notícias, então fica central por natureza.
2. Agecom (0,022) é a origem das notícias. Faz sentido estrutural: ela é o canal que conecta tudo.
3. José Daniel Diniz Melo (0,007) é o reitor da UFRN. O algoritmo identifica corretamente a autoridade máxima da instituição só pela frequência com que ele aparece junto a outros entes institucionais.
4. Instituto Metrópole Digital (0,005) é um dos centros mais ativos em comunicação no portal, o que combina com a natureza tecnológica das atividades publicadas.
5. MEC (0,005) é o único órgão federal acima da UFRN. A centralidade dele reflete decisões que afetam toda a universidade.

A comparação com Erdős-Rényi e Watts-Strogatz mostra que a estrutura observada não pode ser explicada por aleatoriedade: o clustering real é 63 vezes maior que ER com a mesma densidade, e o caminho médio é até menor que o Watts-Strogatz canônico. Isso é típico de redes geradas por processos não-aleatórios (comunidades temáticas e hubs hierárquicos). Em outras palavras, a UFRN não é uma rede de menções aleatórias, ela é organizada em torno de poucos eixos institucionais que comprimem todos os caminhos. Diâmetro 4 significa que qualquer entidade alcança qualquer outra em até quatro passos.

### 7.2 As correções metodológicas mudaram a leitura

Na primeira execução, o top de PageRank era dominado por três jornalistas da Agecom (Beatriz, Hellen e Rebeca) e ainda existia a duplicação UFRN versus Universidade Federal do Rio Grande do Norte. Esses dois problemas distorciam a interpretação: o grafo media "quem assinou junto" em vez de "quem trabalha junto". A solução foi adicionar a canonicalização manual de aliases (`src/canonical.py`) e o filtro de bylines (`src/bylines.json`). O top mudou e a leitura passou a refletir a estrutura institucional real.

A lição metodológica é que, em análise de rede a partir de texto, a definição do que conta como uma entidade determina o resultado. NER bruto sem pós-processamento gera grafos visualmente bonitos mas semanticamente quebrados.

Outro ponto importante é o `EntityRuler`: siglas como `DCA`, `IMD`, `ECT`, `PROEX` não estão no `pt_core_news_lg`, então ele as ignora ou classifica como `MISC`. O `EntityRuler` com 78 padrões manuais carrega esse conhecimento de domínio sem precisar treinar nada. Vale o investimento: sem ele, o grafo perde o vocabulário próprio da UFRN.

### 7.3 Limitações

- Amostra de 150 notícias, recorte de mais ou menos 1 mês. Para análises longitudinais, seria necessário scraping incremental com cache.
- Canonicalização manual cobre cerca de 50 aliases conhecidos. Variantes não previstas (por exemplo "Daniel Diniz" e "José Daniel Diniz Melo") ainda aparecem como nós distintos. Trabalho futuro: fuzzy matching com `dedupe` ou `record-linkage`.
- Co-ocorrência em texto não equivale a relação causal. Uma matéria que cita Pessoa X e Departamento Y porque X comentou sobre Y gera aresta `PERTENCE_A` mesmo que X não trabalhe lá. As 261 arestas `PERTENCE_A` são o sinal mais limpo, mas as 6.036 `RELACIONADO_A` carregam ruído.
- O NER do spaCy comete erros em nomes brasileiros pouco frequentes, e o `EntityRuler` cobre apenas as entidades-chave que listei à mão.

## 8. Conclusões

Com scraping, NER e grafos foi possível reconstruir parte da estrutura da UFRN só a partir das notícias. As centralidades apontam UFRN, Agecom, reitor, centros e órgãos federais como nós principais, sem que o algoritmo tenha qualquer informação prévia sobre a hierarquia da universidade. A comparação com Erdős-Rényi e Watts-Strogatz mostrou que a rede é small-world de verdade, não acaso estatístico.

A combinação de spaCy + EntityRuler + canonicalização + filtro de bylines deixa claro que NER bruto não basta: as etapas de pós-processamento decidem se o grafo conta uma história sobre a instituição ou sobre o método jornalístico. Próximos passos naturais para evoluir o trabalho: (1) canonicalização fuzzy para resolver variantes de nomes não previstas, (2) enriquecimento com análise sintática para refinar tipos de relação (separar `PERTENCE_A` de `RELACIONADO_A` com mais precisão), e (3) coleta longitudinal para análise temporal e detecção de comunidades emergentes.

---

## 9. Como reproduzir

```powershell
# 1. Instalar dependências
pip install -r requirements.txt
python -m spacy download pt_core_news_lg

# 2. Executar o notebook
python -m nbconvert --to notebook --execute notebooks/analise_ufrn.ipynb --output analise_ufrn.ipynb
```

Saídas geradas em `data/`, `imagens/` e `results/`.

## 10. Estrutura do projeto

```
T1/
├── README.md                     (este arquivo)
├── requirements.txt
├── data/
│   ├── raw/noticias.json         (scraping bruto)
│   └── processed/entidades.json  (NER aplicado)
├── src/
│   ├── scraper.py                (coleta WP REST API + filtro de bylines)
│   ├── ner.py + patterns.json    (spaCy + EntityRuler)
│   ├── canonical.py              (canonicalização de aliases UFRN, IMD, ...)
│   ├── bylines.json              (lista de jornalistas a filtrar)
│   ├── graph.py                  (MultiDiGraph com relações tipadas)
│   ├── analysis.py               (métricas + 5 centralidades + ER/WS)
│   ├── visualization.py          (matplotlib + PyVis)
│   └── dashboard.py              (HTML estático index.html)
├── notebooks/
│   └── analise_ufrn.ipynb        (pipeline orquestrado)
├── imagens/                       (6 PNGs)
└── results/
    ├── grafo.graphml
    ├── grafo.gexf                 (formato nativo do Gephi)
    ├── grafo_interativo.html
    ├── index.html                 (entregável principal)
    ├── metricas.json
    └── ranking_top20.csv
```
