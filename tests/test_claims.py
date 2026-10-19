"""Jede Zahl aus der README wird hier über dieselben Auswertungsfunktionen wie in der App nachgerechnet (DEMO-PLAYBOOK §4).

Netze der Messreihen: die acht festen Netze `SWEEP_SEEDS` je Zelle, n = 250, c = 6, wo nichts anderes steht (Experiment 3 und 5: n = 300). Alle Rangkorrelationen sind
Spearman-Werte mit Mittelwerträngen über die Knoten mit mindestens einem Kontakt, Mediane über die acht Netze. Zufall läuft über seedbare Generatoren und ist plattformstabil;
Kennzahlen werden mit Band geprüft."""

from functools import lru_cache

import numpy as np
import pytest

import slo_algorithm as A
import slo_constants as C
import slo_evaluation as ev
import slo_scenario as S

SW = C.SWEEP_SEEDS


@lru_cache(maxsize=None)
def _degree():
    return {r["typ"]: r for r in ev.degree_rows(250, 6, seeds=SW)}


@lru_cache(maxsize=None)
def _broker(c):
    return {r["typ"]: r for r in ev.broker_rows(250, c, seeds=SW)}


@lru_cache(maxsize=None)
def _gran():
    return {r["c"]: r for r in ev.granovetter_rows(300, seeds=SW)}


@lru_cache(maxsize=None)
def _watts():
    return {r["beta"]: r for r in ev.watts_rows(300, seeds=SW)}


@lru_cache(maxsize=None)
def _arrival():
    return {r["typ"]: r for r in ev.arrival_rows(250, 6, seeds=SW)}


@lru_cache(maxsize=None)
def _diversity():
    return ev.diversity_stats(300, seeds=SW)


def test_constraint_is_nearly_a_degree_measure_in_most_network_types():
    rows = _degree()
    expect = {C.T_COMMUNITIES: -0.96, C.T_RANDOM: -0.99, C.T_POWER: -0.96, C.T_BA: -0.97, C.T_RING: -0.76, C.T_GRID: -0.82, C.T_HUBS: -0.98}
    for typ, rho in expect.items():
        assert rows[typ]["c_deg"] == pytest.approx(rho, abs=0.03), typ
    assert sum(1 for r in rows.values() if r["c_deg"] <= -0.9) == 5
    assert rows[C.T_RANDOM]["c_eff"] == pytest.approx(-1.0, abs=0.02) and rows[C.T_HUBS]["c_eff"] == pytest.approx(-0.86, abs=0.03) and rows[C.T_HUBS]["eff_deg"] == pytest.approx(0.77, abs=0.03)


def test_what_stays_at_fixed_degree_is_clustering_and_betweenness():
    rows = _degree()
    clu = {C.T_COMMUNITIES: 0.78, C.T_RANDOM: 0.84, C.T_POWER: 0.88, C.T_BA: 0.90, C.T_RING: 0.21, C.T_HUBS: 0.84}
    for typ, value in clu.items():
        assert rows[typ]["c_clu_deg"] == pytest.approx(value, abs=0.04), typ
    assert np.isnan(rows[C.T_GRID]["c_clu_deg"])                              # im Gitter ist der Grad fast konstant: nicht definiert
    bet = {C.T_COMMUNITIES: -0.49, C.T_RANDOM: -0.27, C.T_POWER: -0.47, C.T_BA: -0.21, C.T_RING: -0.19, C.T_GRID: -0.75, C.T_HUBS: -0.79}
    for typ, value in bet.items():
        assert rows[typ]["c_bet_deg"] == pytest.approx(value, abs=0.05), typ


def test_degree_verdict_numbers():
    kind, text = ev.verdict_degree(list(_degree().values()))
    assert kind == "info" and "In 5 von 7 Netztypen" in text and "„Ring mit Abkürzungen“ mit ρ = -0,76" in text and "0,21 bis 0,90" in text


def test_the_constraint_depends_on_equal_degree_and_triangles_almost_entirely():
    res = ev.equal_degree_spread(250, 6, seeds=SW)
    assert res["groups"] == 161 and res["median"] == pytest.approx(0.012, abs=0.004) and res["share_wide"] == pytest.approx(0.019, abs=0.01)


