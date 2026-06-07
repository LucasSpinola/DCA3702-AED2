"""
Gera o dashboard HTML autossuficiente do projeto.

A pagina e construida por interpolacao de strings (sem framework). Imagens
do Matplotlib sao embutidas em base64 para que o arquivo HTML possa ser
aberto offline (e funcionar via GitHub raw) sem dependencias externas.

Estrutura do dashboard:
    1. Cabecalho do projeto
    2. Resumo (noticias, entidades, metricas-chave)
    3. Visualizacoes estaticas (imagens embutidas)
    4. Tabela top-20 por PageRank
    5. Iframe com o grafo interativo (PyVis)
    6. Conclusoes
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
header h1{margin:0;font-size:1.8rem}
header p{margin:8px 0 0;opacity:.9}
main{max-width:1100px;margin:0 auto;padding:24px}
section{margin-bottom:40px}
section h2{color:var(--azul);border-bottom:2px solid var(--azul-claro);padding-bottom:6px;margin-top:0}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}
.card{background:var(--cinza);border:1px solid var(--borda);border-radius:6px;padding:14px;text-align:center}
.card .v{font-size:1.6rem;font-weight:bold;color:var(--azul)}
.card .l{font-size:.85rem;color:#555;margin-top:4px}
.figura{margin:18px 0;text-align:center}
.figura img{max-width:100%;height:auto;border:1px solid var(--borda);border-radius:6px}
.figura figcaption{color:#555;font-size:.9rem;margin-top:6px}
table{width:100%;border-collapse:collapse;margin-top:10px;font-size:.92rem}
th,td{padding:8px 10px;border-bottom:1px solid var(--borda);text-align:left}
th{background:var(--cinza);color:var(--azul)}
tr:hover{background:#fafafa}
.tag{display:inline-block;padding:2px 8px;border-radius:12px;font-size:.75rem;color:#fff}
iframe{width:100%;height:720px;border:1px solid var(--borda);border-radius:6px}
footer{text-align:center;padding:20px;color:#888;font-size:.85rem;border-top:1px solid var(--borda);margin-top:40px}
"""

CORES_TIPO = {
    "PESSOA":       "#1f77b4",
    "ORGANIZACAO":  "#ff7f0e",
    "CENTRO":       "#2ca02c",
    "DEPARTAMENTO": "#d62728",
    "PROJETO":      "#9467bd",
    "EVENTO":       "#8c564b",
    "LABORATORIO":  "#e377c2",
    "SISTEMA":      "#17becf",
}


