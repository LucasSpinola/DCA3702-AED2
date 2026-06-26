"""
Visualizações do RideSmart.

Estáticas (matplotlib + OSMnx):
    plot_rede_estudo       : mapa da região com A e B marcados.
    plot_rotas             : até 3 rotas no mesmo mapa (cores diferentes).
    plot_candidatos        : buffer de caminhada e candidatos P.
    plot_tempo_vs_x        : gráfico linha tempo total vs X (com e sem trânsito).
    plot_nodes_expanded    : barras de nós expandidos por algoritmo.
    plot_runtime           : barras de tempo de execução por algoritmo.

Interativa (folium):
    mapa_interativo        : HTML com A, B e a rota escolhida em diferentes X.
"""
from __future__ import annotations

import os
from typing import Any

import folium
import matplotlib.pyplot as plt
import networkx as nx
import osmnx as ox
import pandas as pd


def _ensure_dir(caminho: str) -> None:
    pasta = os.path.dirname(caminho)
    if pasta:
        os.makedirs(pasta, exist_ok=True)


def plot_rede_estudo(
    G_drive: nx.MultiDiGraph,
    coord_a: tuple[float, float],
    coord_b: tuple[float, float],
    caminho: str,
) -> None:
    """Mapa simples da rede com A e B destacados."""
    _ensure_dir(caminho)
    fig, ax = ox.plot_graph(
        G_drive, node_size=0, edge_color="#cccccc", edge_linewidth=0.4,
        bgcolor="white", show=False, close=False,
    )
    ax.scatter([coord_a[1]], [coord_a[0]], c="green", s=120, zorder=5, label="A (UFRN)")
    ax.scatter([coord_b[1]], [coord_b[0]], c="red", s=120, zorder=5, label="B (Marinha)")
    ax.legend()
    ax.set_title("Rede viária de estudo: UFRN -> Marinha")
    fig.savefig(caminho, dpi=140, bbox_inches="tight")
    plt.close(fig)


def plot_rotas(
    G_drive: nx.MultiDiGraph,
    rotas: dict[str, list],
    coord_a: tuple[float, float],
    coord_b: tuple[float, float],
    caminho: str,
) -> None:
    """
    Plota varias rotas no mesmo mapa. `rotas` e dict {label: lista_de_nos}.
    """
    _ensure_dir(caminho)
    cores = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
    fig, ax = ox.plot_graph(
        G_drive, node_size=0, edge_color="#dddddd", edge_linewidth=0.3,
        bgcolor="white", show=False, close=False,
    )
    for i, (label, rota) in enumerate(rotas.items()):
        if not rota:
            continue
        cor = cores[i % len(cores)]
        xs = [G_drive.nodes[n]["x"] for n in rota]
        ys = [G_drive.nodes[n]["y"] for n in rota]
        ax.plot(xs, ys, color=cor, linewidth=2.5, alpha=0.8, label=label, zorder=4)
    ax.scatter([coord_a[1]], [coord_a[0]], c="green", s=140, zorder=5, label="A")
    ax.scatter([coord_b[1]], [coord_b[0]], c="red", s=140, zorder=5, label="B")
    ax.legend(loc="upper right")
    ax.set_title("Rotas comparadas (mesma origem e destino, custos diferentes)")
    fig.savefig(caminho, dpi=140, bbox_inches="tight")
    plt.close(fig)