def test_hand_examples_of_the_constraint():
    adj = S.broker_instance().adj
    cons, eff = A.constraint(adj), A.effective_size(adj)
    assert cons[S.BROKER_MAKLER] == pytest.approx(1 / 3) and eff[S.BROKER_MAKLER] == pytest.approx(3.0)
    assert cons[S.BROKER_HUB] == pytest.approx(0.3007, abs=1e-3) and eff[S.BROKER_HUB] == pytest.approx(5.2857, abs=1e-3)
    betw = A.betweenness(adj)
    assert max(range(19), key=lambda i: betw[i]) == S.BROKER_MAKLER and betw[S.BROKER_MAKLER] == pytest.approx(0.686, abs=0.003)
    barbell = tuple(tuple(sorted(j for j in range(12) if j != i and (j // 6 == i // 6 or {i, j} == {5, 6}))) for i in range(12))
    cb, eb = A.constraint(barbell), A.effective_size(barbell)
    assert cb[5] == pytest.approx(0.478, abs=0.001) and cb[0] == pytest.approx(0.629, abs=0.001) and eb[5] == pytest.approx(2.667, abs=0.001) and eb[0] == pytest.approx(1.0)
    triangle = ((1, 2), (0, 2), (0, 1))
    assert A.constraint(triangle)[0] == pytest.approx(1.125)
    assert A.constraint(((1, 2, 3), (0, 2), (0, 1), (0,)))[0] == pytest.approx(11 / 18)
    assert A.constraint(((1, 2, 3), (0, 2, 4, 5, 6), (0, 1), (0,), (1,), (1,), (1,)))[0] == pytest.approx(0.5211, abs=1e-3)       # Dreiecks-Nachbar mit drei weiteren Kontakten


def test_top_five_percent_sets_overlap_only_in_communities_and_hubs():
    rows = _broker(6)
    assert rows[C.T_COMMUNITIES]["j_cd"] == pytest.approx(0.51, abs=0.05) and rows[C.T_COMMUNITIES]["j_cb"] == pytest.approx(0.37, abs=0.05)
    assert rows[C.T_HUBS]["j_cd"] == pytest.approx(0.60, abs=0.05) and rows[C.T_HUBS]["j_cb"] == pytest.approx(0.50, abs=0.05)
    assert rows[C.T_POWER]["j_cd"] == pytest.approx(0.85, abs=0.05) and rows[C.T_POWER]["j_cb"] == pytest.approx(0.71, abs=0.05)
    assert rows[C.T_BA]["j_cd"] == pytest.approx(0.85, abs=0.05) and rows[C.T_BA]["j_cb"] == pytest.approx(0.85, abs=0.05)
    assert rows[C.T_RING]["j_cd"] == pytest.approx(0.71, abs=0.05) and rows[C.T_RING]["j_cb"] == pytest.approx(0.50, abs=0.05)
    assert rows[C.T_RANDOM]["j_cd"] == pytest.approx(0.60, abs=0.05) and rows[C.T_RANDOM]["j_cb"] == pytest.approx(0.71, abs=0.05)
    assert rows[C.T_GRID]["j_cd"] == 0.0 and rows[C.T_GRID]["ties"] == 183 and rows[C.T_RING]["ties"] == pytest.approx(49, abs=3)              # Gleichstandsartefakt


def test_bridges_follow_the_degree_percentile_not_a_constraint_extreme():
    rows = _broker(3)
    assert rows[C.T_RANDOM]["bridges"] == pytest.approx(41.5, abs=3) and rows[C.T_RANDOM]["bridges_inner"] == pytest.approx(7.0, abs=2)
    assert rows[C.T_RANDOM]["perc_c"] == pytest.approx(0.52, abs=0.05) and rows[C.T_RANDOM]["perc_d"] == pytest.approx(0.50, abs=0.05)
    assert rows[C.T_COMMUNITIES]["bridges"] == pytest.approx(44.5, abs=3) and rows[C.T_COMMUNITIES]["bridges_inner"] == pytest.approx(8.5, abs=2)
    assert rows[C.T_COMMUNITIES]["perc_c"] == pytest.approx(0.51, abs=0.05) and rows[C.T_COMMUNITIES]["perc_d"] == pytest.approx(0.49, abs=0.05)
    assert rows[C.T_POWER]["bridges"] == pytest.approx(149, abs=8) and rows[C.T_POWER]["bridges_inner"] == pytest.approx(28, abs=4)
    assert rows[C.T_POWER]["perc_c"] == pytest.approx(0.21, abs=0.04) and rows[C.T_POWER]["perc_d"] == pytest.approx(0.22, abs=0.04)
    hubs = _broker(6)[C.T_HUBS]
    assert hubs["bridges"] == pytest.approx(142, abs=5) and hubs["bridges_inner"] == pytest.approx(5, abs=1) and hubs["perc_c"] == pytest.approx(0.016, abs=0.01) and hubs["perc_d"] == pytest.approx(0.018, abs=0.01)


def test_granovetter_depends_on_the_triangle_density():
    rows = _gran()
    auc = {6: 0.68, 10: 0.84, 16: 0.96}
    zero_inner = {6: 0.60, 10: 0.25, 16: 0.035}
    zero_between = {6: 0.97, 10: 0.88, 16: 0.69}
    for c in (6, 10, 16):
        assert rows[c]["auc"] == pytest.approx(auc[c], abs=0.03), c
        assert rows[c]["zero_inner"] == pytest.approx(zero_inner[c], abs=0.03), c
        assert rows[c]["zero_between"] == pytest.approx(zero_between[c], abs=0.03), c
        assert rows[c]["between_share"] == pytest.approx(0.2, abs=0.001), c
    assert rows[6]["bridge_share"] == pytest.approx(0.004, abs=0.003) and rows[10]["bridge_share"] == 0.0 and rows[16]["bridge_share"] == 0.0
    kind, text = ev.verdict_granovetter(list(rows.values()))
    assert kind == "info" and "c = 6: 0,68, c = 10: 0,84, c = 16: 0,96" in text


def test_a_few_shortcuts_shorten_the_paths_without_destroying_the_triangles():
    rows = _watts()
    assert rows[0.0]["path"] == pytest.approx(25.4, abs=0.3) and rows[0.0]["clustering"] == pytest.approx(0.6, abs=0.005) and rows[0.0]["constraint"] == pytest.approx(0.378, abs=0.005)
    assert rows[0.01]["path"] == pytest.approx(12.1, abs=0.8) and rows[0.01]["clustering"] == pytest.approx(0.586, abs=0.01) and rows[0.01]["zero"] == pytest.approx(0.009, abs=0.005)
    assert rows[0.1]["path"] == pytest.approx(4.77, abs=0.15) and rows[0.1]["clustering"] == pytest.approx(0.438, abs=0.015) and rows[0.1]["zero"] == pytest.approx(0.116, abs=0.02)
    assert rows[1.0]["zero"] == pytest.approx(0.917, abs=0.02) and rows[1.0]["clustering"] == pytest.approx(0.016, abs=0.01) and rows[1.0]["constraint"] == pytest.approx(0.19, abs=0.01)
    assert rows[1.0]["path"] == pytest.approx(3.38, abs=0.1)
    kind, text = ev.verdict_watts(list(rows.values()))
    assert "von 25,4 auf 12,1" in text and "von 0,60 nur auf 0,59" in text and "92 %" in text


def test_the_news_arrive_earlier_at_low_constraint_but_closeness_predicts_better():
    rows = _arrival()
    tc = {C.T_RANDOM: 0.89, C.T_COMMUNITIES: 0.83, C.T_BA: 0.64, C.T_RING: 0.71, C.T_HUBS: 0.86}
    tl = {C.T_RANDOM: -0.95, C.T_COMMUNITIES: -0.90, C.T_BA: -0.92, C.T_RING: -0.89, C.T_HUBS: -0.84}
    pl = {C.T_RANDOM: 0.18, C.T_COMMUNITIES: 0.30, C.T_BA: 0.49, C.T_RING: 0.08, C.T_HUBS: 0.44}
    for typ in tc:
        assert rows[typ]["t_c"] == pytest.approx(tc[typ], abs=0.04), typ
        assert rows[typ]["t_l"] == pytest.approx(tl[typ], abs=0.04), typ
        assert rows[typ]["pc_l"] == pytest.approx(pl[typ], abs=0.07), typ
    assert rows[C.T_HUBS]["t_d"] == pytest.approx(-0.87, abs=0.04) and rows[C.T_RING]["t_d"] == pytest.approx(-0.50, abs=0.06) and rows[C.T_RING]["pc_d"] == pytest.approx(0.61, abs=0.06)
    kind, text = ev.verdict_arrival(list(rows.values()))
    assert "in 5 von 5 Netztypen früher" in text and "0,64 bis 0,89" in text and "in 4 von 5 Netztypen besser voraus" in text and "0,08 bis 0,49" in text


def test_diversity_of_the_neighbourhood_beyond_the_degree():
    s = _diversity()
    assert s["ent_cons_deg"] == pytest.approx(-0.54, abs=0.05) and s["ent_deg"] == pytest.approx(0.18, abs=0.04) and s["ent_cons"] == pytest.approx(-0.34, abs=0.04)
    assert s["div_eff"] == pytest.approx(0.48, abs=0.04) and s["div_cons"] == pytest.approx(-0.54, abs=0.04) and s["div_deg"] == pytest.approx(0.41, abs=0.04) and s["ent_eff"] == pytest.approx(0.27, abs=0.04)


def test_link_network_with_and_without_the_navigation_pages():
    full = ev.analyse(ev.Settings(netztyp=C.T_LINK))
    drop = ev.analyse(ev.Settings(netztyp=C.T_LINK, nav=C.NAV_DROP))
    assert (full.inst.n, full.inst.m, full.valid, len(full.bridges)) == (350, 2374, 349, 0) and (drop.inst.n, drop.inst.m, drop.valid, len(drop.bridges)) == (348, 1679, 347, 121)
    assert float(np.mean(full.tab[C.M_CLUSTERING])) == pytest.approx(0.939, abs=0.005) and float(np.mean(drop.tab[C.M_CLUSTERING])) == pytest.approx(0.584, abs=0.005)
    assert full.stats["c_deg"] == pytest.approx(-0.91, abs=0.01) and drop.stats["c_deg"] == pytest.approx(-0.97, abs=0.01)
    assert full.stats["c_eff"] == pytest.approx(-0.60, abs=0.01) and drop.stats["c_eff"] == pytest.approx(-0.65, abs=0.01)
    assert full.jac_cd == pytest.approx(0.26, abs=0.01) and drop.jac_cd == pytest.approx(0.55, abs=0.01) and drop.jac_cb == pytest.approx(0.79, abs=0.01)
    names = full.inst.labels
    i, k = names.index("index.html"), names.index("kontakt.html")
    assert len(full.inst.adj[i]) == len(full.inst.adj[k]) == 348 and full.tab[C.M_CONSTRAINT][i] == pytest.approx(0.066, abs=0.001) and full.tab[C.M_BETWEENNESS][i] == pytest.approx(0.42, abs=0.01)
    low_full = min((x, j) for j, x in enumerate(full.tab[C.M_CONSTRAINT]) if x == x and full.tab[C.M_DEGREE][j] >= 2)
    assert names[low_full[1]] == "konzepte-spieltheorie.html" and low_full[0] == pytest.approx(0.055, abs=0.001) and full.tab[C.M_DEGREE][low_full[1]] == 65
    dn = drop.inst.labels
    low_drop = sorted((x, j) for j, x in enumerate(drop.tab[C.M_CONSTRAINT]) if x == x and drop.tab[C.M_DEGREE][j] >= 2)[:2]
    assert [dn[j] for _, j in low_drop] == ["konzepte-netzwerkfluss.html", "demos.html"] and [round(x, 3) for x, _ in low_drop] == [0.040, 0.043]
    top_bet = max(range(drop.inst.n), key=lambda j: drop.tab[C.M_BETWEENNESS][j])
    assert dn[top_bet] == "demos.html" and drop.tab[C.M_BETWEENNESS][top_bet] == pytest.approx(0.13, abs=0.005)
    assert sum(1 for d in drop.tab[C.M_DEGREE] if d == 1) / drop.inst.n == pytest.approx(0.348, abs=0.003)


def test_default_network_numbers():
    """Standardnetz (Verbünde, n = 120, c = 6, Seed 35, Knoten 100): die Zahlen der Voreinstellung."""
    a = ev.analyse(ev.Settings())
    assert (a.inst.m, a.valid, len(a.bridges), a.tops["k"]) == (360, 120, 1, 6)
    assert a.stats["c_deg"] == pytest.approx(-0.87, abs=0.01) and a.stats["c_clu_deg"] == pytest.approx(0.75, abs=0.01) and a.stats["c_bet_deg"] == pytest.approx(-0.49, abs=0.01)
    assert a.jac_cd == pytest.approx(0.33, abs=0.01) and a.jac_cb == pytest.approx(0.71, abs=0.01)
    assert a.tab[C.M_CONSTRAINT][100] == pytest.approx(0.112, abs=0.001) and a.tab[C.M_DEGREE][100] == 11
    assert ev.verdict_main(a)[0] == "success"
