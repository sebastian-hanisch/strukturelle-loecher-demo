"""Netze: gültige Netze, Determinismus (auch über Prozesse), Positionen, Makler-Beispiel, Link-Netz mit und ohne Navigationsseiten, Watts-Strogatz."""

import math
import os
import subprocess
import sys
from pathlib import Path

import pytest

import slo_algorithm as A
import slo_constants as C
import slo_scenario as S

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("typ", C.GENERATED_TYPES)
@pytest.mark.parametrize("n,c", [(C.N_MIN, C.C_MIN), (C.N_MIN, C.C_MAX), (C.DEFAULT_N, C.DEFAULT_C), (C.N_MAX, C.C_MAX)])
def test_every_corner_gives_a_valid_network(typ, n, c):
    inst = S.make_instance(typ, n, c, 35)
    assert inst.n >= 2 and len(inst.pos) == inst.n
    for x, y in inst.pos:
        assert math.isfinite(x) and math.isfinite(y) and -1e-9 <= x <= 1 + 1e-9 and -1e-9 <= y <= 1 + 1e-9
    for a, nb in enumerate(inst.adj):
        assert list(nb) == sorted(set(nb)) and a not in nb          # sortiert, keine Doppelkanten, keine Schleifen
        for b in nb:
            assert a in inst.adj[b]                                 # symmetrisch


def test_instances_are_deterministic_per_seed_and_differ_between_seeds():
    a = S.make_instance(C.T_COMMUNITIES, 80, 6, 5)
    b = S.make_instance(C.T_COMMUNITIES, 80, 6, 5)
    assert a.adj == b.adj and a.pos == b.pos
    assert S.make_instance(C.T_COMMUNITIES, 80, 6, 6, layout=False).adj != a.adj


def test_layout_free_instances_have_the_same_network():
    for typ in (C.T_RANDOM, C.T_LINK):
        assert S.make_instance(typ, 60, 6, 3, layout=False).adj == S.make_instance(typ, 60, 6, 3).adj


def test_the_community_network_has_the_planned_inside_share():
    inst = S.make_instance(C.T_COMMUNITIES, 240, 8, 7, layout=False)
    group = S.communities_of(240, C.BLOCKS)
    inside = sum(1 for a, b in A.edges_of(inst.adj) if group[a] == group[b]) / inst.m
    assert inside == pytest.approx(0.8, abs=0.01) and inst.groups == tuple(group)


def test_the_broker_example_has_the_planned_structure():
    inst = S.make_instance(C.T_BROKER, 999, 99, 1)
    assert inst.n == 19 and inst.m == 36                                  # drei K5 (30 Kanten) + 3 Kanten des Maklers + 3 Blätter
    assert [len(inst.adj[i]) for i in (S.BROKER_MAKLER, S.BROKER_HUB, 0, 1, 16)] == [3, 7, 5, 4, 1]
    assert inst.groups[S.BROKER_MAKLER] == "Makler" and inst.groups[16] == "Blatt am Hub"
    assert len(inst.pos) == 19 and all(0 <= x <= 1 and 0 <= y <= 1 for x, y in inst.pos)


def test_the_link_network_with_and_without_the_navigation_pages():
    full = S.make_instance(C.T_LINK, 0, 0, 0, layout=False)
    drop = S.make_instance(C.T_LINK, 0, 0, 0, nav=C.NAV_DROP, layout=False)
    assert full.n == 350 and drop.n == 348 and "index.html" in full.labels and "index.html" not in drop.labels and "kontakt.html" not in drop.labels
    i, k = full.labels.index("index.html"), full.labels.index("kontakt.html")
    assert len(full.adj[i]) == len(full.adj[k]) == 348                    # mit allen anderen verlinkt (außer dem isolierten Knoten und sich selbst)
    assert full.m - drop.m == len(full.adj[i]) + len(full.adj[k]) - (1 if k in full.adj[i] else 0)
    assert S.link_stand() == "2026-09-30"


def test_watts_strogatz_keeps_the_edge_count_and_beta_zero_is_the_regular_ring():
    ring = S.watts_strogatz_instance(60, 6, 0.0, 1)
    assert ring.m == 180 and set(A.degrees(ring.adj)) == {6}
    assert A.clustering(ring.adj)[0] == pytest.approx(0.6)               # k = 6: Clustering 3(k - 2) / (4(k - 1)) = 0,6
    assert S.watts_strogatz_instance(60, 6, 0.3, 2).m == 180


def test_unknown_network_type_raises():
    with pytest.raises(ValueError):
        S.make_instance("gibt es nicht", 50, 6, 1)


def test_the_force_layout_of_a_single_node():
    assert S.layout_force(((),), 1) == ((0.5, 0.5),)


def test_results_do_not_depend_on_the_hash_seed():
    """Dasselbe Szenario in zwei Prozessen mit verschiedenem PYTHONHASHSEED rechnet dasselbe."""
    code = (
        "import sys; sys.path.insert(0, %r)\n"
        "import slo_evaluation as ev, slo_constants as C\n"
        "out = []\n"
        "for typ in (C.T_COMMUNITIES, C.T_POWER, C.T_HUBS):\n"
        "    a = ev.analyse(ev.Settings(typ, 90, 6, 7))\n"
        "    out.append((a.inst.m, round(a.stats['c_deg'], 9), round(a.jac_cd, 9), len(a.bridges)))\n"
        "print(repr(out))\n"
    ) % str(ROOT)
    outputs = []
    for hash_seed in ("1", "2"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONIOENCODING="utf-8")
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=180)
        assert proc.returncode == 0, proc.stderr
        outputs.append(proc.stdout)
    assert outputs[0] == outputs[1]
