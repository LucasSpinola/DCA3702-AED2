"""
Gera o dashboard HTML autossuficiente do RideSmart.

Imagens em base64, sem dependencia externa.
"""
from __future__ import annotations

import base64
import html as html_lib
import os
from typing import Any

import pandas as pd

CSS = """
:root {
    --azul:#003366; --azul-claro:#1f77b4; --cinza:#f5f5f5;
    --borda:#dddddd; --texto:#222222;
}
*{box-sizing:border-box}
body{font-family:'Segoe UI',Arial,sans-serif;margin:0;padding:0;color:var(--texto);background:#fff;line-height:1.55}
header{background:var(--azul);color:#fff;padding:32px 24px;text-align:center}
header h1{margin:0;font-size:1.6rem}
header p{margin:8px 0 0;opacity:.92}
main{max-width:1100px;margin:0 auto;padding:24px}
section{margin-bottom:40px}
section h2{color:var(--azul);border-bottom:2px solid var(--azul-claro);padding-bottom:6px;margin-top:0}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}
.card{background:var(--cinza);border:1px solid var(--borda);border-radius:6px;padding:14px;text-align:center}
.card .v{font-size:1.4rem;font-weight:bold;color:var(--azul)}
.card .l{font-size:.85rem;color:#555;margin-top:4px}
.figura{margin:18px 0;text-align:center}
.figura img{max-width:100%;height:auto;border:1px solid var(--borda);border-radius:6px}
.figura figcaption{color:#555;font-size:.9rem;margin-top:6px}
table{width:100%;border-collapse:collapse;margin-top:10px;font-size:.92rem}
th,td{padding:8px 10px;border-bottom:1px solid var(--borda);text-align:left}
th{background:var(--cinza);color:var(--azul)}
tr:hover{background:#fafafa}
footer{text-align:center;padding:20px;color:#888;font-size:.85rem;border-top:1px solid var(--borda);margin-top:40px}
"""

INTEGRANTES_DEFAULT = (
    "Lucas Augusto Spinola Pinto",
    "Membro 2 (a definir)",
    "Membro 3 (a definir)",
    "Membro 4 (a definir)",
)


