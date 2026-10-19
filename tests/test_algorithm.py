"""Einheiten des Kerns an Mini-Instanzen mit von Hand gerechneten Werten (DEMO-PLAYBOOK §1b)."""

import math
from fractions import Fraction as F

import numpy as np
import pytest

import slo_algorithm as A
import slo_scenario as S
from conftest import make_adj


def test_constraint_hand_values(star3, triangle, path3, d3t1):
    c = A.constraint(star3)
    assert c[0] == pytest.approx(1 / 3) and c[1] == pytest.approx(1.0)
    assert A.constraint(triangle) == pytest.approx([1.125] * 3)                       # Constraint kann über 1 liegen
    assert A.constraint(path3) == pytest.approx([1.0, 0.5, 1.0])
    assert A.constraint(d3t1)[0] == pytest.approx(11 / 18)


def test_constraint_of_a_complete_graph_follows_the_closed_form():
    for d in range(3, 9):
        k = make_adj(d, [(a, b) for a in range(d) for b in range(a + 1, d)])
        expected = (d - 1) * (1 / (d - 1) + (d - 2) / (d - 1) ** 2) ** 2
        assert A.constraint(k) == pytest.approx([expected] * d)
    assert A.constraint(make_adj(5, [(a, b) for a in range(5) for b in range(a + 1, 5)]))[0] == pytest.approx(0.765625)


def test_effective_size_and_clustering_hand_values(star3, triangle, path3, d3t1):
    assert A.effective_size(star3) == pytest.approx([3.0, 1.0, 1.0, 1.0])
    assert A.effective_size(triangle) == pytest.approx([1.0] * 3)
    assert A.effective_size(path3) == pytest.approx([1.0, 2.0, 1.0])
    assert A.effective_size(d3t1)[0] == pytest.approx(3 - 2 * 1 / 3)
    assert A.clustering(triangle) == [1.0] * 3 and A.clustering(star3)[0] == 0.0 and A.clustering(path3)[1] == 0.0
    assert A.clustering(d3t1)[0] == pytest.approx(1 / 3)
    assert A.triangles_at(d3t1, 0) == 1 and A.triangles_at(d3t1, 3) == 0


def test_a_broker_between_r_cliques_has_constraint_one_over_r():
    for r in (2, 3, 4, 6):
        pairs, broker = [], 4 * r
        for b in range(r):
            pairs += [(4 * b + i, 4 * b + j) for i in range(4) for j in range(i + 1, 4)] + [(broker, 4 * b)]
        adj = make_adj(4 * r + 1, pairs)
        assert A.constraint(adj)[broker] == pytest.approx(1 / r) and A.effective_size(adj)[broker] == pytest.approx(r)


def test_nodes_without_contacts_are_nan():
    adj = make_adj(3, [(0, 1)])
    assert math.isnan(A.constraint(adj)[2]) and math.isnan(A.effective_size(adj)[2])
    assert A.clustering(adj)[2] == 0.0 and A.ego_terms(adj, 2) == []


def test_ego_terms_sum_to_the_constraint(d3t1):
    rows = A.ego_terms(d3t1, 0)
    assert [r[0] for r in rows] == [1, 2, 3]
    j, direct, indirect, total, square = rows[0]
    assert direct == pytest.approx(1 / 3) and indirect == [(2, pytest.approx(1 / 6))] and total == pytest.approx(1 / 2) and square == pytest.approx(1 / 4)
    assert rows[2][2] == [] and rows[2][4] == pytest.approx(1 / 9)
    assert sum(r[4] for r in rows) == pytest.approx(A.constraint(d3t1)[0])


def test_the_constraint_depends_on_the_degree_of_the_triangle_neighbour_only():
    triangle_nb = make_adj(7, [(0, 1), (0, 2), (0, 3), (1, 2), (1, 4), (1, 5), (1, 6)])       # Dreiecks-Nachbar 1 mit drei weiteren Kontakten
    outside_nb = make_adj(7, [(0, 1), (0, 2), (0, 3), (1, 2), (3, 4), (3, 5), (3, 6)])        # Nachbar 3 außerhalb des Dreiecks mit drei weiteren Kontakten
    # Handrechnung: j = 1: 1/3 + 1/3 · 1/2 = 1/2; j = 2: 1/3 + 1/3 · 1/5 = 2/5; j = 3: 1/3 → 1/4 + 4/25 + 1/9
    assert A.constraint(triangle_nb)[0] == pytest.approx(1 / 4 + 4 / 25 + 1 / 9)
    assert A.constraint(outside_nb)[0] == pytest.approx(11 / 18)


