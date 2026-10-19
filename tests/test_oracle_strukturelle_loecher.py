"""Orakel-Test strukturelle-loecher-demo: die Eigenbauten gegen einen anderen Rechenweg (networkx, scipy, Aufzählung, Mengenformel).

Orakel je Einheit (ORACLE-PLAYBOOK §2): Constraint, effektive Größe, Clustering, Nähe, Betweenness und Brücken gegen `networkx` auf 120 festen Zufallsnetzen
(auch mit isolierten Knoten und mehreren Komponenten); die Überlappung der Kanten gegen die Mengenformel |N(a) ∪ N(b) ohne a und b|; Spearman gegen
`scipy.stats.spearmanr` (mit Gleichständen); AUC gegen die Aufzählung aller Paare; die Ausbreitung bei p = 1 gegen den Breitensuche-Abstand von networkx.
Gelaufen sind vorab 300 Zufallsnetze im Scratch-Ordner; im Repo stehen 120 feste Netze unter 10 Sekunden."""

import itertools
import math

import numpy as np
import pytest

import slo_algorithm as A
import slo_constants as C
import slo_scenario as S
from conftest import make_adj

nx = pytest.importorskip("networkx")


def _graph(adj):
    g = nx.Graph()
    g.add_nodes_from(range(len(adj)))
    g.add_edges_from(A.edges_of(adj))
    return g


def _random_adj(seed):
    rng = np.random.default_rng(seed)
    n = int(rng.integers(4, 26))
    p = float(rng.uniform(0.05, 0.6))
    pairs = [(a, b) for a in range(n) for b in range(a + 1, n) if rng.random() < p]
    return make_adj(n, pairs)


SEEDS = range(120)


def _same(a, b, tol=1e-9):
    assert len(a) == len(b)
    for x, y in zip(a, b):
        assert (math.isnan(x) and math.isnan(y)) or abs(x - y) < tol, (x, y)


@pytest.mark.parametrize("seed", SEEDS)
def test_burt_measures_and_clustering_match_networkx(seed):
    adj = _random_adj(seed)
    g = _graph(adj)
    isolated = [v for v in g if g.degree(v) == 0]
    g2 = g.copy()
    g2.remove_nodes_from(isolated)                                  # networkx.constraint rechnet nur mit Kontakten; Isolierte sind bei uns nan
    if g2.number_of_nodes() == 0:
        pytest.skip("kein Knoten mit Kontakt")
    nc, ne = nx.constraint(g2), nx.effective_size(g2)
    mine_c, mine_e = A.constraint(adj), A.effective_size(adj)
    for v in g2:
        assert mine_c[v] == pytest.approx(nc[v], abs=1e-9) and mine_e[v] == pytest.approx(ne[v], abs=1e-9)
    assert all(math.isnan(mine_c[v]) and math.isnan(mine_e[v]) for v in isolated)
    nclu = nx.clustering(g)
    _same(A.clustering(adj), [nclu[v] for v in range(len(adj))])


@pytest.mark.parametrize("seed", SEEDS)
def test_closeness_betweenness_and_bridges_match_networkx(seed):
    adj = _random_adj(seed)
    g = _graph(adj)
    nclo, nbet = nx.closeness_centrality(g), nx.betweenness_centrality(g)
    _same(A.closeness(adj), [nclo[v] for v in range(len(adj))])
    _same(A.betweenness(adj), [nbet[v] for v in range(len(adj))])
    assert A.bridges(adj) == sorted((min(a, b), max(a, b)) for a, b in nx.bridges(g))


@pytest.mark.parametrize("seed", SEEDS)
def test_edge_overlap_matches_the_set_formula(seed):
    adj = _random_adj(seed)
    for a, b in A.edges_of(adj):
        union = (set(adj[a]) | set(adj[b])) - {a, b}
        common = set(adj[a]) & set(adj[b])
        expected = len(common) / len(union) if union else 0.0
        assert A.edge_overlap(adj, a, b) == pytest.approx(expected)


@pytest.mark.parametrize("typ", C.GENERATED_TYPES)
def test_measures_match_networkx_on_every_generated_type(typ):
    inst = S.make_instance(typ, 80, 6, 11, layout=False)
    g = _graph(inst.adj)
    g.remove_nodes_from([v for v in list(g) if g.degree(v) == 0])
    nc = nx.constraint(g)
    mine = A.constraint(inst.adj)
    assert all(mine[v] == pytest.approx(nc[v], abs=1e-9) for v in g)


def test_largest_component_and_mean_path_length_match_networkx():
    for seed in range(40):
        adj = _random_adj(seed)
        sub, nodes = A.largest_component(adj)
        g = _graph(adj)
        biggest = max(nx.connected_components(g), key=len)
        assert set(nodes) == set(biggest) or len(biggest) == len(nodes)           # bei gleich großen Komponenten kann die andere gewinnen
        if len(nodes) > 1:
            h = _graph(sub)
            assert nx.is_connected(h) and A.mean_path_length(sub) == pytest.approx(nx.average_shortest_path_length(h))


def test_spearman_matches_scipy_with_ties():
    stats = pytest.importorskip("scipy.stats")
    rng = np.random.default_rng(5)
    for _ in range(60):
        n = int(rng.integers(3, 40))
        a = rng.integers(0, 6, size=n).astype(float)               # viele Gleichstände
        b = rng.integers(0, 6, size=n).astype(float)
        ref = stats.spearmanr(a, b)[0]
        mine = A.spearman(a, b)
        assert (math.isnan(ref) and math.isnan(mine)) or mine == pytest.approx(ref, abs=1e-9)


def test_auc_matches_the_enumeration_of_all_pairs():
    rng = np.random.default_rng(6)
    for _ in range(60):
        pos = rng.integers(0, 8, size=int(rng.integers(1, 12))).tolist()
        neg = rng.integers(0, 8, size=int(rng.integers(1, 12))).tolist()
        wins = sum(1.0 if p > q else 0.5 if p == q else 0.0 for p, q in itertools.product(pos, neg))
        assert A.auc(pos, neg) == pytest.approx(wins / (len(pos) * len(neg)))


def test_arrival_at_p_one_equals_the_networkx_distance():
    for seed in range(30):
        adj = _random_adj(seed)
        g = _graph(adj)
        sub, nodes = A.largest_component(adj)
        if len(nodes) < 2:
            continue
        source = nodes[0]
        t = A.arrival_times(adj, 1.0, [source], 1, seed)
        dist = nx.single_source_shortest_path_length(g, source)
        for v in range(len(adj)):
            if v == source or v not in dist:
                assert math.isnan(t[v])
            else:
                assert t[v] == dist[v]
