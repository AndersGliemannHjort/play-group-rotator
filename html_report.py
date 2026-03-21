"""Interactive HTML report with Plotly charts for play group rotations."""

import json
from itertools import combinations


def generate_html_report(children, new_iterations, filepath, past_count=0):
    """Build a self-contained HTML file with interactive Plotly charts."""
    total = past_count + len(new_iterations)
    names = sorted(c.name for c in children)
    name_idx = {n: i for i, n in enumerate(names)}

    meeting_matrix = _build_meeting_matrix(children, names)
    hosting_data = _build_hosting_data(children, names)
    hosting_timeline = _build_hosting_timeline(children, names)
    gap_data = _build_gap_distribution(children)
    coverage_data = _build_coverage_data(children, names)
    iteration_groups = _build_iteration_groups(new_iterations, past_count)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Play Group Rotations &mdash; {total} iterations</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root {{
    --bg: #0f1117;
    --card: #1a1d27;
    --border: #2a2d3a;
    --text: #e0e0e6;
    --muted: #8b8fa3;
    --accent: #6c72cb;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    padding: 2rem;
  }}
  h1 {{
    font-size: 1.8rem;
    font-weight: 600;
    margin-bottom: .25rem;
  }}
  .subtitle {{
    color: var(--muted);
    margin-bottom: 2rem;
    font-size: .95rem;
  }}
  .chart-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
  }}
  .chart-card h2 {{
    font-size: 1.1rem;
    font-weight: 500;
    margin-bottom: 1rem;
    color: var(--text);
  }}
  .grid-2 {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }}
  @media (max-width: 1000px) {{
    .grid-2 {{ grid-template-columns: 1fr; }}
  }}
  .plot {{ width: 100%; }}
</style>
</head>
<body>

<h1>Play Group Rotations</h1>
<p class="subtitle">
  {past_count} past + {len(new_iterations)} new = {total} total iterations
  &middot; {len(children)} children
</p>

<div class="chart-card">
  <h2>Meeting Heatmap &mdash; pairwise meeting counts</h2>
  <div id="heatmap" class="plot"></div>
</div>

<div class="grid-2">
  <div class="chart-card">
    <h2>Hosting counts per child</h2>
    <div id="hosting" class="plot"></div>
  </div>
  <div class="chart-card">
    <h2>Unique peers met (of {len(children) - 1})</h2>
    <div id="coverage" class="plot"></div>
  </div>
</div>

<div class="grid-2">
  <div class="chart-card">
    <h2>Average meeting gap (per pair)</h2>
    <p style="color:var(--muted);font-size:.85rem;margin-bottom:.75rem;">
      For every pair that met 2+ times: mean iterations between consecutive
      meetings. Lower = they tend to meet again sooner overall.
    </p>
    <div id="gaps" class="plot"></div>
  </div>
  <div class="chart-card">
    <h2>Hosting timeline</h2>
    <p style="color:var(--muted);font-size:.85rem;margin-bottom:.75rem;">
      Each dot marks an iteration where the child hosted a group.
    </p>
    <div id="timeline" class="plot"></div>
  </div>
</div>

<div class="chart-card">
  <h2>Group composition by iteration</h2>
  <p style="color:var(--muted);font-size:.85rem;margin-bottom:.75rem;">
    Each row is a child, each column an iteration.
    Colour encodes which of the 6 groups the child was in.
    Hover for group members.
  </p>
  <div id="groupmap" class="plot"></div>
</div>

<script>
const PLOTLY_LAYOUT_DEFAULTS = {{
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  font: {{ color: '#e0e0e6', family: 'Segoe UI, system-ui, sans-serif', size: 12 }},
  margin: {{ l: 110, r: 30, t: 30, b: 60 }},
}};

/* ---- Heatmap ---- */
(function() {{
  const names = {json.dumps(names)};
  const z = {json.dumps(meeting_matrix)};
  Plotly.newPlot('heatmap', [{{
    z: z,
    x: names,
    y: names,
    type: 'heatmap',
    colorscale: [
      [0, '#1a1d27'],
      [0.2, '#2d3561'],
      [0.4, '#6c72cb'],
      [0.7, '#c0a6f0'],
      [1, '#f0e6ff']
    ],
    hovertemplate: '%{{x}} & %{{y}}: %{{z}} meetings<extra></extra>',
    colorbar: {{ title: {{ text: 'Meetings', side: 'right' }}, tickcolor: '#e0e0e6' }},
  }}], {{
    ...PLOTLY_LAYOUT_DEFAULTS,
    height: 650,
    xaxis: {{ tickangle: -45, side: 'bottom' }},
    yaxis: {{ autorange: 'reversed' }},
  }}, {{ responsive: true }});
}})();

/* ---- Hosting bar chart ---- */
(function() {{
  const d = {json.dumps(hosting_data)};
  const sorted = d.names.map((n, i) => ({{ name: n, count: d.counts[i] }}))
    .sort((a, b) => a.count - b.count);
  Plotly.newPlot('hosting', [{{
    y: sorted.map(d => d.name),
    x: sorted.map(d => d.count),
    type: 'bar',
    orientation: 'h',
    marker: {{ color: '#6c72cb' }},
    hovertemplate: '%{{y}}: %{{x}} times hosted<extra></extra>',
  }}], {{
    ...PLOTLY_LAYOUT_DEFAULTS,
    height: 550,
    xaxis: {{ title: 'Times hosted', dtick: 1 }},
    yaxis: {{ automargin: true }},
  }}, {{ responsive: true }});
}})();

