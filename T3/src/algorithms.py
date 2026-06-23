"""
Implementacoes proprias de algoritmos de caminho minimo.

Quatro funcoes com a mesma assinatura:
    func(G, source, target, weight='travel_time')
    -> dict com chaves {path, cost, nodes_expanded, elapsed_ms, alg}

Implementadas:
    1. dijkstra_simples (busca linear, O(V^2))
    2. dijkstra_heap    (heapq, O(E log V))
    3. a_star           (heuristica geografica admissivel)
    4. dijkstra_bidirecional (busca simultanea de origem e destino)
"""
from __future__ import annotations

import heapq
import math
import time
from typing import Any

import networkx as nx


INF = float("inf")


def _multi_min_weight(G: nx.MultiDiGraph, u: Any, v: Any, weight: str) -> float:
    """Em MultiDiGraph existe key adicional. Pega o menor peso entre paralelas."""
    edges_data = G.get_edge_data(u, v)
    if not edges_data:
        return INF
    return min(float(d.get(weight, INF)) for d in edges_data.values())


def _reconstruir_caminho(predecessor: dict, target: Any) -> list:
    """Refaz o caminho a partir do dicionario de predecessores."""
    caminho = []
    no = target
    while no is not None:
        caminho.append(no)
        no = predecessor.get(no)
    caminho.reverse()
    return caminho


# ------------------------------------------------------------
# 1. Dijkstra simples (busca linear)
# ------------------------------------------------------------
def dijkstra_simples(
    G: nx.MultiDiGraph,
    source: Any,
    target: Any,
    weight: str = "travel_time",
) -> dict[str, Any]:
    """
    Dijkstra com busca linear (sem heap). Mantido para comparacao.
    Complexidade O(V^2). Funciona, mas e o mais lento dos quatro.
    """
    t0 = time.perf_counter()
    dist: dict[Any, float] = {n: INF for n in G.nodes()}
    pred: dict[Any, Any] = {n: None for n in G.nodes()}
    visitado: set = set()
    dist[source] = 0.0
    nodes_expanded = 0

    while True:
        # Acha o no nao visitado com menor distancia
        no_atual = None
        menor = INF
        for n in G.nodes():
            if n not in visitado and dist[n] < menor:
                menor = dist[n]
                no_atual = n
        if no_atual is None or no_atual == target or menor == INF:
            break
        visitado.add(no_atual)
        nodes_expanded += 1
        # Relaxa os vizinhos
        for viz in G.successors(no_atual):
            if viz in visitado:
                continue
            w = _multi_min_weight(G, no_atual, viz, weight)
            nova = dist[no_atual] + w
            if nova < dist[viz]:
                dist[viz] = nova
                pred[viz] = no_atual

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    custo = dist.get(target, INF)
    caminho = _reconstruir_caminho(pred, target) if custo < INF else []
    return {
        "path": caminho, "cost": custo,
        "nodes_expanded": nodes_expanded,
        "elapsed_ms": elapsed_ms, "alg": "dijkstra_simples",
    }


# ------------------------------------------------------------
# 2. Dijkstra com heap
# ------------------------------------------------------------
def dijkstra_heap(
    G: nx.MultiDiGraph,
    source: Any,
    target: Any,
    weight: str = "travel_time",
) -> dict[str, Any]:
    """Dijkstra com heapq. Complexidade O(E log V)."""
    t0 = time.perf_counter()
    dist = {source: 0.0}
    pred: dict[Any, Any] = {source: None}
    visitado: set = set()
    fila: list = [(0.0, source)]
    nodes_expanded = 0

    while fila:
        d_u, u = heapq.heappop(fila)
        if u in visitado:
            continue
        visitado.add(u)
        nodes_expanded += 1
        if u == target:
            break
        for v in G.successors(u):
            if v in visitado:
                continue
            w = _multi_min_weight(G, u, v, weight)
            nova = d_u + w
            if nova < dist.get(v, INF):
                dist[v] = nova
                pred[v] = u
                heapq.heappush(fila, (nova, v))

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    custo = dist.get(target, INF)
    caminho = _reconstruir_caminho(pred, target) if custo < INF else []
    return {
        "path": caminho, "cost": custo,
        "nodes_expanded": nodes_expanded,
        "elapsed_ms": elapsed_ms, "alg": "dijkstra_heap",
    }