def _img_b64(caminho: str) -> str:
    with open(caminho, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


def _card(valor: Any, rotulo: str) -> str:
    if isinstance(valor, float):
        v = f"{valor:.2f}"
    else:
        v = str(valor)
    return f'<div class="card"><div class="v">{html_lib.escape(v)}</div><div class="l">{html_lib.escape(rotulo)}</div></div>'


def _figura(b64: str, legenda: str) -> str:
    return f'<figure class="figura"><img src="{b64}" alt="{html_lib.escape(legenda)}"><figcaption>{html_lib.escape(legenda)}</figcaption></figure>'


def _tabela_df(df: pd.DataFrame, max_linhas: int = 20) -> str:
    if df is None or df.empty:
        return "<p><em>Sem dados.</em></p>"
    sub = df.head(max_linhas)
    cabecalho = "".join(f"<th>{html_lib.escape(c)}</th>" for c in sub.columns)
    linhas = []
    for _, row in sub.iterrows():
        celulas = []
        for c in sub.columns:
            v = row[c]
            if isinstance(v, float):
                celulas.append(f"<td>{v:.3f}</td>")
            else:
                celulas.append(f"<td>{html_lib.escape(str(v))}</td>")
        linhas.append("<tr>" + "".join(celulas) + "</tr>")
    return f"<table><thead><tr>{cabecalho}</tr></thead><tbody>{''.join(linhas)}</tbody></table>"


def gerar(
    df_alg: pd.DataFrame,
    df_sweep: pd.DataFrame,
    resumo: dict[str, Any],
    imagens: dict[str, str],
    iframe_mapa: str | None,
    caminho_saida: str,
    integrantes: tuple[str, ...] = INTEGRANTES_DEFAULT,
) -> None:
    """Monta `results/index.html`."""
    os.makedirs(os.path.dirname(caminho_saida) or ".", exist_ok=True)

    melhor_sem = resumo.get("melhor_X_sem_transito") or {}
    melhor_com = resumo.get("melhor_X_com_transito") or {}
    cards = "".join([
        _card(resumo.get("melhor_algoritmo_runtime", "n/d"), "Algoritmo mais rapido"),
        _card(melhor_sem.get("x_metros", "n/d"), "Melhor X sem transito (m)"),
        _card(melhor_com.get("x_metros", "n/d"), "Melhor X com transito (m)"),
        _card(
            f"{(melhor_sem.get('t_total_s', 0) or 0) / 60:.1f} min",
            "Tempo total sem transito",
        ),
        _card(
            f"{(melhor_com.get('t_total_s', 0) or 0) / 60:.1f} min",
            "Tempo total com transito",
        ),
    ])

    blocos_fig = []
    if imagens.get("rede"):
        blocos_fig.append(_figura(_img_b64(imagens["rede"]), "Rede viaria de estudo (UFRN -> Marinha)"))
    if imagens.get("rotas"):
        blocos_fig.append(_figura(_img_b64(imagens["rotas"]), "Rotas comparadas (custos diferentes)"))
    if imagens.get("candidatos"):
        blocos_fig.append(_figura(_img_b64(imagens["candidatos"]), "Candidatos a ponto de embarque P"))
    if imagens.get("tempo_x"):
        blocos_fig.append(_figura(_img_b64(imagens["tempo_x"]), "Tempo total vs X (com e sem transito)"))
    if imagens.get("nodes"):
        blocos_fig.append(_figura(_img_b64(imagens["nodes"]), "Nos expandidos por algoritmo"))
    if imagens.get("runtime"):
        blocos_fig.append(_figura(_img_b64(imagens["runtime"]), "Tempo de execucao por algoritmo"))
    figuras = "".join(blocos_fig)

    integrantes_html = "<ul>" + "".join(
        f"<li>{html_lib.escape(n)}</li>" for n in integrantes
    ) + "</ul>"

    bloco_iframe = (
        f'<iframe src="{html_lib.escape(iframe_mapa)}" '
        f'style="width:100%;height:600px;border:1px solid var(--borda);border-radius:6px"'
        f'></iframe>'
        if iframe_mapa else "<p><em>Mapa interativo nao disponivel.</em></p>"
    )

    html = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="utf-8">
    <title>Trabalho 3 - RideSmart - DCA3702</title>
    <style>{CSS}</style>
</head>
<body>
<header>
    <h1>RideSmart: Modelagem e Analise de Rotas Urbanas com Grafos</h1>
    <p>Projeto Final - DCA3702 - Algoritmos e Estrutura de Dados II - UFRN</p>
</header>
<main>
    <section>
        <h2>1. Integrantes</h2>
        {integrantes_html}
    </section>

    <section>
        <h2>2. Resumo</h2>
        <p>Cenario: <strong>Setor de Aulas IV (UFRN, Lagoa Nova)</strong> ate
        <strong>Comando do 3o Distrito Naval (Santos Reis, Natal/RN)</strong>.
        O usuario aceita caminhar ate X metros antes de embarcar. O sistema
        escolhe o melhor ponto P combinando o tempo a pe e o tempo de carro.</p>
        <div class="cards">{cards}</div>
    </section>

    <section>
        <h2>3. Comparacao dos 4 algoritmos (A -> B sem caminhada)</h2>
        {_tabela_df(df_alg)}
    </section>

    <section>
        <h2>4. Sweep em X (com e sem transito)</h2>
        {_tabela_df(df_sweep, max_linhas=30)}
    </section>

    <section>
        <h2>5. Visualizacoes</h2>
        {figuras}
    </section>

    <section>
        <h2>6. Mapa interativo (folium)</h2>
        {bloco_iframe}
    </section>

    <section>
        <h2>7. Observacoes</h2>
        <ul>
            <li>O algoritmo adicional escolhido foi o Dijkstra Bidirecional. Ele avanca
            duas frentes (uma do origem e outra do destino no grafo reverso) e para
            quando a soma das distancias atinge o melhor candidato. Em redes viarias
            grandes, expande aproximadamente metade dos nos do Dijkstra unidirecional.</li>
            <li>O transito sintetico foi correlacionado com o tipo da via: avenidas
            principais recebem fator entre 1,5 e 2,5; ruas secundarias entre 1,2 e
            1,8; residenciais entre 1,0 e 1,3.</li>
            <li>A heuristica do A* e a distancia de Haversine dividida pela velocidade
            maxima do grafo, o que garante admissibilidade.</li>
        </ul>
    </section>
</main>
<footer>
    {' / '.join(integrantes)} - DCA3702 - UFRN - 2026
</footer>
</body>
</html>
"""
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(html)
