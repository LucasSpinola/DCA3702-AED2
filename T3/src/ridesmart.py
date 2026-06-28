"""
Pipeline RideSmart.

Dado (A, B, X):
    1. Encontra todos os candidatos P em G_drive (nós onde o carro pode pegar
       o usuário) cuja distância de caminhada de A até a posição de P, medida
       em G_walk, é menor ou igual a X metros.
    2. Para cada P candidato:
        - tempo a pé (5 km/h) de A até P (distância real em G_walk).
        - tempo de carro de P até B, usando o algoritmo escolhido.
    3. Escolhe o P* que minimiza o tempo total.

Importante: os candidatos P são nós de G_drive (onde o motorista embarca de
fato). Para garantir consistência entre "até onde o usuário caminha" e "onde
o motorista pega", a distância de caminhada é calculada de A até a projeção
de P em G_walk (nó de G_walk mais próximo geograficamente do nó de G_drive).
"""

from __future__ import annotations

import math
import random
from typing import Any, Callable

import networkx as nx
import osmnx as ox

from .algorithms import dijkstra_heap


# Velocidade de caminhada em km/h
VELOCIDADE_CAMINHADA_KPH = 5.0
MAX_CANDIDATOS = 100


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância geográfica em metros entre dois pontos (lat, lon)."""
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _drive_para_walk(
    G_walk: nx.MultiDiGraph,
    G_drive: nx.MultiDiGraph,
    no_drive: Any,
) -> Any:
    """Para um nó de G_drive, retorna o nó mais próximo em G_walk (em coords)."""
    lat = float(G_drive.nodes[no_drive]["y"])
    lon = float(G_drive.nodes[no_drive]["x"])
    return ox.distance.nearest_nodes(G_walk, X=lon, Y=lat)


def candidatos_p_drive(
    G_walk: nx.MultiDiGraph,
    G_drive: nx.MultiDiGraph,
    no_a_walk: Any,
    x_metros: float,
    margem_busca: float = 1.5,
    tolerancia_projecao_m: float = 200.0,
) -> dict[Any, dict[str, Any]]:
    """
    Retorna {no_drive: {"d_walk_m": x, "q_walk": q_walk, "gap_m": gap}} para
    cada nó de G_drive cuja posição está a até `x_metros` de A medidos pelo
    caminho real em G_walk.

    Estratégia:
        1. Calcula distâncias single-source em G_walk a partir de no_a_walk,
           até `x_metros * margem_busca` (margem para pegar nós de G_walk
           cuja posição cai perto de algum nó de G_drive válido).
        2. Filtra geograficamente nós de G_drive na bounding box +- raio_geo.
        3. Para cada nó de G_drive nessa região, encontra o nó q_walk mais
           próximo geograficamente. Se q_walk está no dicionário do passo 1,
           usa a distância de caminhada de A até q_walk como d_walk.
        4. Mantém só os nós cuja d_walk <= x_metros.
        5. Para nos onde a projecao geografica esta muito longe (> tolerancia),
           descarta porque o motorista nao pegaria onde o pedestre chegou.

    Se x_metros = 0, retorna apenas a projecao de A em G_drive como unico
    candidato (com d_walk = 0).
    """
    # Caso X = 0: candidato unico = projecao de A para G_drive
    if x_metros <= 0:
        lat_a = float(G_walk.nodes[no_a_walk]["y"])
        lon_a = float(G_walk.nodes[no_a_walk]["x"])
        no_a_drive = ox.distance.nearest_nodes(G_drive, X=lon_a, Y=lat_a)
        return {
            no_a_drive: {
                "d_walk_m": 0.0,
                "q_walk": no_a_walk,
                "gap_m": _haversine_m(
                    lat_a, lon_a,
                    float(G_drive.nodes[no_a_drive]["y"]),
                    float(G_drive.nodes[no_a_drive]["x"]),
                ),
            }
        }

    # 1. Single-source em G_walk com cutoff folgado
    cutoff = x_metros * margem_busca
    dist_walk = nx.single_source_dijkstra_path_length(
        G_walk, no_a_walk, cutoff=cutoff, weight="length",
    )

    # 2. Filtra G_drive geograficamente (bounding box) para evitar nearest_nodes
    # global em milhares de candidatos.
    lat_a = float(G_walk.nodes[no_a_walk]["y"])
    lon_a = float(G_walk.nodes[no_a_walk]["x"])
    # raio geografico (linha reta) que cobre x_metros de caminhada com folga
    raio_geo = x_metros * 1.3 + 100.0
    dlat = raio_geo / 111000.0
    dlon = raio_geo / (111000.0 * math.cos(math.radians(lat_a)) + 1e-9)
    lat_min, lat_max = lat_a - dlat, lat_a + dlat
    lon_min, lon_max = lon_a - dlon, lon_a + dlon

    nos_drive_proximos = []
    for n, data in G_drive.nodes(data=True):
        lat = float(data.get("y", 0.0))
        lon = float(data.get("x", 0.0))
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            nos_drive_proximos.append((n, lat, lon))

    if not nos_drive_proximos:
        return {}

    # 3. Para cada no de G_drive na regiao, encontra q_walk mais proximo
    coords_drive = [(lat, lon) for _, lat, lon in nos_drive_proximos]
    lats = [c[0] for c in coords_drive]
    lons = [c[1] for c in coords_drive]
    qs_walk_raw = ox.distance.nearest_nodes(G_walk, X=lons, Y=lats)
    # garante lista de elementos hashable (numpy array vira list de int)
    try:
        qs_walk = [int(q) for q in qs_walk_raw]
    except TypeError:
        qs_walk = [int(qs_walk_raw)]

    candidatos: dict[Any, dict[str, Any]] = {}
    for (n_drive, lat_d, lon_d), q_walk in zip(nos_drive_proximos, qs_walk):
        if q_walk not in dist_walk:
            # nao foi alcancado dentro do cutoff
            continue
        d_walk = float(dist_walk[q_walk])
        if d_walk > x_metros:
            continue
        # checa o gap geografico entre o nó de G_drive e o nó projetado em
        # G_walk; se for grande, a equivalencia P_drive <-> q_walk fica ruim
        lat_q = float(G_walk.nodes[q_walk]["y"])
        lon_q = float(G_walk.nodes[q_walk]["x"])
        gap = _haversine_m(lat_d, lon_d, lat_q, lon_q)
        if gap > tolerancia_projecao_m:
            continue
        # Se o mesmo n_drive ja veio com outro q_walk, mantém o de menor d_walk
        atual = candidatos.get(n_drive)
        if atual is None or d_walk < atual["d_walk_m"]:
            candidatos[n_drive] = {
                "d_walk_m": d_walk,
                "q_walk": q_walk,
                "gap_m": gap,
            }

    return candidatos


def _amostrar(
    candidatos: dict[Any, dict[str, Any]],
    no_a_drive: Any,
    max_candidatos: int,
) -> dict[Any, dict[str, Any]]:
    """Limita o numero de candidatos. Garante que A (X=0) entre na amostra."""
    if len(candidatos) <= max_candidatos:
        return candidatos
    outros = [(n, info) for n, info in candidatos.items() if n != no_a_drive]
    rng = random.Random(42)
    sampled = dict(rng.sample(outros, max_candidatos - 1))
    if no_a_drive in candidatos:
        sampled[no_a_drive] = candidatos[no_a_drive]
    return sampled


def escolher_melhor_p(
    G_drive: nx.MultiDiGraph,
    G_walk: nx.MultiDiGraph,
    no_a_walk: Any,
    no_b_drive: Any,
    x_metros: float,
    weight: str = "travel_time",
    algoritmo: Callable = dijkstra_heap,
    max_candidatos: int = MAX_CANDIDATOS,
    no_a_drive: Any | None = None,
) -> dict[str, Any]:
    """
    Encontra o melhor ponto de embarque P para o cenário (A, B, X).

    Os candidatos P são nós de G_drive (onde o carro embarca). A distância
    de caminhada de cada P é medida em G_walk, pelo caminho real até a
    posição geográfica daquele P.
    """
    candidatos = candidatos_p_drive(G_walk, G_drive, no_a_walk, x_metros)

    # Identifica no_a_drive e garante que ele sempre apareca como candidato com
    # d_walk = 0. Assim, "nao caminhar" sempre e uma opcao avaliada.
    if no_a_drive is None:
        lat_a = float(G_walk.nodes[no_a_walk]["y"])
        lon_a = float(G_walk.nodes[no_a_walk]["x"])
        no_a_drive = ox.distance.nearest_nodes(G_drive, X=lon_a, Y=lat_a)
    if no_a_drive not in candidatos:
        candidatos[no_a_drive] = {
            "d_walk_m": 0.0, "q_walk": no_a_walk, "gap_m": 0.0,
        }

    if not candidatos:
        return {"erro": "sem candidatos P", "x": x_metros}

    candidatos = _amostrar(candidatos, no_a_drive, max_candidatos)

    melhor: dict[str, Any] | None = None
    for p_drive, info in candidatos.items():
        d_walk_m = info["d_walk_m"]
        t_walk_s = (d_walk_m / 1000.0) / VELOCIDADE_CAMINHADA_KPH * 3600.0
        if p_drive == no_b_drive:
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
            "p_drive_node": p_drive,
            "p_walk_node": info["q_walk"],
            "d_walk_m": float(d_walk_m),
            "t_walk_s": float(t_walk_s),
            "t_drive_s": float(t_drive_s),
            "t_total_s": float(t_total),
            "d_drive_m": float(d_drive_m),
            "d_total_m": float(d_total),
            "caminho_drive": caminho,
            "gap_projecao_m": float(info["gap_m"]),
        }
        if melhor is None or t_total < melhor["t_total_s"]:
            melhor = cand_info
    return melhor or {"erro": "nenhum caminho viavel"}


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
    no_a_drive: Any | None = None,
) -> list[dict[str, Any]]:
    """Roda `escolher_melhor_p` para cada valor de X e devolve a lista."""
    resultados = []
    for x in valores_x:
        r = escolher_melhor_p(
            G_drive, G_walk, no_a_walk, no_b_drive, x,
            weight=weight, algoritmo=algoritmo, no_a_drive=no_a_drive,
        )
        resultados.append(r)
    return resultados


# Compatibilidade retroativa: API antiga
def candidatos_p(
    G_walk: nx.MultiDiGraph,
    no_a_walk: Any,
    x_metros: float,
) -> dict[Any, float]:
    """[Deprecated] Retorna {no_walk: dist_walk}. Util para visualizacoes que
    querem mostrar todos os nos de G_walk dentro do raio X."""
    if x_metros <= 0:
        return {no_a_walk: 0.0}
    return dict(nx.single_source_dijkstra_path_length(
        G_walk, no_a_walk, cutoff=x_metros, weight="length",
    ))


def obter_candidatos_filtrados(
    G_walk: nx.MultiDiGraph,
    no_a_walk: Any,
    x_metros: float,
    max_candidatos: int = MAX_CANDIDATOS,
) -> dict[Any, float]:
    """[Deprecated] Versao antiga: candidatos em G_walk com amostragem aleatoria.
    Usada por visualizacoes de candidatos no notebook."""
    cand = candidatos_p(G_walk, no_a_walk, x_metros)
    if not cand:
        return {}
    if len(cand) > max_candidatos:
        outros = [(n, dist) for n, dist in cand.items() if n != no_a_walk]
        rng = random.Random(42)
        sampled = rng.sample(outros, max_candidatos - 1)
        topo = dict(sampled)
        topo[no_a_walk] = 0.0
        return topo
    return cand
