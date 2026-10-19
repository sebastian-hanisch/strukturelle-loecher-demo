"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import math

import plotly.graph_objects as go

import slo_algorithm as A
import slo_constants as C
from slo_evaluation import de


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=340, bottom=10):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=bottom), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _name(inst, i):
    return inst.labels[i] if inst.labels else str(i)


def build_network(inst, values, mass, bridges, node, height=430):
    """Netz mit festen Positionen; Knoten nach `mass` gefärbt (Knoten ohne Wert grau), Brückenkanten orange, der gewählte Knoten rot umrandet. Gleicher Maßstab auf beiden Achsen."""
    n = inst.n
    xs, ys = [], []
    bridge_set = set(bridges)
    bx, by = [], []
    for a, b in A.edges_of(inst.adj):
        target = (bx, by) if (a, b) in bridge_set else (xs, ys)
        target[0].extend([inst.pos[a][0], inst.pos[b][0], None])
        target[1].extend([inst.pos[a][1], inst.pos[b][1], None])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_EDGE, width=0.7), hoverinfo="skip", showlegend=False))
    if bx:
        fig.add_trace(go.Scatter(x=bx, y=by, mode="lines", line=dict(color=C.COLOR_BRIDGE, width=2.4), hoverinfo="skip", name="Brückenkante"))
    ok = [i for i in range(n) if not math.isnan(values[i])]
    no = [i for i in range(n) if math.isnan(values[i])]
    size = 5 if n > 200 else 8
    if no:
        fig.add_trace(go.Scatter(x=[inst.pos[i][0] for i in no], y=[inst.pos[i][1] for i in no], mode="markers", marker=dict(size=size, color="rgba(150,150,150,0.8)"),
                                 hovertext=[f"Knoten {_name(inst, i)}: kein Wert (keine Kontakte)" for i in no], hoverinfo="text", name="ohne Wert"))
    fig.add_trace(go.Scatter(x=[inst.pos[i][0] for i in ok], y=[inst.pos[i][1] for i in ok], mode="markers",
                             marker=dict(size=size, color=[values[i] for i in ok], colorscale=C.SCALE_CONSTRAINT, reversescale=(mass == C.M_CONSTRAINT), showscale=True,
                                         colorbar=dict(title=dict(text=mass), thickness=12, len=0.8), line=dict(color="rgba(40,40,40,0.45)", width=0.4)),
                             hovertext=[f"Knoten {_name(inst, i)}: {mass} {de(values[i], 3)}" for i in ok], hoverinfo="text", showlegend=False))
    x, y = inst.pos[node]
    fig.add_trace(go.Scatter(x=[x], y=[y], mode="markers", marker=dict(size=size + 9, color="rgba(0,0,0,0)", line=dict(color=C.COLOR_SELECT, width=2.5)), hoverinfo="skip", name="gewählter Knoten"))
    fig.add_trace(go.Scatter(x=[-0.04, 1.04], y=[-0.04, 1.04], mode="markers", marker=dict(size=1, color="rgba(0,0,0,0)"), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, autorange=True)
    fig.update_yaxes(visible=False, autorange=True, scaleanchor="x", scaleratio=1)
    return _base(fig, height=height, bottom=30)


def build_ego(inst, node, terms, height=440):
    """Ego-Netz des gewählten Knotens: in der Mitte der Knoten, ringsum seine Kontakte (Farbe = Beitrag zum Constraint), Linien zwischen den Kontakten sind die Dreiecke."""
    adj = inst.adj
    alters = list(adj[node])
    k = len(alters)
    fig = go.Figure()
    if k == 0:
        fig.add_annotation(text="Der Knoten hat keine Kontakte.", showarrow=False, x=0.5, y=0.5)
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        return _base(fig, height=200)
    pos = {a: (math.cos(2 * math.pi * i / k + math.pi / 2), math.sin(2 * math.pi * i / k + math.pi / 2)) for i, a in enumerate(alters)}
    spokes_x, spokes_y, ties_x, ties_y = [], [], [], []
    for a in alters:
        spokes_x += [0.0, pos[a][0], None]
        spokes_y += [0.0, pos[a][1], None]
    for i, a in enumerate(alters):
        for b in alters[i + 1:]:
            if b in adj[a]:
                ties_x += [pos[a][0], pos[b][0], None]
                ties_y += [pos[a][1], pos[b][1], None]
    fig.add_trace(go.Scatter(x=spokes_x, y=spokes_y, mode="lines", line=dict(color="rgba(120,120,120,0.45)", width=1), hoverinfo="skip", name="Kontakt des Knotens"))
    if ties_x:
        fig.add_trace(go.Scatter(x=ties_x, y=ties_y, mode="lines", line=dict(color=C.COLOR_A, width=2), hoverinfo="skip", name="Kontakte untereinander verbunden"))
    square = {row[0]: row[4] for row in terms}
    fig.add_trace(go.Scatter(x=[pos[a][0] for a in alters], y=[pos[a][1] for a in alters], mode="markers+text", text=[_name(inst, a) for a in alters], textposition="top center",
                             marker=dict(size=16, color=[square[a] for a in alters], colorscale=C.SCALE_CONSTRAINT, showscale=True, colorbar=dict(title=dict(text="Beitrag"), thickness=10, len=0.6),
                                         line=dict(color="rgba(40,40,40,0.6)", width=0.6)),
                             hovertext=[f"Kontakt {_name(inst, a)}: Beitrag {de(square[a], 3)}, Grad {len(adj[a])}" for a in alters], hoverinfo="text", showlegend=False))
    fig.add_trace(go.Scatter(x=[0.0], y=[0.0], mode="markers+text", text=[_name(inst, node)], textposition="middle center", marker=dict(size=26, color=C.COLOR_SELECT), textfont=dict(color="white"),
                             hoverinfo="skip", name="gewählter Knoten"))
    fig.update_xaxes(visible=False, range=[-1.45, 1.45])
    fig.update_yaxes(visible=False, range=[-1.45, 1.45], scaleanchor="x", scaleratio=1)
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.02, font=dict(size=11)), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_profile(profile):
    """Wo steht der Knoten unter allen? Anteil der Knoten mit besserem Wert je Maß (0 = bester; beim Constraint zählt klein als besser)."""
    rows = [r for r in profile if not math.isnan(r[2])]
    fig = go.Figure(go.Bar(y=[r[0] for r in rows], x=[100 * r[2] for r in rows], orientation="h", marker_color=C.COLOR_LINE,
                           text=[f"{de(r[1], 3)}  (besser: {de(100 * r[2], 0)} %)" for r in rows], textposition="auto"))
    fig.update_xaxes(title_text="Anteil der Knoten mit besserem Wert in % (0 = bester)", range=[0, 100])
    fig.update_yaxes(autorange="reversed")
    return _base(fig, height=260, bottom=40)


