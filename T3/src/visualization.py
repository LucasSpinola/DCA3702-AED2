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
from branca.element import Element
import math


def _ensure_dir(caminho: str) -> None:
    pasta = os.path.dirname(caminho)
    if pasta:
        os.makedirs(pasta, exist_ok=True)


def plot_rede_estudo(
    G_drive: nx.MultiDiGraph,
    coord_a: tuple[float, float],
    coord_b: tuple[float, float],
    caminho: str,
    nome_a: str = "A (UFRN)",
    nome_b: str = "B (Marinha)",
) -> None:
    """Mapa simples da rede com A e B destacados."""
    _ensure_dir(caminho)
    fig, ax = ox.plot_graph(
        G_drive,
        node_size=0,
        edge_color="#cccccc",
        edge_linewidth=0.4,
        bgcolor="white",
        show=False,
        close=False,
    )
    ax.scatter([coord_a[1]], [coord_a[0]], c="green", s=120, zorder=5, label=nome_a)
    ax.scatter([coord_b[1]], [coord_b[0]], c="red", s=120, zorder=5, label=nome_b)
    ax.legend()
    ax.set_title(f"Rede viária de estudo: {nome_a} -> {nome_b}")
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
        G_drive,
        node_size=0,
        edge_color="#dddddd",
        edge_linewidth=0.3,
        bgcolor="white",
        show=False,
        close=False,
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
    candidatos_selecionados: dict[Any, float] | None = None,
    melhor_p: Any | None = None,
    caminho_walk: list[Any] | None = None,
    melhor_p_com: Any | None = None,
    caminho_walk_com: list[Any] | None = None,
    melhor_p_sem: Any | None = None,
    caminho_walk_sem: list[Any] | None = None,
) -> None:
    """
    Plota os nós candidatos P dentro do buffer de caminhada X.
    Se candidatos_selecionados for fornecido, plota em subplots.
    Se melhor_p_com ou melhor_p_sem for fornecido, plota uma coluna adicional com a melhor escolha e o trajeto.
    """
    _ensure_dir(caminho)

    melhor_p_com_efetivo = melhor_p_com if melhor_p_com is not None else melhor_p
    caminho_walk_com_efetivo = (
        caminho_walk_com if caminho_walk_com is not None else caminho_walk
    )
    tem_3_colunas = melhor_p_com_efetivo is not None or melhor_p_sem is not None

    if candidatos_selecionados is None:
        # Modo antigo: gráfico único
        fig, ax = ox.plot_graph(
            G_walk,
            node_size=0,
            edge_color="#cccccc",
            edge_linewidth=0.6,
            bgcolor="white",
            show=False,
            close=False,
        )
        xs = [G_walk.nodes[n]["x"] for n in candidatos.keys()]
        ys = [G_walk.nodes[n]["y"] for n in candidatos.keys()]
        distancias = list(candidatos.values())
        sc = ax.scatter(
            xs, ys, c=distancias, cmap="viridis", s=20, alpha=0.85, zorder=4
        )
        plt.colorbar(sc, ax=ax, label="Distância a pé (m)")
        xa = G_walk.nodes[no_a_walk]["x"]
        ya = G_walk.nodes[no_a_walk]["y"]
        ax.scatter([xa], [ya], c="red", s=140, zorder=5, label="A (origem)")

        xa = G_walk.nodes[no_a_walk]["x"]
        ya = G_walk.nodes[no_a_walk]["y"]
        raio_exibicao = max(x_metros, 100.0) * 1.15
        delta_lat = raio_exibicao / 111000.0
        delta_lon = raio_exibicao / (111000.0 * math.cos(math.radians(ya)))
        ax.set_xlim(xa - delta_lon, xa + delta_lon)
        ax.set_ylim(ya - delta_lat, ya + delta_lat)

        ax.legend()
        ax.set_title(f"Candidatos a P (raio de caminhada X = {x_metros:.0f} m)")
    else:
        # Temos 2 ou 3 colunas
        if tem_3_colunas:
            fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))
        else:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Plotamos a rede de fundo nos subplots
        ox.plot_graph(
            G_walk,
            ax=ax1,
            node_size=0,
            edge_color="#cccccc",
            edge_linewidth=0.6,
            bgcolor="white",
            show=False,
            close=False,
        )
        ox.plot_graph(
            G_walk,
            ax=ax2,
            node_size=0,
            edge_color="#cccccc",
            edge_linewidth=0.6,
            bgcolor="white",
            show=False,
            close=False,
        )
        if tem_3_colunas:
            ox.plot_graph(
                G_walk,
                ax=ax3,
                node_size=0,
                edge_color="#cccccc",
                edge_linewidth=0.6,
                bgcolor="white",
                show=False,
                close=False,
            )

        # Coordenadas e distâncias de todos os candidatos
        xs = [G_walk.nodes[n]["x"] for n in candidatos.keys()]
        ys = [G_walk.nodes[n]["y"] for n in candidatos.keys()]
        distancias = list(candidatos.values())

        # Coordenadas e distâncias dos candidatos selecionados
        xs_sel = [G_walk.nodes[n]["x"] for n in candidatos_selecionados.keys()]
        ys_sel = [G_walk.nodes[n]["y"] for n in candidatos_selecionados.keys()]
        distancias_sel = list(candidatos_selecionados.values())

        # Scatter no subplot 1 (Todos)
        sc1 = ax1.scatter(
            xs, ys, c=distancias, cmap="viridis", s=25, alpha=0.85, zorder=4
        )
        # Scatter no subplot 2 (Selecionados)
        sc2 = ax2.scatter(
            xs_sel,
            ys_sel,
            c=distancias_sel,
            cmap="viridis",
            s=50,
            alpha=0.9,
            zorder=4,
            edgecolor="black",
            linewidth=0.5,
        )

        # Adiciona a barra de cores
        plt.colorbar(sc1, ax=ax1, label="Distância a pé (m)")
        plt.colorbar(sc2, ax=ax2, label="Distância a pé (m)")

        # Origem A
        xa = G_walk.nodes[no_a_walk]["x"]
        ya = G_walk.nodes[no_a_walk]["y"]
        ax1.scatter([xa], [ya], c="red", s=140, zorder=5, label="A (origem)")
        ax2.scatter([xa], [ya], c="red", s=140, zorder=5, label="A (origem)")

        # Terceira coluna
        if tem_3_colunas:
            ax3.scatter([xa], [ya], c="red", s=140, zorder=5, label="A (origem)")

            # Caso 1: Ambos coincidem com a origem
            if melhor_p_com_efetivo == no_a_walk and melhor_p_sem == no_a_walk:
                ax3.text(
                    xa,
                    ya,
                    "  P* (Com e Sem) = A",
                    fontsize=11,
                    fontweight="bold",
                    color="purple",
                    zorder=6,
                )
            else:
                # Caso 2: P* sem trânsito
                if melhor_p_sem is not None:
                    if melhor_p_sem == no_a_walk:
                        ax3.text(
                            xa,
                            ya,
                            "  P* (Sem Trânsito) = A",
                            fontsize=9,
                            fontweight="bold",
                            color="#17becf",
                            zorder=6,
                        )
                    else:
                        xp_sem = G_walk.nodes[melhor_p_sem]["x"]
                        yp_sem = G_walk.nodes[melhor_p_sem]["y"]
                        label_sem = (
                            "P* (Sem Trânsito)"
                            if melhor_p_sem != melhor_p_com_efetivo
                            else "P* (Sem e Com Trânsito)"
                        )
                        ax3.scatter(
                            [xp_sem],
                            [yp_sem],
                            c="#17becf",
                            s=140,
                            zorder=5,
                            label=label_sem,
                        )
                        if caminho_walk_sem:
                            xs_path_sem = [
                                G_walk.nodes[n]["x"] for n in caminho_walk_sem
                            ]
                            ys_path_sem = [
                                G_walk.nodes[n]["y"] for n in caminho_walk_sem
                            ]
                            label_path_sem = (
                                "A pé (Sem Trânsito)"
                                if melhor_p_sem != melhor_p_com_efetivo
                                else "A pé (Sem e Com Trânsito)"
                            )
                            ax3.plot(
                                xs_path_sem,
                                ys_path_sem,
                                color="#17becf",
                                linestyle="--",
                                linewidth=3.5,
                                label=label_path_sem,
                                zorder=6,
                            )

                # Caso 3: P* com trânsito
                if (
                    melhor_p_com_efetivo is not None
                    and melhor_p_com_efetivo != melhor_p_sem
                ):
                    if melhor_p_com_efetivo == no_a_walk:
                        ax3.text(
                            xa,
                            ya,
                            "  P* (Com Trânsito) = A",
                            fontsize=9,
                            fontweight="bold",
                            color="#1f77b4",
                            zorder=6,
                        )
                    else:
                        xp_com = G_walk.nodes[melhor_p_com_efetivo]["x"]
                        yp_com = G_walk.nodes[melhor_p_com_efetivo]["y"]
                        ax3.scatter(
                            [xp_com],
                            [yp_com],
                            c="#1f77b4",
                            s=140,
                            zorder=5,
                            label="P* (Com Trânsito)",
                        )
                        if caminho_walk_com_efetivo:
                            xs_path_com = [
                                G_walk.nodes[n]["x"] for n in caminho_walk_com_efetivo
                            ]
                            ys_path_com = [
                                G_walk.nodes[n]["y"] for n in caminho_walk_com_efetivo
                            ]
                            ax3.plot(
                                xs_path_com,
                                ys_path_com,
                                color="#1f77b4",
                                linewidth=3.5,
                                label="A pé (Com Trânsito)",
                                zorder=6,
                            )

            ax3.legend(loc="upper right")
            ax3.set_title("Melhor Escolha e Trajeto a pé")

        # Zoom síncrono centrado na origem A
        xa = G_walk.nodes[no_a_walk]["x"]
        ya = G_walk.nodes[no_a_walk]["y"]
        raio_exibicao = max(x_metros, 100.0) * 1.15
        delta_lat = raio_exibicao / 111000.0
        delta_lon = raio_exibicao / (111000.0 * math.cos(math.radians(ya)))

        axes = [ax1, ax2]
        if tem_3_colunas:
            axes.append(ax3)

        for ax in axes:
            ax.set_xlim(xa - delta_lon, xa + delta_lon)
            ax.set_ylim(ya - delta_lat, ya + delta_lat)

        ax1.legend(loc="upper right")
        ax2.legend(loc="upper right")
        ax1.set_title(f"Todos os Candidatos (raio X = {x_metros:.0f} m)")
        ax2.set_title(f"Apenas os {len(candidatos_selecionados)} Selecionados")
    fig.savefig(caminho, dpi=140, bbox_inches="tight")
    plt.close(fig)