# ------------------------------------------------------------
# 3. A* com heuristica geografica (Haversine)
# ------------------------------------------------------------
def _haversine_segundos(
    coord_u: tuple[float, float],
    coord_v: tuple[float, float],
    vmax_kph: float,
) -> float:
    """
    Distancia Haversine em metros, convertida em segundos pela velocidade
    maxima do grafo. Heuristica admissivel para tempo de viagem.
    """
    R = 6371000.0
    lat1, lon1 = math.radians(coord_u[0]), math.radians(coord_u[1])
    lat2, lon2 = math.radians(coord_v[0]), math.radians(coord_v[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    d_m = 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    vmax_mps = vmax_kph / 3.6
    return d_m / max(vmax_mps, 0.1)


def a_star(
    G: nx.MultiDiGraph,
    source: Any,
    target: Any,
    weight: str = "travel_time",
) -> dict[str, Any]:
    """
    A* com heuristica de Haversine convertida para segundos pela vmax do grafo.
    Heuristica admissivel (nao superestima) garante otimalidade.
    """
    t0 = time.perf_counter()
    # vmax = maior speed_kph no grafo (limite superior para tempo de viagem)
    vmax_kph = max(
        (float(d.get("speed_kph", 30.0)) for _, _, d in G.edges(data=True)),
        default=80.0,
    )
    # Coordenadas do destino
    coord_target = (float(G.nodes[target]["y"]), float(G.nodes[target]["x"]))

    g_score = {source: 0.0}
    pred: dict[Any, Any] = {source: None}
    visitado: set = set()
    # heap por (f = g + h)
    coord_source = (float(G.nodes[source]["y"]), float(G.nodes[source]["x"]))
    h_source = _haversine_segundos(coord_source, coord_target, vmax_kph)
    fila: list = [(h_source, 0.0, source)]
    nodes_expanded = 0

    while fila:
        f_u, g_u, u = heapq.heappop(fila)
        if u in visitado:
            continue
        visitado.add(u)
        nodes_expanded += 1
        if u == target:
            break
        for v in G.successors(u):
            if v in visitado:
                continue
            w = _multi_min_weight(G, u, v, weight)
            tentativo = g_u + w
            if tentativo < g_score.get(v, INF):
                g_score[v] = tentativo
                pred[v] = u
                coord_v = (float(G.nodes[v]["y"]), float(G.nodes[v]["x"]))
                h_v = _haversine_segundos(coord_v, coord_target, vmax_kph)
                heapq.heappush(fila, (tentativo + h_v, tentativo, v))

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    custo = g_score.get(target, INF)
    caminho = _reconstruir_caminho(pred, target) if custo < INF else []
    return {
        "path": caminho, "cost": custo,
        "nodes_expanded": nodes_expanded,
        "elapsed_ms": elapsed_ms, "alg": "a_star",
    }


# ------------------------------------------------------------
# 4. Dijkstra Bidirecional (algoritmo adicional)
# ------------------------------------------------------------
def dijkstra_bidirecional(
    G: nx.MultiDiGraph,
    source: Any,
    target: Any,
    weight: str = "travel_time",
) -> dict[str, Any]:
    """
    Dijkstra bidirecional: avanca uma busca a partir de `source` e outra
    no grafo reverso a partir de `target`. Para quando o melhor candidato
    nao pode mais ser melhorado pela soma das duas distancias.

    Em redes viarias grandes, costuma expandir cerca de metade dos nos
    que o Dijkstra unidirecional.
    """
    t0 = time.perf_counter()
    if source == target:
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return {"path": [source], "cost": 0.0, "nodes_expanded": 1,
                "elapsed_ms": elapsed_ms, "alg": "dijkstra_bidirecional"}

    G_rev = G.reverse(copy=False)

    dist_f = {source: 0.0}
    pred_f: dict[Any, Any] = {source: None}
    visit_f: set = set()
    fila_f: list = [(0.0, source)]

    dist_b = {target: 0.0}
    pred_b: dict[Any, Any] = {target: None}
    visit_b: set = set()
    fila_b: list = [(0.0, target)]

    melhor = INF
    no_meio = None
    nodes_expanded = 0

    def _avanca(fila, dist, pred, visit, outro_dist, sentido):
        nonlocal melhor, no_meio, nodes_expanded
        if not fila:
            return None
        d_u, u = heapq.heappop(fila)
        if u in visit:
            return d_u
        visit.add(u)
        nodes_expanded += 1
        # Verifica fechamento
        if u in outro_dist:
            total = d_u + outro_dist[u]
            if total < melhor:
                melhor = total
                no_meio = u
        # Relaxa
        grafo = G if sentido == "forward" else G_rev
        for v in grafo.successors(u):
            if v in visit:
                continue
            w = _multi_min_weight(grafo, u, v, weight)
            nova = d_u + w
            if nova < dist.get(v, INF):
                dist[v] = nova
                pred[v] = u
                heapq.heappush(fila, (nova, v))
        return d_u

    while fila_f or fila_b:
        # Criterio de parada: top das duas filas somados >= melhor encontrado
        top_f = fila_f[0][0] if fila_f else INF
        top_b = fila_b[0][0] if fila_b else INF
        if top_f + top_b >= melhor:
            break
        if top_f <= top_b:
            _avanca(fila_f, dist_f, pred_f, visit_f, dist_b, "forward")
        else:
            _avanca(fila_b, dist_b, pred_b, visit_b, dist_f, "backward")

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    if no_meio is None:
        return {"path": [], "cost": INF,
                "nodes_expanded": nodes_expanded,
                "elapsed_ms": elapsed_ms, "alg": "dijkstra_bidirecional"}

    # Caminho: source -> ... -> no_meio (forward) + no_meio -> ... -> target (backward)
    cam_f = _reconstruir_caminho(pred_f, no_meio)
    cam_b = _reconstruir_caminho(pred_b, no_meio)
    # cam_b sai de target chegando em no_meio; precisa inverter (excluindo no_meio que ja esta em cam_f)
    cam_b_invertido = list(reversed(cam_b[:-1])) if len(cam_b) > 1 else []
    caminho = cam_f + cam_b_invertido
    return {
        "path": caminho, "cost": melhor,
        "nodes_expanded": nodes_expanded,
        "elapsed_ms": elapsed_ms, "alg": "dijkstra_bidirecional",
    }


ALGORITMOS = {
    "dijkstra_simples": dijkstra_simples,
    "dijkstra_heap": dijkstra_heap,
    "a_star": a_star,
    "dijkstra_bidirecional": dijkstra_bidirecional,
}
