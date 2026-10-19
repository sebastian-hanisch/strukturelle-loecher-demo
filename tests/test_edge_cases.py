"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): n = 1, n = 2, keine Kanten, Gleichstände, inklusive Grenzen."""

import math

import pytest

import slo_algorithm as A
import slo_constants as C
import slo_evaluation as ev
import slo_scenario as S
from conftest import make_adj


def test_measures_of_networks_without_edges_are_defined():
    adj = make_adj(4, [])
    assert all(math.isnan(x) for x in A.constraint(adj)) and all(math.isnan(x) for x in A.effective_size(adj))
    assert A.clustering(adj) == [0.0] * 4 and A.closeness(adj) == [0.0] * 4 and A.betweenness(adj) == [0.0] * 4 and A.bridges(adj) == []
    tab = ev.measure_table(adj)
    assert ev.top_sets(adj, tab)["k"] == 0
    assert all(math.isnan(v) for v in ev.rank_stats(adj, tab).values())


def test_single_node_and_single_edge():
    one = make_adj(1, [])
    assert A.betweenness(one) == [0.0] and A.closeness(one) == [0.0] and A.mean_path_length(one) == 0.0 and A.largest_component(one) == (((),), [0])
    edge = make_adj(2, [(0, 1)])
    assert A.constraint(edge) == [1.0, 1.0] and A.effective_size(edge) == [1.0, 1.0] and A.bridges(edge) == [(0, 1)] and A.edge_overlap(edge, 0, 1) == 0.0
    assert A.arrival_times(edge, 0.5, [0], 1, 1)[0] != A.arrival_times(edge, 0.5, [0], 1, 1)[0]            # nan für die Quelle


def test_empty_inputs_of_the_statistics():
    assert math.isnan(A.spearman([], [])) and math.isnan(A.auc([], [])) and A.jaccard(set(), {1}) == 0.0
    assert A.average_ranks([]).tolist() == []


def test_clamp_node_is_inclusive_at_both_ends():
    assert ev.clamp_node(-5, 10) == 0 and ev.clamp_node(0, 10) == 0 and ev.clamp_node(9, 10) == 9 and ev.clamp_node(10, 10) == 9 and ev.clamp_node(999, 1) == 0


def test_analysis_of_every_type_at_the_slider_corners_does_not_fail():
    for typ in C.GENERATED_TYPES:
        for n, c in ((C.N_MIN, C.C_MIN), (C.N_MAX, C.C_MAX)):
            a = ev.analyse(ev.Settings(typ, n, c, 1, C.M_BETWEENNESS, C.KNOTEN_MAX))
            assert a.node == a.inst.n - 1 and len(a.tab[C.M_CONSTRAINT]) == a.inst.n and 0 <= a.valid <= a.inst.n
            assert ev.verdict_main(a)[0] in ("success", "info", "warning")


def test_every_node_of_every_preset_network_has_a_calculation_path_that_sums_to_the_constraint():
    for typ in (C.T_BROKER, C.T_RANDOM):
        a = ev.analyse(ev.Settings(typ, 40, 5, 2))
        for node in range(a.inst.n):
            terms = A.ego_terms(a.inst.adj, node)
            if terms:
                assert sum(t[4] for t in terms) == pytest.approx(a.tab[C.M_CONSTRAINT][node])
            else:
                assert math.isnan(a.tab[C.M_CONSTRAINT][node])


def test_the_selected_node_beyond_the_network_is_clamped():
    a = ev.analyse(ev.Settings(C.T_BROKER, knoten=300))
    assert a.node == 18


def test_experiments_survive_tiny_networks():
    n = C.N_MIN
    assert len(ev.degree_rows(n, C.C_MIN, seeds=(1,))) == len(C.GENERATED_TYPES)
    assert len(ev.broker_rows(n, C.C_MIN, seeds=(1,))) == len(C.GENERATED_TYPES)
    assert len(ev.granovetter_rows(n, seeds=(1,))) == len(C.GRAN_DEGREES)
    assert len(ev.watts_rows(n, seeds=(1,))) == len(C.WS_BETAS)
    assert len(ev.arrival_rows(n, C.C_MIN, seeds=(1,))) == len(C.ARR_TYPES)
    assert set(ev.diversity_stats(n, seeds=(1,))) == {"div_eff", "div_cons", "div_deg", "ent_eff", "ent_cons", "ent_deg", "ent_cons_deg"}


def test_grid_rounds_to_a_square_and_has_equal_corner_degrees():
    inst = S.make_instance(C.T_GRID, 50, 4, 1)
    assert inst.n == 49 and A.degrees(inst.adj)[0] == 2 and max(A.degrees(inst.adj)) == 4


def test_ties_in_the_top_set_follow_the_smaller_node_number():
    inst = S.make_instance(C.T_GRID, 100, 4, 1, layout=False)
    tab = ev.measure_table(inst.adj)
    tops = ev.top_sets(inst.adj, tab)
    assert tops["k"] == 5 and tops["d_ties"] > 0 and tops["d"] == set(sorted(i for i, d in enumerate(A.degrees(inst.adj)) if d == 4)[:5])


def test_verdict_for_a_grid_says_the_measures_do_not_separate():
    kind, text = ev.verdict_main(ev.analyse(ev.Settings(C.T_GRID, 120, 6, 1)))
    assert kind == "warning" and "trennen hier nicht" in text
