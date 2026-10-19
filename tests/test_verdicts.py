"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier."""

import dataclasses

import pytest

import slo_constants as C
import slo_evaluation as ev

NAN = float("nan")


def _analysis(rho=-0.97, jac_cd=0.71, jac_cb=0.71, clu=0.74, k=6, ties=0, typ=C.T_RANDOM, valid=None, edges=True):
    a = ev.analyse(ev.Settings(typ, 120, 6, 3))
    inst = a.inst
    if not edges:
        inst = dataclasses.replace(inst, adj=tuple(() for _ in inst.adj))
    stats = dict(a.stats, c_deg=rho, c_clu_deg=clu)
    tops = dict(a.tops, k=k, c_ties=ties, d_ties=0, b_ties=0)
    return dataclasses.replace(a, inst=inst, stats=stats, tops=tops, jac_cd=jac_cd, jac_cb=jac_cb, valid=a.valid if valid is None else valid)


def test_de_uses_a_decimal_comma_and_a_dash_for_undefined_numbers():
    assert ev.de(1.26, 1) == "1,3" and ev.de(0.9487, 3) == "0,949" and ev.de(3, 0) == "3" and ev.de(float("nan"), 2) == "–" and ev.de(None) == "–"


def test_main_verdict_warns_when_the_broker_is_nearly_a_hub():
    kind, text = ev.verdict_main(_analysis())
    assert kind == "warning" and "fast ein Knoten mit vielen Kontakten" in text
    assert "ρ = -0,97" in text and "zu 0,71, (niedriges Constraint, hohe Betweenness) zu 0,71" in text and "mit dem Clustering mit ρ = 0,74 zusammen" in text


def test_main_verdict_thresholds():
    assert ev.verdict_main(_analysis(rho=-0.9, jac_cd=0.7))[0] == "warning"              # beide Grenzen gelten einschließlich
    assert ev.verdict_main(_analysis(rho=-0.89, jac_cd=0.7))[0] == "info"                # Korrelation zu schwach
    assert ev.verdict_main(_analysis(rho=-0.97, jac_cd=0.69))[0] == "info"               # Überlappung zu klein für "fast Hub", aber nicht klein genug
    assert ev.verdict_main(_analysis(rho=-0.97, jac_cd=0.6))[0] == "info"
    kind, text = ev.verdict_main(_analysis(rho=-0.97, jac_cd=0.59))
    assert kind == "success" and "verschiedene Knoten" in text and "mehr als ein Hub" in text


def test_main_verdict_hides_an_undefined_partial_correlation_and_an_undefined_rank_correlation():
    assert "Clustering" not in ev.verdict_main(_analysis(clu=NAN))[1]
    kind, text = ev.verdict_main(_analysis(rho=NAN, jac_cd=0.5))
    assert kind == "warning" and "nicht definiert" in text and "zu 0,50" in text


def test_main_verdict_says_the_measures_do_not_separate_when_ties_fill_the_selection():
    kind, text = ev.verdict_main(_analysis(k=6, ties=6))
    assert kind == "warning" and "trennen hier nicht" in text and "(6)" in text and "ρ = -0,97" in text
    assert ev.verdict_main(_analysis(k=6, ties=5))[0] == "warning" and "Hinweis: am Rand" in ev.verdict_main(_analysis(k=6, ties=5))[1]      # kleinere Zahl: nur der Hinweis
    assert "Hinweis" not in ev.verdict_main(_analysis(k=6, ties=0))[1]


def test_main_verdict_for_tiny_networks_names_the_broker_and_the_hub():
    a = ev.analyse(ev.Settings(C.T_BROKER, knoten=15))
    kind, text = ev.verdict_main(a)
    assert kind == "info" and "zu klein für Top-5-%-Mengen (19 Knoten mit Kontakt)" in text
    assert "niedrigste Constraint hat Knoten 4 (0,301, Grad 7)" in text
    assert "Der Makler (Knoten 15, drei Kontakte in drei Verbünden) hat 0,333, der Hub (Knoten 4, 7 Kontakte, davon drei Blätter) 0,301" in text


def test_main_verdict_without_edges():
    kind, text = ev.verdict_main(_analysis(edges=False))
    assert kind == "warning" and "zu wenige Kanten" in text


def test_degree_verdict_counts_near_degree_measures_and_names_the_farthest():
    rows = [{"typ": "A", "c_deg": -0.95, "c_clu_deg": 0.7}, {"typ": "B", "c_deg": -0.5, "c_clu_deg": 0.2}, {"typ": "C", "c_deg": NAN, "c_clu_deg": NAN}]
    kind, text = ev.verdict_degree(rows)
    assert kind == "info" and "In 1 von 2 Netztypen" in text and "„B“ mit ρ = -0,50" in text and "0,20 bis 0,70" in text
    assert ev.verdict_degree([{"typ": "A", "c_deg": -0.9, "c_clu_deg": NAN}])[1].startswith("In 1 von 1 Netztypen")      # genau -0,9 zählt
    assert ev.verdict_degree([{"typ": "A", "c_deg": -0.89, "c_clu_deg": NAN}])[1].startswith("In 0 von 1 Netztypen")
    assert ev.verdict_degree([{"typ": "A", "c_deg": NAN, "c_clu_deg": NAN}])[0] == "warning"


