"""
Pipeline RideSmart.

Dado (A, B, X):
    1. Em G_walk, encontra todos os nós `P` a distância <= X metros de A.
    2. Para cada P candidato:
        - tempo a pé (5 km/h) de A até P.
        - tempo de carro de P até B, usando o algoritmo escolhido.
    3. Escolhe o P* que minimiza o tempo total.

Realiza o sweep em X = [0, 200, 500, 800, 1000] m.
"""

from __future__ import annotations

import random
from typing import Any, Callable

import networkx as nx
import osmnx as ox

from .algorithms import dijkstra_heap


# Velocidade de caminhada em km/h
VELOCIDADE_CAMINHADA_KPH = 5.0
MAX_CANDIDATOS = 100


def _no_walk_para_drive(
    G_drive: nx.MultiDiGraph,
    G_walk: nx.MultiDiGraph,
    no_walk: Any,
) -> Any:
    """Para um nó de G_walk, retorna o nó mais próximo em G_drive."""
    lat = float(G_walk.nodes[no_walk]["y"])
    lon = float(G_walk.nodes[no_walk]["x"])
    return ox.distance.nearest_nodes(G_drive, X=lon, Y=lat)


def candidatos_p(
    G_walk: nx.MultiDiGraph,
    no_a_walk: Any,
    x_metros: float,
) -> dict[Any, float]:
    """
    Retorna dict {no_walk: distancia_em_metros} para todos os nós
    alcançáveis em até `x_metros` a partir de `no_a_walk` em G_walk.

    Usa Dijkstra single-source do NetworkX (rápido em C).
    """
    if x_metros <= 0:
        return {no_a_walk: 0.0}
    distancias = nx.single_source_dijkstra_path_length(
        G_walk,
        no_a_walk,
        cutoff=x_metros,
        weight="length",
    )
    return distancias


def obter_candidatos_filtrados(
    G_walk: nx.MultiDiGraph,
    no_a_walk: Any,
    x_metros: float,
    max_candidatos: int = MAX_CANDIDATOS,
) -> dict[Any, float]:
    """
    Retorna dict de candidatos filtrados de acordo com o limite de max_candidatos,
    usando amostragem aleatória se necessário, mas mantendo a origem.
    """
    cand = candidatos_p(G_walk, no_a_walk, x_metros)
    if not cand:
        return {}
    if len(cand) > max_candidatos:
        # Garante a inclusão do ponto de origem A (0.0m de caminhada)
        outros_candidatos = [(n, dist) for n, dist in cand.items() if n != no_a_walk]
        rng = random.Random(42)
        sampled = rng.sample(outros_candidatos, max_candidatos - 1)
        topo = dict(sampled)
        topo[no_a_walk] = 0.0
        return topo
    return cand


def escolher_melhor_p(
    G_drive: nx.MultiDiGraph,
    G_walk: nx.MultiDiGraph,
    no_a_walk: Any,
    no_b_drive: Any,
    x_metros: float,
    weight: str = "travel_time",
    algoritmo: Callable = dijkstra_heap,
    max_candidatos: int = MAX_CANDIDATOS,
) -> dict[str, Any]:
    """
    Encontra o melhor ponto de embarque P para o cenário (A, B, X).

    Estratégia:
      - Pega candidatos P em G_walk (dist <= X) filtrados por max_candidatos.
      - Para cada candidato, projeta para G_drive e roda o algoritmo escolhido.
      - Compara tempo total: t_walk(A,P) + t_drive(P,B).

    Retorna dict com o melhor P, tempo a pé, tempo de carro, tempo total,
    distância total e o caminho de carro escolhido.
    """
    cand = obter_candidatos_filtrados(G_walk, no_a_walk, x_metros, max_candidatos)
    if not cand:
        return {"erro": "sem candidatos P", "x": x_metros}

    melhor: dict[str, Any] | None = None
    for p_walk, d_walk_m in cand.items():
        t_walk_s = (d_walk_m / 1000.0) / VELOCIDADE_CAMINHADA_KPH * 3600.0
        p_drive = _no_walk_para_drive(G_drive, G_walk, p_walk)
        if p_drive == no_b_drive:
            # Caso raro: P coincide com destino. Sem carro.
            t_drive_s = 0.0
            caminho = [p_drive]
            d_drive_m = 0.0
        else:
            res = algoritmo(G_drive, p_drive, no_b_drive, weight=weight)
            if not res["path"] or res["cost"] == float("inf"):
                continue
            t_drive_s = float(res["cost"])
            caminho = res["path"]
            d_drive_m = _distancia_caminho(G_drive, caminho)

        t_total = t_walk_s + t_drive_s
        d_total = d_walk_m + d_drive_m
        cand_info = {
            "x_metros": x_metros,
            "p_walk_node": p_walk,
            "p_drive_node": p_drive,
            "d_walk_m": float(d_walk_m),
            "t_walk_s": float(t_walk_s),
            "t_drive_s": float(t_drive_s),
            "t_total_s": float(t_total),
            "d_drive_m": float(d_drive_m),
            "d_total_m": float(d_total),
            "caminho_drive": caminho,
        }
        if melhor is None or t_total < melhor["t_total_s"]:
            melhor = cand_info
    return melhor or {"erro": "nenhum caminho viável"}


def _distancia_caminho(G: nx.MultiDiGraph, caminho: list) -> float:
    """Soma `length` ao longo do caminho (em MultiDiGraph, pega o menor)."""
    total = 0.0
    for u, v in zip(caminho[:-1], caminho[1:]):
        edges = G.get_edge_data(u, v) or {}
        if not edges:
            continue
        menor = min(float(d.get("length", 0.0)) for d in edges.values())
        total += menor
    return total


def sweep_x(
    G_drive: nx.MultiDiGraph,
    G_walk: nx.MultiDiGraph,
    no_a_walk: Any,
    no_b_drive: Any,
    valores_x: list[float],
    weight: str = "travel_time",
    algoritmo: Callable = dijkstra_heap,
) -> list[dict[str, Any]]:
    """Roda `escolher_melhor_p` para cada valor de X e devolve a lista."""
    resultados = []
    for x in valores_x:
        r = escolher_melhor_p(
            G_drive,
            G_walk,
            no_a_walk,
            no_b_drive,
            x,
            weight=weight,
            algoritmo=algoritmo,
        )
        resultados.append(r)
    return resultados