def _bars(rows, series, ytitle, rng=(-1.3, 1.2), height=340, label_key="typ", bottom=90):
    fig = go.Figure()
    for key, name, color in series:
        ys = [None if (r[key] is None or (isinstance(r[key], float) and math.isnan(r[key]))) else r[key] for r in rows]
        fig.add_trace(go.Bar(x=[r[label_key] for r in rows], y=ys, name=name, marker_color=color,
                             text=[de(v, 2) if v is not None else "" for v in ys], textposition="outside", hovertemplate="%{x}: %{y:.2f}<extra>" + name + "</extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text=ytitle, range=list(rng))
    fig.update_xaxes(tickangle=-25)
    return _base(fig, height=height, bottom=bottom)


def build_degree(rows):
    """Rangkorrelation des Constraints mit dem Grad, der effektiven Größe und (bei festem Grad) dem Clustering je Netztyp."""
    return _bars(rows, [("c_deg", "Constraint ~ Grad", C.COLOR_A), ("c_eff", "Constraint ~ effektive Größe", C.COLOR_LINE), ("c_clu_deg", "Constraint ~ Clustering (Grad fest)", C.COLOR_B)],
                 "Rangkorrelation", height=380)


def build_broker(rows):
    """Überlappung (Jaccard) der Top-5-%-Mengen je Netztyp."""
    return _bars(rows, [("j_cd", "niedriges Constraint ~ hoher Grad", C.COLOR_A), ("j_cb", "niedriges Constraint ~ hohe Betweenness", C.COLOR_B), ("j_ed", "hohe eff. Größe ~ hoher Grad", C.COLOR_LINE)],
                 "Überlappung (Jaccard)", rng=(0, 1.15), height=380)


def build_granovetter(rows):
    """Anteil der Kanten ohne gemeinsamen Nachbarn innerhalb und zwischen den Verbünden und die Güte (AUC) von „keine gemeinsamen Nachbarn sagt: zwischen“."""
    xs = [f"c = {r['c']}" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[r["zero_inner"] for r in rows], name="Kanten innerhalb ohne gemeinsamen Nachbarn", marker_color=C.COLOR_A,
                         text=[de(r["zero_inner"], 2) for r in rows], textposition="outside"))
    fig.add_trace(go.Bar(x=xs, y=[r["zero_between"] for r in rows], name="Kanten zwischen den Verbünden ohne gemeinsamen Nachbarn", marker_color=C.COLOR_B,
                         text=[de(r["zero_between"], 2) for r in rows], textposition="outside"))
    fig.add_trace(go.Scatter(x=xs, y=[r["auc"] for r in rows], mode="lines+markers+text", name="Güte (AUC)", line=dict(color=C.COLOR_C, width=3),
                             text=[de(r["auc"], 2) for r in rows], textposition="top center"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Anteil bzw. AUC", range=[0, 1.2])
    return _base(fig, height=340, bottom=70)


def build_watts(rows):
    """Watts und Strogatz: Pfadlänge und Clustering, jeweils geteilt durch den Wert des regelmäßigen Rings (β = 0), dazu der Anteil der Abkürzungen ohne gemeinsamen Nachbarn."""
    base = rows[0]
    xs = [f"β = {de(r['beta'], 2)}" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[r["path"] / base["path"] if base["path"] else None for r in rows], mode="lines+markers", name="Pfadlänge / Pfadlänge bei β = 0", line=dict(color=C.COLOR_B, width=3)))
    fig.add_trace(go.Scatter(x=xs, y=[r["clustering"] / base["clustering"] if base["clustering"] else None for r in rows], mode="lines+markers", name="Clustering / Clustering bei β = 0", line=dict(color=C.COLOR_A, width=3)))
    fig.add_trace(go.Scatter(x=xs, y=[r["zero"] for r in rows], mode="lines+markers", name="Anteil Kanten ohne gemeinsamen Nachbarn", line=dict(color=C.COLOR_C, width=2, dash="dot")))
    fig.update_yaxes(title_text="Verhältnis bzw. Anteil", range=[0, 1.08])
    return _base(fig, height=340, bottom=60)


def build_arrival(rows):
    """Betrag der Rangkorrelation der Ankunftszeit mit Constraint, Grad, Nähe und effektiver Größe je Netztyp (kleine Ankunftszeit = früher)."""
    abs_rows = [{"typ": r["typ"], **{k: abs(r[k]) if not math.isnan(r[k]) else float("nan") for k in ("t_c", "t_d", "t_l", "t_e")}} for r in rows]
    return _bars(abs_rows, [("t_c", "Constraint", C.COLOR_A), ("t_d", "Grad", C.COLOR_LINE), ("t_l", "Nähe", C.COLOR_B), ("t_e", "effektive Größe", C.COLOR_C)],
                 "Betrag der Rangkorrelation mit der Ankunftszeit", rng=(0, 1.15), height=380)


def build_diversity(stats):
    """Rangkorrelationen von Vielfalt (Zahl der Verbünde bzw. Entropie unter den Kontakten) mit effektiver Größe, Constraint und Grad."""
    labels = [("div_eff", "Zahl ~ eff. Größe"), ("div_cons", "Zahl ~ Constraint"), ("div_deg", "Zahl ~ Grad"), ("ent_eff", "Entropie ~ eff. Größe"),
              ("ent_cons", "Entropie ~ Constraint"), ("ent_deg", "Entropie ~ Grad"), ("ent_cons_deg", "Entropie ~ Constraint (Grad fest)")]
    ys = [None if math.isnan(stats[k]) else stats[k] for k, _ in labels]
    fig = go.Figure(go.Bar(x=[name for _, name in labels], y=ys, marker_color=[C.COLOR_A if k == "ent_cons_deg" else C.COLOR_LINE for k, _ in labels],
                           text=[de(v, 2) if v is not None else "" for v in ys], textposition="outside"))
    fig.update_yaxes(title_text="Rangkorrelation", range=[-1.3, 1.2])
    fig.update_xaxes(tickangle=-25)
    return _base(fig, height=360, bottom=100)
