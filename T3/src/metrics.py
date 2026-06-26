"""
Metricas, comparações e exportações.

Funções:
    comparar_algoritmos    : roda os 4 algoritmos no mesmo par (source, target)
                             e tabula custo, tempo de execução e nós expandidos.
    tabela_sweep_x         : converte a saída de `sweep_x` em DataFrame.
    salvar_csv             : helper para exportar DataFrame em CSV UTF-8.
    salvar_metricas_json   : helper para exportar dict em JSON UTF-8.
"""
from __future__ import annotations

import json
import os
from typing import Any

import networkx as nx
import pandas as pd

from .algorithms import ALGORITMOS


def comparar_algoritmos(
    G_drive: nx.MultiDiGraph,
    source: Any,
    target: Any,
    weight: str = "travel_time",
) -> pd.DataFrame:
    """
    Roda os 4 algoritmos no mesmo par (source, target) e retorna tabela.
    """
    linhas = []
    for nome, func in ALGORITMOS.items():
        res = func(G_drive, source, target, weight=weight)
        linhas.append({
            "algoritmo": nome,
            "custo_s": float(res["cost"]),
            "nos_expandidos": int(res["nodes_expanded"]),
            "elapsed_ms": float(res["elapsed_ms"]),
            "tamanho_caminho": len(res["path"]),
        })
    return pd.DataFrame(linhas)


def tabela_sweep_x(
    sweep_resultados: list[dict[str, Any]],
    cenario: str,
) -> pd.DataFrame:
    """
    Converte a saída de `sweep_x` em DataFrame com coluna `cenário`.
    """
    linhas = []
    for r in sweep_resultados:
        if "erro" in r:
            linhas.append({
                "cenario": cenario, "x_metros": r.get("x"),
                "erro": r["erro"],
            })
            continue
        linhas.append({
            "cenario": cenario,
            "x_metros": float(r["x_metros"]),
            "d_walk_m": float(r["d_walk_m"]),
            "t_walk_s": float(r["t_walk_s"]),
            "d_drive_m": float(r["d_drive_m"]),
            "t_drive_s": float(r["t_drive_s"]),
            "d_total_m": float(r["d_total_m"]),
            "t_total_s": float(r["t_total_s"]),
        })
    return pd.DataFrame(linhas)


def ganho_caminhada(df_sweep: pd.DataFrame) -> pd.DataFrame:
    """
    Anexa colunas com ganho percentual em tempo total versus X=0
    para cada cenário presente no DataFrame.
    """
    df = df_sweep.copy()
    if "t_total_s" not in df.columns:
        return df
    baselines = (
        df[df["x_metros"] == 0]
        .set_index("cenario")["t_total_s"]
        .to_dict()
    )
    df["ganho_pct"] = df.apply(
        lambda r: (baselines.get(r["cenario"], r["t_total_s"]) - r["t_total_s"])
                  / max(baselines.get(r["cenario"], 1.0), 1e-6) * 100.0,
        axis=1,
    )
    return df


def salvar_csv(df: pd.DataFrame, caminho: str) -> None:
    os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
    df.to_csv(caminho, index=False, encoding="utf-8")


def salvar_metricas_json(metricas: dict[str, Any], caminho: str) -> None:
    os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(metricas, f, ensure_ascii=False, indent=2, default=str)


def resumo_geral(
    df_alg: pd.DataFrame,
    df_sweep_sem: pd.DataFrame,
    df_sweep_com: pd.DataFrame,
    transito_resumo: dict[str, Any],
) -> dict[str, Any]:
    """Agrega tudo num dicionário para o dashboard / metricas.json."""
    melhor_alg = df_alg.sort_values("elapsed_ms").iloc[0]["algoritmo"] if not df_alg.empty else None
    melhor_x_sem = (
        df_sweep_sem.sort_values("t_total_s").iloc[0].to_dict()
        if not df_sweep_sem.empty else None
    )
    melhor_x_com = (
        df_sweep_com.sort_values("t_total_s").iloc[0].to_dict()
        if not df_sweep_com.empty else None
    )
    return {
        "comparacao_algoritmos": df_alg.to_dict(orient="records"),
        "melhor_algoritmo_runtime": melhor_alg,
        "melhor_X_sem_transito": melhor_x_sem,
        "melhor_X_com_transito": melhor_x_com,
        "resumo_transito": transito_resumo,
    }