def plot_tempo_vs_x(df_sweep: pd.DataFrame, caminho: str) -> None:
    """Gráfico linha do tempo total em função de X, para cada cenário."""
    _ensure_dir(caminho)
    fig, ax = plt.subplots(figsize=(8, 5))
    for cenario, sub in df_sweep.groupby("cenario"):
        sub_ord = sub.sort_values("x_metros")
        ax.plot(
            sub_ord["x_metros"],
            sub_ord["t_total_s"] / 60.0,
            marker="o",
            label=cenario,
            linewidth=2,
        )
    ax.set_xlabel("X (metros de caminhada permitida)")
    ax.set_ylabel("Tempo total da rota (min)")
    ax.set_title("Tempo total da rota A -> P -> B em função de X")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    fig.savefig(caminho, dpi=140)
    plt.close(fig)


def plot_nodes_expanded(df_alg: pd.DataFrame, caminho: str) -> None:
    """Barras com nós expandidos por algoritmo."""
    _ensure_dir(caminho)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(
        df_alg["algoritmo"],
        df_alg["nos_expandidos"],
        color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],
    )
    ax.set_ylabel("Nos expandidos")
    ax.set_title("Comparação de nós expandidos por algoritmo (A -> B)")
    for i, v in enumerate(df_alg["nos_expandidos"]):
        ax.text(i, v, str(int(v)), ha="center", va="bottom", fontsize=9)
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    fig.savefig(caminho, dpi=140)
    plt.close(fig)


