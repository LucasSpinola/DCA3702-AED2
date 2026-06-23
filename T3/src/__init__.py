"""
Trabalho 3 - DCA3702 (UFRN)
Projeto Final RideSmart: modelagem e analise de rotas urbanas com grafos.

Cenario: Setor de Aulas IV (UFRN, Lagoa Nova) -> Comando do 3o Distrito Naval
(Santos Reis, Natal/RN). O usuario aceita caminhar ate X metros antes de
embarcar no carro/Uber. O sistema escolhe o melhor ponto de embarque P.

Modulos:
    graph         - download da rede via OSMnx + tres pesos por aresta
    traffic       - transito sintetico correlacionado com tipo de via
    algorithms    - Dijkstra simples, Dijkstra com heap, A*, Bidirecional
    ridesmart     - pipeline RideSmart com sweep em X
    metrics       - medicoes e exportacoes
    visualization - imagens estaticas e mapa folium interativo
    dashboard     - relatorio HTML autossuficiente
"""

__version__ = "1.0.0"