def test_the_broker_example_by_exact_fractions():
    adj = S.broker_instance().adj
    assert S.BROKER_N == 19 and len(adj[S.BROKER_MAKLER]) == 3 and len(adj[S.BROKER_HUB]) == 7
    c = A.constraint(adj)
    assert c[S.BROKER_MAKLER] == pytest.approx(1 / 3) and A.effective_size(adj)[S.BROKER_MAKLER] == pytest.approx(3.0)
    hub = F(1, 16) + 3 * F(289, 4900) + 3 * F(1, 49)           # Handrechnung: Mitglied 0 (Grad 5): 1/4; Mitglieder 1 bis 3: (1/7 + 1/10)²; Blätter (1/7)²
    assert c[S.BROKER_HUB] == pytest.approx(float(hub))
    assert A.effective_size(adj)[S.BROKER_HUB] == pytest.approx(37 / 7)        # 7 - 2 · 6 / 7
    assert c[S.BROKER_HUB] < c[S.BROKER_MAKLER]                                  # der Hub mit Blättern hat das kleinere Constraint: Blätter zählen als Löcher


def test_edge_overlap_hand_values():
    adj = make_adj(5, [(0, 1), (0, 2), (1, 2), (1, 3), (3, 4)])
    assert A.edge_overlap(adj, 0, 1) == pytest.approx(1 / 2)         # gemeinsam {2}; Kontakte beider Enden ohne sie selbst: {2, 3}
    assert A.edge_overlap(adj, 3, 4) == 0.0 and A.edge_overlap(adj, 1, 3) == 0.0
    assert A.edge_overlap(make_adj(2, [(0, 1)]), 0, 1) == 0.0       # beide kennen nur einander
    k4 = make_adj(4, [(a, b) for a in range(4) for b in range(a + 1, 4)])
    assert A.edge_overlap(k4, 0, 1) == pytest.approx(1.0)


def test_bridges_hand_values():
    path = make_adj(4, [(0, 1), (1, 2), (2, 3)])
    assert A.bridges(path) == [(0, 1), (1, 2), (2, 3)]
    cycle = make_adj(4, [(0, 1), (1, 2), (2, 3), (3, 0)])
    assert A.bridges(cycle) == []
    two = make_adj(6, [(0, 1), (0, 2), (1, 2), (3, 4), (3, 5), (4, 5), (2, 3)])
    assert A.bridges(two) == [(2, 3)]
    assert A.bridges(make_adj(3, [])) == []


def test_closeness_and_betweenness_hand_values(star3, path3):
    assert A.closeness(path3) == pytest.approx([2 / 3, 1.0, 2 / 3])
    assert A.closeness(make_adj(3, [(0, 1)]))[2] == 0.0
    assert A.betweenness(star3) == pytest.approx([1.0, 0.0, 0.0, 0.0])
    assert A.betweenness(path3) == pytest.approx([0.0, 1.0, 0.0])
    assert A.betweenness(make_adj(2, [(0, 1)])) == [0.0, 0.0]


def test_largest_component_relabels_in_ascending_order():
    adj = make_adj(6, [(0, 3), (3, 5), (1, 2)])
    sub, nodes = A.largest_component(adj)
    assert nodes == [0, 3, 5] and sub == ((1,), (0, 2), (1,))


def test_mean_path_length_hand_values(path3):
    assert A.mean_path_length(path3) == pytest.approx((1 + 1 + 2) / 3)
    assert A.mean_path_length(make_adj(3, [])) == 0.0


def test_spearman_hand_values_and_ties():
    assert A.spearman([1, 2, 3], [1, 3, 2]) == pytest.approx(0.5)
    assert A.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert A.spearman([1, 1, 2], [1, 2, 2]) == pytest.approx(0.5)     # Mittelwertränge: (1,5; 1,5; 3) und (1; 2,5; 2,5)
    assert math.isnan(A.spearman([1, 1, 1], [1, 2, 3])) and math.isnan(A.spearman([1], [1]))
    with pytest.raises(ValueError):
        A.spearman([1, 2], [1])


def test_average_ranks():
    assert A.average_ranks([10, 20, 20, 30]).tolist() == [1.0, 2.5, 2.5, 4.0]


def test_auc_hand_values():
    assert A.auc([3, 4], [1, 3]) == pytest.approx(0.875)             # Paare: 3>1, 3=3 (1/2), 4>1, 4>3
    assert A.auc([1, 1], [1, 1]) == pytest.approx(0.5) and A.auc([5], [1, 2]) == 1.0 and A.auc([1], [5, 6]) == 0.0
    assert math.isnan(A.auc([], [1]))


def test_partial_spearman_matches_the_residual_route():
    rng = np.random.default_rng(3)
    ctl = rng.normal(size=60)
    a = ctl + rng.normal(size=60)
    b = ctl + 0.5 * a + rng.normal(size=60)
    ra, rb, rc = A.average_ranks(a), A.average_ranks(b), A.average_ranks(ctl)

    def resid(y):
        x = np.vstack([rc, np.ones_like(rc)]).T
        coef = np.linalg.lstsq(x, y, rcond=None)[0]
        return y - x @ coef

    assert A.partial_spearman(a, b, ctl) == pytest.approx(float(np.corrcoef(resid(ra), resid(rb))[0, 1]))
    assert math.isnan(A.partial_spearman(a, b, a))                       # Kontrolle gleich a: nicht definiert