def plot_candidatos(
    G_walk: nx.MultiDiGraph,
    no_a_walk: Any,
    candidatos: dict[Any, float],
    x_metros: float,
    caminho: str,
) -> None:
    """Plota os nós candidatos P dentro do buffer de caminhada X."""
    _ensure_dir(caminho)
    fig, ax = ox.plot_graph(
        G_walk, node_size=0, edge_color="#eeeeee", edge_linewidth=0.3,
        bgcolor="white", show=False, close=False,
    )
    xs = [G_walk.nodes[n]["x"] for n in candidatos.keys()]
    ys = [G_walk.nodes[n]["y"] for n in candidatos.keys()]
    distancias = list(candidatos.values())
    sc = ax.scatter(xs, ys, c=distancias, cmap="viridis", s=20, alpha=0.85, zorder=4)
    plt.colorbar(sc, ax=ax, label="Distância a pé (m)")
    xa = G_walk.nodes[no_a_walk]["x"]
    ya = G_walk.nodes[no_a_walk]["y"]
    ax.scatter([xa], [ya], c="red", s=140, zorder=5, label="A (origem)")
    ax.legend()
    ax.set_title(f"Candidatos a P (raio de caminhada X = {x_metros:.0f} m)")
    fig.savefig(caminho, dpi=140, bbox_inches="tight")
    plt.close(fig)


def plot_tempo_vs_x(df_sweep: pd.DataFrame, caminho: str) -> None:
    """Gráfico linha do tempo total em função de X, para cada cenário."""
    _ensure_dir(caminho)
    fig, ax = plt.subplots(figsize=(8, 5))
    for cenario, sub in df_sweep.groupby("cenario"):
        sub_ord = sub.sort_values("x_metros")
        ax.plot(sub_ord["x_metros"], sub_ord["t_total_s"] / 60.0,
                marker="o", label=cenario, linewidth=2)
    ax.set_xlabel("X (metros de caminhada permitida)")
    ax.set_ylabel("Tempo total da rota (min)")
    ax.set_title("Tempo total da rota A -> P -> B em função de X")
    ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    fig.savefig(caminho, dpi=140)
    plt.close(fig)


def plot_nodes_expanded(df_alg: pd.DataFrame, caminho: str) -> None:
    """Barras com nós expandidos por algoritmo."""
    _ensure_dir(caminho)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(df_alg["algoritmo"], df_alg["nos_expandidos"],
           color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"])
    ax.set_ylabel("Nos expandidos")
    ax.set_title("Comparação de nós expandidos por algoritmo (A -> B)")
    for i, v in enumerate(df_alg["nos_expandidos"]):
        ax.text(i, v, str(int(v)), ha="center", va="bottom", fontsize=9)
    plt.xticks(rotation=15, ha="right"); plt.tight_layout()
    fig.savefig(caminho, dpi=140)
    plt.close(fig)


def plot_runtime(df_alg: pd.DataFrame, caminho: str) -> None:
    """Barras com tempo de execução por algoritmo."""
    _ensure_dir(caminho)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(df_alg["algoritmo"], df_alg["elapsed_ms"],
           color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"])
    ax.set_ylabel("Tempo de execução (ms)")
    ax.set_title("Comparação de runtime por algoritmo (A -> B)")
    ax.set_yscale("log")
    for i, v in enumerate(df_alg["elapsed_ms"]):
        ax.text(i, v, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
    plt.xticks(rotation=15, ha="right"); plt.tight_layout()
    fig.savefig(caminho, dpi=140)
    plt.close(fig)


def mapa_interativo(
    G_drive: nx.MultiDiGraph,
    coord_a: tuple[float, float],
    coord_b: tuple[float, float],
    rotas: dict[str, list],
    caminho: str,
) -> None:
    """
    Mapa folium com A, B e até 4 rotas em camadas selecionáveis.
    """
    _ensure_dir(caminho)
    centro = ((coord_a[0] + coord_b[0]) / 2, (coord_a[1] + coord_b[1]) / 2)
    m = folium.Map(location=centro, zoom_start=13, tiles="OpenStreetMap")
    folium.Marker(coord_a, popup="A: UFRN", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(coord_b, popup="B: Marinha", icon=folium.Icon(color="red")).add_to(m)
    cores = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    for i, (label, rota) in enumerate(rotas.items()):
        if not rota:
            continue
        cor = cores[i % len(cores)]
        coords = [(G_drive.nodes[n]["y"], G_drive.nodes[n]["x"]) for n in rota]
        folium.PolyLine(coords, color=cor, weight=4, opacity=0.85,
                        tooltip=label).add_to(m)
    folium.LayerControl().add_to(m)
    m.save(caminho)
