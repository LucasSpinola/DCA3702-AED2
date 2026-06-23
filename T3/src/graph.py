"""
Construcao da rede viaria para o RideSmart.

Sao baixados dois grafos da regiao de estudo via OSMnx:
    G_drive : tipo 'drive' (vias para carro), usado no trecho P -> B.
    G_walk  : tipo 'walk'  (incluindo pedestre), usado no trecho A -> P.

Cada aresta de G_drive recebe tres atributos de peso:
    length      : metros (peso original do OSMnx).
    travel_time : segundos sem transito (length / speed_kph * 3.6).
    travel_time_synth : segundos com transito sintetico (ver traffic.py).
"""
from __future__ import annotations

import math
import os
from typing import Any

import networkx as nx
import osmnx as ox


# Coordenadas do cenario UFRN -> Marinha
COORD_A = (-5.842450, -35.199750)  # Setor de Aulas IV, UFRN
COORD_B = (-5.770120, -35.197480)  # 3o Distrito Naval, Santos Reis
# Ponto medio aproximado entre A e B (usado como centro da bbox)
CENTRO = ((COORD_A[0] + COORD_B[0]) / 2, (COORD_A[1] + COORD_B[1]) / 2)
# Raio para download (cobre A, B e regiao entre eles com folga)
RAIO_METROS = 10000


def baixar_grafos(
    centro: tuple[float, float] = CENTRO,
    raio: int = RAIO_METROS,
    cache_dir: str | None = None,
) -> tuple[nx.MultiDiGraph, nx.MultiDiGraph]:
    """
    Baixa os grafos 'drive' e 'walk' da regiao.

    Configura o cache do OSMnx em `cache_dir` para evitar re-download.
    """
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        ox.settings.cache_folder = cache_dir
        ox.settings.use_cache = True

    print(f"  [graph] baixando rede 'drive' em {centro}, raio={raio} m")
    G_drive = ox.graph_from_point(centro, dist=raio, network_type="drive")

    print(f"  [graph] baixando rede 'walk' em {centro}, raio={raio} m")
    G_walk = ox.graph_from_point(centro, dist=raio, network_type="walk")

    return G_drive, G_walk


# Velocidades padrao (km/h) por tipo de via para preencher `maxspeed` ausente
_VELOCIDADE_PADRAO_KPH = {
    "motorway": 80, "motorway_link": 60,
    "trunk": 70, "trunk_link": 50,
    "primary": 60, "primary_link": 50,
    "secondary": 50, "secondary_link": 40,
    "tertiary": 40, "tertiary_link": 30,
    "residential": 30, "living_street": 20,
    "unclassified": 30, "service": 20,
    "road": 30,
}


def _normalizar_highway(valor: Any) -> str:
    """OSMnx pode retornar 'highway' como string ou lista. Pega o primeiro."""
    if isinstance(valor, list):
        return valor[0] if valor else "unclassified"
    return valor if isinstance(valor, str) else "unclassified"


def _normalizar_maxspeed(valor: Any) -> float | None:
    """Converte 'maxspeed' em km/h (float). Aceita string '60', '60 km/h' ou lista."""
    if valor is None:
        return None
    if isinstance(valor, list):
        # Lista de maxspeeds: usa a menor (mais conservadora)
        candidatos = [_normalizar_maxspeed(v) for v in valor]
        candidatos = [c for c in candidatos if c is not None]
        return min(candidatos) if candidatos else None
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, str):
        v = valor.lower().replace("km/h", "").replace("kph", "").strip()
        try:
            return float(v.split()[0])
        except (ValueError, IndexError):
            return None
    return None


def adicionar_pesos(G_drive: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """
    Anexa `length`, `speed_kph` e `travel_time` a cada aresta de `G_drive`.
    Usa defaults em `_VELOCIDADE_PADRAO_KPH` quando `maxspeed` esta ausente.

    Retorna o proprio `G_drive` modificado in-place.
    """
    for _, _, data in G_drive.edges(data=True):
        tipo = _normalizar_highway(data.get("highway"))
        speed_kph = _normalizar_maxspeed(data.get("maxspeed"))
        if speed_kph is None or speed_kph <= 0:
            speed_kph = _VELOCIDADE_PADRAO_KPH.get(tipo, 30.0)
        length_m = float(data.get("length", 0.0))
        # tempo (s) = (length_m / 1000) / speed_kph * 3600
        travel_time_s = (length_m / max(speed_kph, 0.1)) * 3.6
        data["highway_norm"] = tipo
        data["speed_kph"] = float(speed_kph)
        data["travel_time"] = float(travel_time_s)
    return G_drive


def adicionar_length_walk(G_walk: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """
    Garante que cada aresta de `G_walk` tenha `length` (metros) numerico.
    OSMnx ja entrega length, mas alguns proxies retornam string.
    """
    for _, _, data in G_walk.edges(data=True):
        data["length"] = float(data.get("length", 0.0))
    return G_walk


def encontrar_nos(
    G_drive: nx.MultiDiGraph,
    G_walk: nx.MultiDiGraph,
    coord_a: tuple[float, float] = COORD_A,
    coord_b: tuple[float, float] = COORD_B,
) -> dict[str, Any]:
    """
    Localiza os nos mais proximos de A (em G_walk) e de B (em G_drive).
    Tambem identifica o no equivalente a A em G_drive (usado quando X=0).
    """
    # OSMnx 2.x usa (X, Y) = (longitude, latitude)
    lon_a, lat_a = coord_a[1], coord_a[0]
    lon_b, lat_b = coord_b[1], coord_b[0]

    no_a_walk = ox.distance.nearest_nodes(G_walk, X=lon_a, Y=lat_a)
    no_a_drive = ox.distance.nearest_nodes(G_drive, X=lon_a, Y=lat_a)
    no_b_drive = ox.distance.nearest_nodes(G_drive, X=lon_b, Y=lat_b)

    return {
        "no_a_walk": no_a_walk,
        "no_a_drive": no_a_drive,
        "no_b_drive": no_b_drive,
        "coord_a": coord_a,
        "coord_b": coord_b,
    }


def haversine_metros(coord1: tuple[float, float], coord2: tuple[float, float]) -> float:
    """Distancia geografica entre dois pontos (lat, lon) em metros."""
    R = 6371000.0  # raio da Terra em metros
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def salvar_graphml(G: nx.Graph, caminho: str) -> None:
    """Sanitiza atributos e salva em GraphML."""
    os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
    tipos_validos = (str, int, float, bool)
    for _, _, data in G.edges(data=True):
        for k in list(data.keys()):
            v = data[k]
            if v is None:
                del data[k]
            elif not isinstance(v, tipos_validos):
                data[k] = str(v)
    for _, data in G.nodes(data=True):
        for k in list(data.keys()):
            v = data[k]
            if v is None:
                del data[k]
            elif not isinstance(v, tipos_validos):
                data[k] = str(v)
    nx.write_graphml(G, caminho)