/* ---- Coverage bar chart ---- */
(function() {{
  const d = {json.dumps(coverage_data)};
  const sorted = d.names.map((n, i) => ({{ name: n, count: d.counts[i] }}))
    .sort((a, b) => a.count - b.count);
  Plotly.newPlot('coverage', [{{
    y: sorted.map(d => d.name),
    x: sorted.map(d => d.count),
    type: 'bar',
    orientation: 'h',
    marker: {{ color: '#4ecca3' }},
    hovertemplate: '%{{y}}: met %{{x}} peers<extra></extra>',
  }}], {{
    ...PLOTLY_LAYOUT_DEFAULTS,
    height: 550,
    xaxis: {{ title: 'Unique peers met', dtick: 1 }},
    yaxis: {{ automargin: true }},
  }}, {{ responsive: true }});
}})();

/* ---- Gap histogram ---- */
(function() {{
  const gaps = {json.dumps(gap_data)};
  Plotly.newPlot('gaps', [{{
    x: gaps,
    type: 'histogram',
    marker: {{ color: '#e8a87c' }},
    nbinsx: 28,
    hovertemplate: 'Avg gap ~%{{x}}: %{{y}} pairs<extra></extra>',
  }}], {{
    ...PLOTLY_LAYOUT_DEFAULTS,
    height: 350,
    xaxis: {{ title: 'Avg iterations between re-meetings (per pair)' }},
    yaxis: {{ title: 'Number of pairs' }},
    bargap: 0.1,
  }}, {{ responsive: true }});
}})();

/* ---- Hosting timeline ---- */
(function() {{
  const d = {json.dumps(hosting_timeline)};
  Plotly.newPlot('timeline', [{{
    x: d.iterations,
    y: d.names,
    mode: 'markers',
    type: 'scatter',
    marker: {{ color: '#6c72cb', size: 8, symbol: 'circle' }},
    hovertemplate: '%{{y}} hosted in iteration %{{x}}<extra></extra>',
  }}], {{
    ...PLOTLY_LAYOUT_DEFAULTS,
    height: 550,
    xaxis: {{ title: 'Iteration', dtick: 1 }},
    yaxis: {{ automargin: true }},
  }}, {{ responsive: true }});
}})();

/* ---- Group composition heatmap ---- */
(function() {{
  const d = {json.dumps(iteration_groups)};
  const names = d.names;
  const iters = d.iterations;
  const z = d.z;
  const text = d.text;

  const colorscale = [
    [0, '#3b528b'],
    [0.2, '#21918c'],
    [0.4, '#5ec962'],
    [0.6, '#fde725'],
    [0.8, '#e8a87c'],
    [1.0, '#d44d5c'],
  ];

  Plotly.newPlot('groupmap', [{{
    z: z,
    x: iters,
    y: names,
    text: text,
    type: 'heatmap',
    colorscale: colorscale,
    showscale: false,
    hovertemplate: '%{{y}}, iteration %{{x}}<br>%{{text}}<extra></extra>',
    zmin: 0,
    zmax: 5,
  }}], {{
    ...PLOTLY_LAYOUT_DEFAULTS,
    height: 650,
    xaxis: {{ title: 'Iteration', dtick: 1 }},
    yaxis: {{ autorange: 'reversed', automargin: true }},
  }}, {{ responsive: true }});
}})();
</script>
</body>
</html>"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML report written: {filepath}")


def _build_meeting_matrix(children, names):
    """24×24 symmetric matrix of pairwise meeting counts."""
    n = len(names)
    idx = {name: i for i, name in enumerate(names)}
    matrix = [[0] * n for _ in range(n)]
    for c in children:
        i = idx[c.name]
        for other, cnt in c.meetings.items():
            j = idx[other]
            matrix[i][j] = cnt
    return matrix


def _build_hosting_data(children, names):
    counts = [next(c.hosting_count for c in children if c.name == n) for n in names]
    return {"names": names, "counts": counts}


def _build_hosting_timeline(children, names):
    xs, ys = [], []
    for c in children:
        for it in c.hosting_iterations:
            xs.append(it)
            ys.append(c.name)
    return {"iterations": xs, "names": ys}


def _build_gap_distribution(children):
    """Per-pair mean iterations between consecutive meetings (2+ meetings)."""
    gaps = []
    seen = set()
    for c in children:
        for other, iters in c.meeting_iterations.items():
            pair = tuple(sorted([c.name, other]))
            if pair in seen or len(iters) < 2:
                continue
            seen.add(pair)
            s = sorted(iters)
            glist = [s[i] - s[i - 1] - 1 for i in range(1, len(s))]
            gaps.append(sum(glist) / len(glist))
    return gaps


def _build_coverage_data(children, names):
    counts = [len(next(c for c in children if c.name == n).meetings) for n in names]
    return {"names": names, "counts": counts}


def _build_iteration_groups(new_iterations, past_count):
    """Build a child×iteration matrix where value = group index (0-5)."""
    names_set = set()
    for groups in new_iterations:
        for g in groups:
            for c in g.children:
                names_set.add(c.name)
    names = sorted(names_set)
    name_idx = {n: i for i, n in enumerate(names)}

    n_children = len(names)
    n_iters = len(new_iterations)
    z = [[None] * n_iters for _ in range(n_children)]
    text = [[""] * n_iters for _ in range(n_children)]

    for col, groups in enumerate(new_iterations):
        iter_num = past_count + col + 1
        for g_idx, group in enumerate(groups):
            members = ", ".join(c.name for c in group.children)
            host = group.host.name if group.host else ""
            label = f"Group {g_idx + 1}: {members} (host: {host})"
            for c in group.children:
                row = name_idx[c.name]
                z[row][col] = g_idx
                text[row][col] = label

    iterations = [past_count + i + 1 for i in range(n_iters)]
    return {"names": names, "iterations": iterations, "z": z, "text": text}