def test_top_set_ties_and_cut():
    chosen, cut = A.top_set([3, 1, 3, 2, 3], 2)
    assert chosen == {0, 2} and cut == 1                               # Gleichstand zwischen 0, 2 und 4: die kleineren Nummern gewinnen, Knoten 4 bleibt draußen
    assert A.top_set([3, 1, 2], 1, largest=False) == ({1}, 0)
    assert A.top_set([float("nan"), 2.0, 1.0], 5) == ({1, 2}, 0) and A.top_set([], 3) == (set(), 0) and A.top_set([1.0], 0) == (set(), 0)


def test_jaccard_and_share_better():
    assert A.jaccard({1, 2}, {2, 3}) == pytest.approx(1 / 3) and A.jaccard(set(), set()) == 1.0
    vals = [5.0, 3.0, 3.0, 1.0, float("nan")]
    assert A.share_better(vals, 0) == 0.0 and A.share_better(vals, 1) == pytest.approx(1 / 3) and A.share_better(vals, 3) == 1.0
    assert A.share_better(vals, 3, largest=False) == 0.0 and math.isnan(A.share_better(vals, 4))


def test_arrival_times_are_bfs_distances_at_p_one_and_never_at_p_zero():
    path = make_adj(4, [(0, 1), (1, 2), (2, 3)])
    t = A.arrival_times(path, 1.0, [0], 1, 1)
    assert math.isnan(t[0]) and t[1:] == [1.0, 2.0, 3.0]
    assert all(math.isnan(x) for x in A.arrival_times(path, 0.0, [0], 3, 1))
    both = A.arrival_times(path, 1.0, [0, 3], 2, 1)
    assert both[1] == pytest.approx((1 + 2) / 2) and both[0] == pytest.approx(3.0)       # Knoten 1: Quelle 0 nach 1, Quelle 3 nach 2; Knoten 0 nur von Quelle 3 (nach 3)


def test_arrival_times_are_deterministic_and_slower_for_small_p():
    adj = S.make_instance("Zufallsnetz", 60, 4, 1, layout=False).adj
    a = A.arrival_times(adj, 0.3, [0, 5], 4, 7)
    np.testing.assert_array_equal(a, A.arrival_times(adj, 0.3, [0, 5], 4, 7))          # nan gleich nan
    fast = A.arrival_times(adj, 0.9, [0, 5], 4, 7)
    ok = [i for i in range(60) if not math.isnan(a[i]) and not math.isnan(fast[i])]
    assert ok and np.mean([a[i] for i in ok]) > np.mean([fast[i] for i in ok])


def test_float_noise_does_not_break_ties():
    """Mathematisch gleiche Werte, die sich um 1e-15 unterscheiden, sind ein Gleichstand (Rang, Auswahl, Anteil der besseren)."""
    noisy = [0.3, 0.3 + 3e-16, 0.1, 0.3 - 2e-16]
    assert A.average_ranks(noisy).tolist() == [3.0, 3.0, 1.0, 3.0]
    assert A.top_set(noisy, 2) == ({0, 1}, 1)                       # Knoten 3 liegt gleichauf und bleibt wegen der größeren Nummer draußen
    assert A.share_better(noisy, 0) == 0.0 and A.share_better(noisy, 2, largest=False) == 0.0


def test_two_node_networks_have_defined_closeness_and_rank_correlation():
    edge = make_adj(2, [(0, 1)])
    assert A.closeness(edge) == [1.0, 1.0]                              # (r - 1) / Summe · (r - 1) / (n - 1) = 1 bei n = 2
    assert A.spearman([1, 2], [1, 2]) == pytest.approx(1.0) and A.spearman([1, 2], [2, 1]) == pytest.approx(-1.0)


def test_constant_vectors_give_nan_without_a_numpy_warning():
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert math.isnan(A.pearson([1.0, 1.0, 1.0], [1.0, 2.0, 3.0])) and math.isnan(A.pearson([1.0, 2.0, 3.0], [2.0, 2.0, 2.0]))
        assert math.isnan(A.spearman([1, 1, 1], [1, 2, 3])) and math.isnan(A.pearson([1.0], [1.0]))


def test_empty_class_gives_nan_auc_without_a_numpy_warning():
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert math.isnan(A.auc([], [1.0])) and math.isnan(A.auc([1.0], [])) and math.isnan(A.auc([], []))


def test_largest_component_of_equal_size_is_the_first_one():
    adj = make_adj(4, [(0, 1), (2, 3)])
    assert A.largest_component(adj) == (((1,), (0,)), [0, 1])           # bei gleicher Größe gewinnt die Komponente mit der kleineren Knotennummer


def test_share_better_with_one_or_two_valid_values():
    assert A.share_better([1.0, 2.0], 0) == 1.0 and A.share_better([1.0, 2.0], 1) == 0.0           # zwei Werte: der andere ist besser bzw. schlechter
    assert math.isnan(A.share_better([5.0], 0)) and math.isnan(A.share_better([5.0, float("nan")], 0))


def test_unreached_nodes_are_nan_without_a_numpy_warning():
    import warnings

    adj = make_adj(4, [(0, 1)])                                          # Knoten 2 und 3 sind nie erreichbar
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        t = A.arrival_times(adj, 0.5, [0], 2, 1)
    assert math.isnan(t[0]) and math.isnan(t[2]) and math.isnan(t[3]) and t[1] >= 1.0
