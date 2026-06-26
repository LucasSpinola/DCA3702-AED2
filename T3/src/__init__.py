"""
Trabalho 3 - DCA3702 (UFRN)
Projeto Final RideSmart: modelagem e análise de rotas urbanas com grafos.

Cenário: Setor de Aulas IV (UFRN, Lagoa Nova) -> Comando do 3o Distrito Naval
(Santos Reis, Natal/RN). O usuário aceita caminhar até X metros antes de
embarcar no carro/Uber. O sistema escolhe o melhor ponto de embarque P.

Módulos:
    graph         - download da rede via OSMnx + três pesos por aresta
    traffic       - trânsito sintético correlacionado com tipo de via
    algorithms    - Dijkstra simples, Dijkstra com heap, A*, Bidirecional
    ridesmart     - pipeline RideSmart com sweep em X
    metrics       - medições e exportações
    visualization - imagens estáticas e mapa folium interativo
    dashboard     - relatório HTML autossuficiente
"""

__version__ = "1.0.0"
