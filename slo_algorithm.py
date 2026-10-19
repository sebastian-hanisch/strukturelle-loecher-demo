"""Kern: Maße für strukturelle Löcher (Burt), Überlappung der Kanten (Granovetter, Onnela u. a.), Brücken, Nähe, Betweenness, Rangstatistik und die Ausbreitung in diskreter Zeit.

Netze sind Nachbarlisten `adj`: Tupel von sortierten Tupeln, Knoten 0 bis n - 1, ungerichtet, ungewichtet, ohne Schleifen und Doppelkanten.
Alle Maße für Knoten ohne Kontakt (Grad 0) sind `nan`: sie haben keine Nachbarschaft, die man messen könnte."""

import math

import numpy as np

NAN = float("nan")


def degrees(adj):
    return [len(a) for a in adj]


# --- Burt: Constraint und effektive Größe -------------------------------------------------------------------------------------------------------------


def ego_terms(adj, i):
    """Rechenweg des Constraints von Knoten `i` (Burt 1992), ungewichtet: p_ij = 1 / Grad(i) für jeden Kontakt j.
    Je Kontakt j: (j, direkter Anteil p_ij, [(q, p_iq * p_qj) für jeden Kontakt q von i, der j kennt], Summe, Quadrat der Summe).
    Das Constraint ist die Summe der Quadrate über alle Kontakte; ein Knoten ohne Kontakt hat keinen Rechenweg (leere Liste)."""
    d = len(adj[i])
    if d == 0:
        return []
    nbr = [set(adj[q]) for q in adj[i]]
    p_i = 1.0 / d
    rows = []
    for j in adj[i]:
        indirect = []
        for q, nq in zip(adj[i], nbr):
            if q != j and j in nq:
                indirect.append((q, p_i * (1.0 / len(adj[q]))))      # p_qj = 1 / Grad(q), weil j ein Kontakt von q ist
        total = p_i + sum(t for _, t in indirect)
        rows.append((j, p_i, indirect, total, total * total))
    return rows


def constraint(adj):
    """Burt-Constraint je Knoten: Summe der Quadrate der (direkten plus indirekten) Anteile; `nan` ohne Kontakte. Kann über 1 liegen (Dreieck: 1,125)."""
    sets = [set(a) for a in adj]
    out = []
    for i, nb in enumerate(adj):
        d = len(nb)
        if d == 0:
            out.append(NAN)
            continue
        p_i = 1.0 / d
        tot = 0.0
        for j in nb:
            s = p_i
            for q in nb:
                if q != j and j in sets[q]:
                    s += p_i / len(adj[q])
            tot += s * s
        out.append(tot)
    return out


def triangles_at(adj, i):
    """Zahl der Kanten zwischen den Kontakten von `i` (= Dreiecke durch `i`)."""
    sets = {q: set(adj[q]) for q in adj[i]}
    return sum(1 for a in adj[i] for b in adj[i] if a < b and b in sets[a])


def effective_size(adj):
    """Effektive Größe (Burt, in der Fassung von Borgatti): Grad - 2t / Grad, t = Kanten zwischen den Kontakten; `nan` ohne Kontakte."""
    out = []
    for i, nb in enumerate(adj):
        d = len(nb)
        out.append(NAN if d == 0 else d - 2.0 * triangles_at(adj, i) / d)
    return out


def clustering(adj):
    """Lokaler Clustering-Koeffizient: Anteil der verbundenen Paare unter den Kontakten (Grad unter 2: 0, wie in networkx)."""
    out = []
    for i, nb in enumerate(adj):
        d = len(nb)
        out.append(0.0 if d < 2 else 2.0 * triangles_at(adj, i) / (d * (d - 1)))
    return out


def edge_overlap(adj, a, b):
    """Überlappung einer Kante (Onnela u. a.): gemeinsame Kontakte geteilt durch alle Kontakte beider Enden außer ihnen selbst; 0, wenn beide nur einander kennen."""
    common = len(set(adj[a]) & set(adj[b]))
    den = len(adj[a]) - 1 + len(adj[b]) - 1 - common
    return common / den if den > 0 else 0.0


def edges_of(adj):
    return [(a, b) for a in range(len(adj)) for b in adj[a] if a < b]


# --- Brücken, Abstände, Nähe, Betweenness -------------------------------------------------------------------------------------------------------------


