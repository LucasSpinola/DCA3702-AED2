"""
Trânsito sintético para o grafo do RideSmart.

Multiplica o `travel_time` de cada aresta por um fator que depende do tipo
da via. A ideia e simular um cenário de congestionamento realista:
    - Avenidas e rodovias urbanas ficam muito mais lentas no horario de pico.
    - Vias secundárias engasgam menos.
    - Ruas residenciais mantem velocidade quase nominal.

Usa seed fixa para garantir reproducibilidade.
"""
from __future__ import annotations

import random
from typing import Any

import networkx as nx


# Faixas de fator multiplicativo por tipo de via
_FATORES_POR_TIPO: dict[str, tuple[float, float]] = {
    "motorway":     (1.5, 2.5),
    "motorway_link": (1.5, 2.5),
    "trunk":        (1.5, 2.5),
    "trunk_link":   (1.5, 2.5),
    "primary":      (1.5, 2.5),
    "primary_link": (1.4, 2.2),
    "secondary":    (1.2, 1.8),
    "secondary_link": (1.2, 1.8),
    "tertiary":     (1.1, 1.6),
    "tertiary_link": (1.1, 1.6),
    "residential":  (1.0, 1.3),
    "living_street": (1.0, 1.2),
    "unclassified": (1.0, 1.3),
    "service":      (1.0, 1.2),
    "road":         (1.0, 1.3),
}


def aplicar_transito_sintetico(
    G_drive: nx.MultiDiGraph,
    seed: int = 42,
) -> nx.MultiDiGraph:
    """
    Aplica fator de trânsito sintético em `travel_time_synth` (novo atributo).

    Cada aresta recebe um fator amostrado uniformemente na faixa correspondente
    ao seu `highway_norm`. Fatores são sampleados uma vez por aresta (estáveis).

    Também grava `traffic_factor` para inspeção.
    """
    rng = random.Random(seed)
    for _, _, data in G_drive.edges(data=True):
        tipo = data.get("highway_norm", "unclassified")
        faixa = _FATORES_POR_TIPO.get(tipo, (1.0, 1.3))
        fator = rng.uniform(*faixa)
        base = float(data.get("travel_time", 0.0))
        data["traffic_factor"] = float(fator)
        data["travel_time_synth"] = float(base * fator)
    return G_drive


def resumo_transito(G_drive: nx.MultiDiGraph) -> dict[str, Any]:
    """Estatísticas rápidas sobre o fator de trânsito aplicado."""
    from collections import defaultdict
    soma = defaultdict(float)
    cont = defaultdict(int)
    for _, _, data in G_drive.edges(data=True):
        tipo = data.get("highway_norm", "?")
        fator = float(data.get("traffic_factor", 1.0))
        soma[tipo] += fator
        cont[tipo] += 1
    media_por_tipo = {t: soma[t] / cont[t] for t in soma}
    media_geral = sum(soma.values()) / max(sum(cont.values()), 1)
    return {
        "media_geral": media_geral,
        "media_por_tipo": dict(sorted(media_por_tipo.items(), key=lambda x: -x[1])),
        "qtd_arestas": int(sum(cont.values())),
    }