def _img_b64(caminho: str) -> str:
    """Le um PNG e retorna como data URI base64."""
    with open(caminho, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")


def _tag(tipo: str) -> str:
    cor = CORES_TIPO.get(tipo, "#999999")
    return f'<span class="tag" style="background:{cor}">{html_lib.escape(tipo)}</span>'


def _card(valor: Any, rotulo: str) -> str:
    if isinstance(valor, float):
        v = f"{valor:.4f}" if valor < 1 else f"{valor:.2f}"
    else:
        v = str(valor)
    return f'<div class="card"><div class="v">{v}</div><div class="l">{rotulo}</div></div>'


def _figura(b64: str, legenda: str) -> str:
    return f'<figure class="figura"><img src="{b64}" alt="{legenda}"><figcaption>{legenda}</figcaption></figure>'


def gerar(
    metricas: dict[str, Any],
    df_top: pd.DataFrame,
    num_noticias: int,
    num_entidades_unicas: int,
    imagens: dict[str, str],
    iframe_html: str | None,
    caminho_saida: str,
    comparacao_aleatorios: dict | None = None,
    contagem_arestas: dict[str, int] | None = None,
) -> None:
    """
    Monta o HTML do dashboard.

    Parametros:
        metricas: dict de metricas estruturais
        df_top: DataFrame com top-N entidades (colunas: node, tipo, pagerank, ...)
        num_noticias: total de noticias processadas
        num_entidades_unicas: total de entidades unicas
        imagens: dict {chave: caminho_png}
        iframe_html: caminho relativo ao iframe do grafo interativo (ou None)
        caminho_saida: caminho do arquivo HTML a salvar
    """
    os.makedirs(os.path.dirname(caminho_saida) or ".", exist_ok=True)

    cards = "".join([
        _card(num_noticias, "Noticias processadas"),
        _card(num_entidades_unicas, "Entidades unicas"),
        _card(metricas["num_nos"], "Nos no grafo"),
        _card(metricas["num_arestas_simples"], "Arestas (grafo simples)"),
        _card(metricas["densidade"], "Densidade"),
        _card(metricas["componentes_conectados"], "Componentes conectados"),
        _card(metricas["grau_medio"], "Grau medio"),
        _card(metricas.get("diametro_maior_componente", "n/d"), "Diametro (maior comp.)"),
        _card(metricas["coeficiente_agrupamento_medio"], "Coef. agrupamento medio"),
        _card(metricas["transitividade"], "Transitividade"),
    ])

    blocos_fig = [
        _figura(_img_b64(imagens["hist_grau"]),          "Distribuicao de grau dos nos"),
        _figura(_img_b64(imagens["top_pagerank"]),       "Top entidades por PageRank"),
        _figura(_img_b64(imagens["distribuicao_tipos"]), "Distribuicao de tipos de entidade"),
        _figura(_img_b64(imagens["componentes"]),        "Tamanho das maiores componentes"),
        _figura(_img_b64(imagens["grafo_estatico"]),     "Grafo estatico - top entidades"),
    ]
    if "comparacao_aleatorios" in imagens:
        blocos_fig.append(_figura(
            _img_b64(imagens["comparacao_aleatorios"]),
            "Comparacao com grafos aleatorios (ER e WS)",
        ))
    figuras = "".join(blocos_fig)

    linhas_tabela = []
    for i, row in df_top.iterrows():
        linhas_tabela.append(
            "<tr>"
            f"<td>{i+1}</td>"
            f"<td>{html_lib.escape(str(row['node']))}</td>"
            f"<td>{_tag(row['tipo'])}</td>"
            f"<td>{row['pagerank']:.4f}</td>"
            f"<td>{row['betweenness']:.4f}</td>"
            f"<td>{row['closeness']:.4f}</td>"
            f"<td>{row['eigenvector']:.4f}</td>"
            f"<td>{int(row['frequencia'])}</td>"
            "</tr>"
        )
    tabela = (
        "<table><thead><tr>"
        "<th>#</th><th>Entidade</th><th>Tipo</th><th>PageRank</th>"
        "<th>Betweenness</th><th>Closeness</th><th>Eigenvector</th><th>Frequencia</th>"
        "</tr></thead><tbody>"
        + "".join(linhas_tabela)
        + "</tbody></table>"
    )

    if iframe_html:
        bloco_iframe = f'<iframe src="{iframe_html}" loading="lazy"></iframe>'
    else:
        bloco_iframe = "<p><em>Grafo interativo nao disponivel.</em></p>"

    bloco_aleatorios = ""
    if comparacao_aleatorios and "erro" not in comparacao_aleatorios:
        cmp = comparacao_aleatorios
        cam_er = cmp["er"]["caminho_medio"]
        cam_ws = cmp["ws"]["caminho_medio"]
        cam_er_s = f"{cam_er:.4f}" if cam_er is not None else "—"
        cam_ws_s = f"{cam_ws:.4f}" if cam_ws is not None else "—"
        cam_real_s = f"{cmp['real']['caminho_medio']:.4f}" if cmp['real']['caminho_medio'] is not None else "—"
        bloco_aleatorios = (
            '<section>'
            '<h2>3.1 Rede real vs grafos aleatorios</h2>'
            '<p>Para validar a hipotese <strong>small-world</strong>, comparamos a rede '
            'real com (i) Erdos-Renyi (mesma densidade) e (ii) Watts-Strogatz '
            '(mesmo grau medio, p_rewire=0,1).</p>'
            '<table><thead><tr><th>Modelo</th><th>n</th><th>Clustering</th><th>Caminho medio</th></tr></thead>'
            f'<tbody>'
            f'<tr><td>Real</td><td>{cmp["real"]["n"]}</td>'
            f'<td><strong>{cmp["real"]["clustering"]:.4f}</strong></td>'
            f'<td><strong>{cam_real_s}</strong></td></tr>'
            f'<tr><td>Erdos-Renyi</td><td>{cmp["er"]["n"]}</td>'
            f'<td>{cmp["er"]["clustering"]:.4f}</td><td>{cam_er_s}</td></tr>'
            f'<tr><td>Watts-Strogatz</td><td>{cmp["ws"]["n"]}</td>'
            f'<td>{cmp["ws"]["clustering"]:.4f}</td><td>{cam_ws_s}</td></tr>'
            '</tbody></table>'
            '<p style="margin-top:10px;color:#555;font-size:.92rem"><em>Assinatura '
            'small-world:</em> clustering real muito maior que ER, com caminho medio '
            'comparavel. Confirma estrutura genuinamente nao aleatoria.</p>'
            '</section>'
        )

    bloco_arestas = ""
    if contagem_arestas:
        linhas = "".join(
            f"<tr><td>{html_lib.escape(tipo)}</td><td>{qtd}</td></tr>"
            for tipo, qtd in contagem_arestas.items()
        )
        bloco_arestas = f"""
        <section>
            <h2>3.2 Distribuicao por tipo de relacao</h2>
            <p>As arestas sao tipadas pela combinacao dos tipos dos nos
            (PESSOA -> DEPARTAMENTO = PERTENCE_A, etc.). Esta a distribuicao:</p>
            <table>
                <thead><tr><th>Tipo de relacao</th><th>Quantidade</th></tr></thead>
                <tbody>{linhas}</tbody>
            </table>
        </section>
        """

    conclusoes = """
    <ul>
        <li>O grafo construido reflete as conexoes implicitas entre entidades nas
            noticias da UFRN: pessoas, departamentos, centros, projetos e eventos
            aparecem co-ocorrendo nos mesmos textos.</li>
        <li>As entidades de maior PageRank correspondem a hubs institucionais
            (UFRN, IMD, ECT, etc.), o que valida o pipeline NER + co-ocorrencia.</li>
        <li>A betweenness destaca entidades que sao pontes entre regioes diferentes
            do grafo - tipicamente coordenadores ou organizacoes intermediarias.</li>
        <li>Limitacoes: o NER do spaCy comete erros em nomes proprios pouco
            frequentes; o EntityRuler mitiga isso para entidades-chave da UFRN.</li>
    </ul>
    """

    html = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="utf-8">
    <title>Trabalho 1 - Rede de Noticias da UFRN</title>
    <style>{CSS}</style>
</head>
<body>
<header>
    <h1>Rede de Relacionamentos nas Noticias da UFRN</h1>
    <p>Trabalho 1 - DCA3702 - Algoritmos e Estrutura de Dados II - UFRN</p>
</header>
<main>
    <section>
        <h2>1. Resumo</h2>
        <p>Este dashboard consolida a analise da rede de entidades extraidas
        automaticamente das noticias publicadas no portal institucional da UFRN.
        Pessoas, departamentos, centros, projetos e organizacoes foram conectados
        por co-ocorrencia em noticias, formando um grafo direcionado e analisado
        com metricas de teoria de redes.</p>
        <div class="cards">{cards}</div>
    </section>

    <section>
        <h2>2. Visualizacoes estaticas</h2>
        {figuras}
    </section>

    {bloco_aleatorios}
    {bloco_arestas}

    <section>
        <h2>3. Top 20 entidades por PageRank</h2>
        <p>O PageRank pondera centralidade pela importancia dos vizinhos. Entidades
        com PageRank alto sao hubs reconhecidos por outros hubs.</p>
        {tabela}
    </section>

    <section>
        <h2>4. Grafo interativo</h2>
        <p>Arraste, aproxime e clique nos nos. Cor por tipo de entidade,
        tamanho proporcional ao PageRank.</p>
        {bloco_iframe}
    </section>

    <section>
        <h2>5. Conclusoes</h2>
        {conclusoes}
    </section>
</main>
<footer>
    Lucas Augusto Spinola Pinto - UFRN - DCA3702 - 2026
</footer>
</body>
</html>
"""
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(html)