def plot_runtime(df_alg: pd.DataFrame, caminho: str) -> None:
    """Barras com tempo de execução por algoritmo."""
    _ensure_dir(caminho)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(
        df_alg["algoritmo"],
        df_alg["elapsed_ms"],
        color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"],
    )
    ax.set_ylabel("Tempo de execução (ms)")
    ax.set_title("Comparação de runtime por algoritmo (A -> B)")
    ax.set_yscale("log")
    for i, v in enumerate(df_alg["elapsed_ms"]):
        ax.text(i, v, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
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
    folium.Marker(coord_a, popup="A: Origem", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(coord_b, popup="B: Destino", icon=folium.Icon(color="red")).add_to(m)

    # Organiza cores por tipo de cenário para facilitar distinção visual
    tons_sem = ["#2ca02c", "#17becf", "#6baed6", "#9ecae1", "#4292c6"]  # Tons frios
    tons_com = ["#d62728", "#ff7f0e", "#e377c2", "#fdae6b", "#fdd0a2"]  # Tons quentes
    idx_sem = 0
    idx_com = 0

    legend_items = []

    for i, (label, rota) in enumerate(rotas.items()):
        if not rota:
            continue

        label_lower = label.lower()
        if "sem transito" in label_lower or "sem trânsito" in label_lower:
            cor = tons_sem[idx_sem % len(tons_sem)]
            idx_sem += 1
        elif "com transito" in label_lower or "com trânsito" in label_lower:
            cor = tons_com[idx_com % len(tons_com)]
            idx_com += 1
        else:
            cor = ["#9467bd", "#8c564b", "#bcbd22", "#7f7f7f"][i % 4]

        coords = [(G_drive.nodes[n]["y"], G_drive.nodes[n]["x"]) for n in rota]

        # Cria FeatureGroup para permitir controle de camadas individual
        fg = folium.FeatureGroup(name=label)
        folium.PolyLine(
            coords, color=cor, weight=5, opacity=0.85, tooltip=label
        ).add_to(fg)
        fg.add_to(m)

        # Adiciona item na legenda
        legend_items.append(f"""
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="background-color: {cor}; width: 24px; height: 4px; display: inline-block; border-radius: 2px;"></span>
          <span style="color: #444; font-weight: 500;">{label}</span>
        </div>
        """)

    # Adiciona a legenda flutuante em HTML
    legend_html = f"""
    <div style="
        position: fixed; 
        bottom: 30px; 
        left: 30px; 
        width: 250px; 
        z-index: 9999; 
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(0, 0, 0, 0.15); 
        border-radius: 8px; 
        padding: 12px; 
        font-size: 13px; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    ">
      <h4 style="margin: 0 0 10px 0; font-size: 14px; font-weight: 600; color: #333; border-bottom: 1px solid #eee; padding-bottom: 6px;">Legenda do Mapa</h4>
      
      <!-- Marcadores de Origem e Destino -->
      <div style="display: flex; flex-direction: column; gap: 6px; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 8px;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="background-color: #2ca02c; width: 10px; height: 10px; display: inline-block; border-radius: 50%;"></span>
          <span style="color: #444; font-weight: 500;">Origem (A)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="background-color: #d62728; width: 10px; height: 10px; display: inline-block; border-radius: 50%;"></span>
          <span style="color: #444; font-weight: 500;">Destino (B)</span>
        </div>
      </div>

      <!-- Caminhos das Rotas -->
      <div style="display: flex; flex-direction: column; gap: 8px;">
        {"".join(legend_items)}
      </div>
    </div>
    """
    m.get_root().html.add_child(Element(legend_html))

    folium.LayerControl().add_to(m)
    m.save(caminho)