def _broker_rows():
    return [{"typ": "Gitter", "j_cd": 0.0, "perc_c": NAN, "perc_d": NAN, "bridges": 0.0, "bridges_inner": 0.0, "ties": 75.0},
            {"typ": "Hubs", "j_cd": 0.6, "perc_c": 0.034, "perc_d": 0.042, "bridges": 68.0, "bridges_inner": 5.0, "ties": 2.0},
            {"typ": "BA", "j_cd": 0.85, "perc_c": NAN, "perc_d": NAN, "bridges": 0.0, "bridges_inner": 0.0, "ties": 0.0}]


def test_broker_verdict_names_range_bridges_and_ties():
    kind, text = ev.verdict_broker(_broker_rows())
    assert kind == "info"
    assert "zwischen 0,00 („Gitter“) und 0,85 („BA“)" in text
    assert "im Netztyp „Hubs“ sind von 68 Brücken nur 5 Brücken" in text and "Perzentil 0,03, beim Grad im Perzentil 0,04" in text
    assert "bis zu 75 Knoten am Rand" in text


def test_broker_verdict_without_bridges_or_ties():
    rows = [dict(r, perc_c=NAN, perc_d=NAN, ties=0.0) for r in _broker_rows()]
    text = ev.verdict_broker(rows)[1]
    assert "Brücken führen" not in text and "Gleichständen" not in text
    assert ev.verdict_broker([{"typ": "x", "j_cd": NAN, "perc_c": NAN, "perc_d": NAN, "bridges": 0.0, "bridges_inner": 0.0, "ties": 0.0}])[0] == "warning"


def test_granovetter_verdict_lists_the_auc_and_the_shares():
    rows = [{"c": 6, "auc": 0.68, "zero_inner": 0.6, "zero_between": 0.97, "bridge_share": 0.004}, {"c": 16, "auc": 0.96, "zero_inner": 0.03, "zero_between": 0.69, "bridge_share": 0.0}]
    kind, text = ev.verdict_granovetter(rows)
    assert kind == "info" and "c = 6: 0,68, c = 16: 0,96" in text
    assert "Bei c = 6 haben 60 %" in text and "bei c = 16 nur 3 %" in text and "(zwischen den Verbünden 69 %)" in text and "Anteil der Kanten 0,0 %" in text
    assert ev.verdict_granovetter(rows[:1])[0] == "warning" and ev.verdict_granovetter([dict(rows[0], auc=NAN), dict(rows[1], auc=NAN)])[0] == "warning"


def test_watts_verdict_names_the_drop_in_path_length_and_clustering():
    rows = [{"beta": 0.0, "clustering": 0.6, "zero": 0.0, "constraint": 0.378, "path": 25.4}, {"beta": 0.01, "clustering": 0.586, "zero": 0.009, "constraint": 0.373, "path": 12.1},
            {"beta": 1.0, "clustering": 0.016, "zero": 0.917, "constraint": 0.19, "path": 3.4}]
    kind, text = ev.verdict_watts(rows)
    assert kind == "info" and "Schon bei β = 0,01 sinkt die mittlere Pfadlänge von 25,4 auf 12,1, während das Clustering von 0,60 nur auf 0,59 fällt" in text
    assert "Bei β = 1,0 haben 92 % der Kanten keinen gemeinsamen Nachbarn (Clustering 0,02, mittleres Constraint 0,19 gegen 0,38" in text
    assert ev.verdict_watts(rows[:1])[0] == "warning" and ev.verdict_watts([rows[0], rows[2]])[0] == "warning"        # ohne kleine Umverdrahtung kein Vergleich


def test_arrival_verdict_counts_earlier_and_closer_types():
    rows = [{"typ": "A", "t_c": 0.89, "t_l": -0.95, "pc_l": 0.18}, {"typ": "B", "t_c": 0.86, "t_l": -0.84, "pc_l": 0.44}]
    kind, text = ev.verdict_arrival(rows)
    assert kind == "info" and "in 2 von 2 Netztypen früher" in text and "0,86 bis 0,89" in text and "in 1 von 2 Netztypen besser voraus" in text and "0,18 bis 0,44" in text
    assert "in 1 von 2 Netztypen früher" in ev.verdict_arrival([rows[0], dict(rows[1], t_c=-0.2)])[1]
    assert ev.verdict_arrival([{"typ": "A", "t_c": NAN, "t_l": NAN, "pc_l": NAN}])[0] == "warning"


def test_diversity_verdict_thresholds():
    stats = {"ent_deg": 0.18, "ent_cons": -0.34, "ent_cons_deg": -0.54, "div_eff": 0.48}
    kind, text = ev.verdict_diversity(stats)
    assert kind == "success" and "ρ = 0,18" in text and "ρ = -0,34" in text and "-0,54" in text and "ρ = 0,48" in text
    assert ev.verdict_diversity(dict(stats, ent_cons_deg=-0.3))[0] == "success"           # genau -0,3 zählt
    assert ev.verdict_diversity(dict(stats, ent_cons_deg=-0.29))[0] == "info"
    assert ev.verdict_diversity(dict(stats, ent_cons_deg=NAN))[0] == "warning"