def bridges(adj):
    """Brückenkanten (a < b) per iterativem Low-Link: die Baumkante (p, u) ist eine Brücke, wenn low[u] > disc[p]."""
    n = len(adj)
    disc, low, parent = [0] * n, [0] * n, [-1] * n
    pos = [0] * n
    clock = 0
    found = []
    for s in range(n):
        if disc[s]:
            continue
        clock += 1
        disc[s] = low[s] = clock
        stack = [s]
        while stack:
            u = stack[-1]
            if pos[u] < len(adj[u]):
                v = adj[u][pos[u]]
                pos[u] += 1
                if not disc[v]:
                    parent[v] = u
                    clock += 1
                    disc[v] = low[v] = clock
                    stack.append(v)
                elif v != parent[u]:
                    low[u] = min(low[u], disc[v])
            else:
                stack.pop()
                p = parent[u]
                if p != -1:
                    low[p] = min(low[p], low[u])
                    if low[u] > disc[p]:
                        found.append((min(p, u), max(p, u)))
    return sorted(found)


def bfs_distances(adj, s):
    dist = {s: 0}
    queue = [s]
    for u in queue:
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist


def closeness(adj):
    """Nähe nach der Fassung von Wasserman und Faust (wie `networkx.closeness_centrality`): (r - 1) / Summe der Abstände, mit (r - 1) / (n - 1) skaliert,
    wobei r die Zahl der erreichbaren Knoten einschließlich des Knotens selbst ist. Im zusammenhängenden Netz (n - 1) / Summe der Abstände."""
    n = len(adj)
    out = []
    for s in range(n):
        dist = bfs_distances(adj, s)
        total = sum(dist.values())
        r = len(dist)
        out.append(0.0 if total == 0 or n <= 1 else (r - 1) / total * (r - 1) / (n - 1))
    return out


def betweenness(adj):
    """Betweenness nach Brandes (2001), normiert wie `networkx.betweenness_centrality` (geteilt durch (n - 1)(n - 2))."""
    n = len(adj)
    cb = [0.0] * n
    for s in range(n):
        stack = []
        pred = [[] for _ in range(n)]
        sigma = [0.0] * n
        sigma[s] = 1.0
        dist = [-1] * n
        dist[s] = 0
        queue = [s]
        for v in queue:
            stack.append(v)
            for w in adj[v]:
                if dist[w] < 0:
                    dist[w] = dist[v] + 1
                    queue.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)
        delta = [0.0] * n
        while stack:
            w = stack.pop()
            for v in pred[w]:
                delta[v] += sigma[v] / sigma[w] * (1.0 + delta[w])
            if w != s:
                cb[w] += delta[w]
    scale = 1.0 / ((n - 1) * (n - 2)) if n > 2 else 1.0
    return [x * scale for x in cb]


def largest_component(adj):
    """(Nachbarliste der größten Komponente, neu nummeriert in aufsteigender alter Nummer; Liste der alten Nummern)."""
    n = len(adj)
    seen = [False] * n
    best = []
    for s in range(n):
        if seen[s]:
            continue
        comp = [s]
        seen[s] = True
        for u in comp:
            for v in adj[u]:
                if not seen[v]:
                    seen[v] = True
                    comp.append(v)
        if len(comp) > len(best):
            best = comp
    nodes = sorted(best)
    index = {old: new for new, old in enumerate(nodes)}
    return tuple(tuple(sorted(index[v] for v in adj[old])) for old in nodes), nodes


def mean_path_length(adj):
    """Mittlerer kürzester Abstand über alle erreichbaren Paare (ungeordnet); 0 ohne Paare."""
    total = 0
    pairs = 0
    for s in range(len(adj)):
        dist = bfs_distances(adj, s)
        total += sum(dist.values())
        pairs += len(dist) - 1
    return total / pairs if pairs else 0.0


# --- Rangstatistik --------------------------------------------------------------------------------------------------------------------------------------


