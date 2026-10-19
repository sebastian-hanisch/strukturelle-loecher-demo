"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen."""

import slo_constants as C
import slo_evaluation as ev
import slo_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for name, p in C.PRESETS.items():
        assert p["netztyp"] in C.ALL_TYPES and C.N_MIN <= p["n"] <= C.N_MAX and C.C_MIN <= p["c"] <= C.C_MAX, name
        assert 0 <= p["seed"] <= C.SEED_MAX and p["mass"] in C.MEASURES and p["nav"] in C.NAV_CHOICES and 0 <= p["knoten"] <= C.KNOTEN_MAX, name


def test_every_preset_node_exists_in_its_network():
    for name, p in C.PRESETS.items():
        a = ev.analyse(ev.Settings(**p))
        assert a.node == p["knoten"], name                  # nicht auf n - 1 begrenzt: die Nummer gibt es wirklich


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Verbünde (Voreinstellung)"]) == ev.Settings()
    assert next(iter(C.PRESETS)) == "Verbünde (Voreinstellung)"


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_presets_cover_both_link_variants_and_the_broker_example():
    ps = list(C.PRESETS.values())
    assert {p["nav"] for p in ps if p["netztyp"] == C.T_LINK} == set(C.NAV_CHOICES)
    assert any(p["netztyp"] == C.T_BROKER for p in ps) and any(p["netztyp"] == C.T_COMMUNITIES for p in ps)


def test_the_default_node_has_the_lowest_constraint_of_the_default_network():
    a = ev.analyse(ev.Settings())
    cons = a.tab[C.M_CONSTRAINT]
    assert a.node == C.DEFAULT_KNOTEN and cons[a.node] == min(x for x in cons if x == x)