def average_ranks(values):
    """Ränge 1 bis N, bei Gleichstand der Mittelwert der belegten Ränge. Werte werden auf 12 Stellen gerundet: Gleitkomma-Summen mathematisch gleicher Knoten unterscheiden sich um ~1e-16."""
    v = np.round(np.asarray(values, dtype=float), 12)
    order = np.argsort(v, kind="mergesort")
    ranks = np.empty(len(v), dtype=float)
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def pearson(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(a) < 2 or np.std(a) == 0 or np.std(b) == 0:
        return NAN
    return float(np.corrcoef(a, b)[0, 1])


def spearman(a, b):
    """Rangkorrelation (Pearson auf den Rängen mit Mittelwerten bei Gleichstand); `nan`, wenn ein Vektor konstant ist oder kürzer als 2."""
    if len(a) != len(b):
        raise ValueError("Vektoren ungleich lang")
    if len(a) < 2:
        return NAN
    return pearson(average_ranks(a), average_ranks(b))


def partial_spearman(a, b, control):
    """Partielle Rangkorrelation von a und b bei festgehaltenem `control`: (r_ab - r_ac r_bc) / sqrt((1 - r_ac^2)(1 - r_bc^2)); `nan`, wenn nicht definiert."""
    r_ab, r_ac, r_bc = spearman(a, b), spearman(a, control), spearman(b, control)
    if any(math.isnan(x) for x in (r_ab, r_ac, r_bc)):
        return NAN
    den = (1.0 - r_ac * r_ac) * (1.0 - r_bc * r_bc)
    if den <= 1e-12:
        return NAN
    return (r_ab - r_ac * r_bc) / math.sqrt(den)


def auc(pos, neg):
    """Wahrscheinlichkeit, dass ein zufälliges Positiv einen größeren Wert hat als ein zufälliges Negativ (Gleichstand zählt halb); `nan` ohne Paare."""
    pos = np.asarray(pos, dtype=float)
    neg = np.asarray(neg, dtype=float)
    if len(pos) == 0 or len(neg) == 0:
        return NAN
    ranks = average_ranks(np.concatenate([pos, neg]))
    return float((ranks[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg)))


def top_set(values, k, largest=True):
    """Die k besten Knoten (nan zählt nicht); bei Gleichstand gewinnt die kleinere Knotennummer. Zweiter Rückgabewert: Zahl der nicht gewählten Knoten, die mit dem
    k-ten Wert gleichauf liegen (größer als 0 heißt: die Auswahl hängt an der Gleichstandsregel)."""
    items = [(i, round(v, 12)) for i, v in enumerate(values) if not math.isnan(v)]      # Rundung: gleiche Werte müssen gleich sein, das Rauschen darf nicht entscheiden
    items.sort(key=lambda kv: (-kv[1] if largest else kv[1], kv[0]))
    chosen = {i for i, _ in items[:k]}
    if not items or k <= 0:
        return set(), 0
    edge = items[min(k, len(items)) - 1][1]
    return chosen, sum(1 for i, v in items if v == edge and i not in chosen)


def jaccard(a, b):
    return len(a & b) / len(a | b) if (a | b) else 1.0


def share_better(values, i, largest=True):
    """Anteil der Knoten (ohne nan), die einen echt besseren Wert haben als Knoten `i` (0 = bester, Gleichstand zählt nicht)."""
    valid = [round(v, 12) for v in values if not math.isnan(v)]
    if len(valid) < 2 or math.isnan(values[i]):
        return NAN
    ref = round(values[i], 12)
    better = sum(1 for v in valid if (v > ref if largest else v < ref))
    return better / (len(valid) - 1)


# --- Ausbreitung (SI in diskreter Zeit) -----------------------------------------------------------------------------------------------------------------


def arrival_times(adj, p, sources, runs, seed):
    """Mittlere Ankunftszeit je Knoten. Modell SI in diskreter Zeit: in jedem Schritt steckt jeder Infizierte jeden noch gesunden Kontakt mit Wahrscheinlichkeit p an.
    Gemittelt über alle Quellen und `runs` Läufe je Quelle, die Quelle selbst zählt in ihrem Lauf nicht; Knoten, die nie erreicht wurden: `nan`.
    p = 1 gibt den Breitensuche-Abstand, p = 0 nie eine Ankunft."""
    n = len(adj)
    src = np.array([a for a in range(n) for _ in adj[a]], dtype=int)
    dst = np.array([b for a in range(n) for b in adj[a]], dtype=int)
    rng = np.random.default_rng(int(seed))
    total = np.zeros(n)
    count = np.zeros(n)
    for s in sources:
        for _ in range(runs):
            infected = np.zeros(n, dtype=bool)
            infected[s] = True
            arrival = np.full(n, np.nan)
            t = 0
            while p > 0 and t < 10_000:
                idx = np.flatnonzero(infected[src] & ~infected[dst])
                if len(idx) == 0:
                    break
                hit = rng.random(len(idx)) < p
                t += 1
                new = np.unique(dst[idx[hit]])
                infected[new] = True
                arrival[new] = t
            reached = ~np.isnan(arrival)
            total[reached] += arrival[reached]
            count[reached] += 1
    out = np.full(n, np.nan)
    ok = count > 0
    out[ok] = total[ok] / count[ok]
    return [float(x) for x in out]
