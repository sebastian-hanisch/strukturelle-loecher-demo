"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: lädt app.py mit den Standardeinstellungen, klickt jeden Button, fährt jeden Slider an seine Grenzen,
prüft Permalink, Netztypen, Maße, Knotenwahl und alle fünf Experimente; es darf kein Python-Fehler auftreten."""

import os

import pytest
from streamlit.testing.v1 import AppTest

import slo_constants as C

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
EXPERIMENTS = ("degree", "broker", "gran", "watts", "arrival", "diversity")


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _metric(at, label):
    return next(m.value for m in at.metric if m.label == label)


def test_app_loads_without_exception():
    at = _fresh_app()
    assert _metric(at, "Knoten / Kanten") == "120 / 360" and _metric(at, "Brückenkanten") == "1" and _metric(at, "Rangkorrelation Constraint ~ Grad") == "-0,87"
    assert not at.error and not at.warning


def test_every_preset_click_does_not_raise():
    for name in C.PRESETS:
        at = _fresh_app()
        at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
        assert not at.exception, (name, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert labels, "keine Slider gefunden"
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            slider.set_value(int(value) if isinstance(slider.value, int) else value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


def test_all_sliders_at_their_minimum_and_all_at_their_maximum_do_not_raise():
    for edge in ("min", "max"):
        at = _fresh_app()
        for index in range(len(at.slider)):
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            slider.set_value(int(value) if isinstance(slider.value, int) else value)
        at.run(timeout=TIMEOUT)
        assert not at.exception, (edge, [str(e) for e in at.exception])


@pytest.mark.parametrize("typ", C.ALL_TYPES)
def test_every_network_type_renders_with_every_measure(typ):
    at = _fresh_app()
    at.selectbox(key="netztyp_select").set_value(typ).run(timeout=TIMEOUT)
    assert not at.exception
    for mass in C.MEASURES:
        at.selectbox(key="mass_select").set_value(mass).run(timeout=TIMEOUT)
        assert not at.exception, (typ, mass, [str(e) for e in at.exception])


def test_fixed_networks_disable_size_and_seed():
    at = _fresh_app()
    at.selectbox(key="netztyp_select").set_value(C.T_BROKER).run(timeout=TIMEOUT)
    assert at.slider(key="n_slider").disabled and at.slider(key="c_slider").disabled and at.number_input(key="seed_input").disabled
    assert _metric(at, "Knoten / Kanten") == "19 / 36"
    at.selectbox(key="netztyp_select").set_value(C.T_LINK).run(timeout=TIMEOUT)
    assert _metric(at, "Knoten / Kanten") == "350 / 2374"
    at.selectbox(key="nav_select").set_value(C.NAV_DROP).run(timeout=TIMEOUT)
    assert _metric(at, "Knoten / Kanten") == "348 / 1679" and _metric(at, "Brückenkanten") == "121"
    assert any("Schnappschuss" in i.value for i in at.info)


def test_a_node_beyond_the_network_is_clamped_and_reported():
    at = _fresh_app()
    at.number_input(key="knoten_input").set_value(C.KNOTEN_MAX).run(timeout=TIMEOUT)
    assert not at.exception
    assert any("gibt es in diesem Netz nicht" in w.value and "Knoten 119" in w.value for w in at.warning)


def test_the_broker_example_shows_the_hand_calculation():
    at = _fresh_app()
    at.sidebar.button(key=f"preset_Makler-Beispiel").click().run(timeout=TIMEOUT)
    assert not at.exception
    assert any("Constraint = Summe der Quadrate = 0,333" in m.value for m in at.markdown)
    assert any("zu klein für Top-5-%-Mengen" in i.value for i in at.info)


def test_permalink_values_are_clamped_and_unknown_choices_ignored():
    at = AppTest.from_file(APP_PATH)
    at.query_params["n"] = "5"
    at.query_params["c"] = "99"
    at.query_params["knoten"] = "-4"
    at.query_params["typ"] = "gibt es nicht"
    at.query_params["mass"] = "Unsinn"
    at.run(timeout=TIMEOUT)
    assert not at.exception
    assert at.slider(key="n_slider").value == C.N_MIN and at.slider(key="c_slider").value == C.C_MAX and at.number_input(key="knoten_input").value == 0
    assert at.selectbox(key="netztyp_select").value == C.T_COMMUNITIES and at.selectbox(key="mass_select").value == C.M_CONSTRAINT


def test_permalink_selects_a_network_type_and_a_measure():
    at = AppTest.from_file(APP_PATH)
    at.query_params["typ"] = C.T_HUBS
    at.query_params["mass"] = C.M_BETWEENNESS
    at.run(timeout=TIMEOUT)
    assert not at.exception and at.selectbox(key="netztyp_select").value == C.T_HUBS and at.selectbox(key="mass_select").value == C.M_BETWEENNESS


def test_every_experiment_runs_and_is_invalidated_by_a_setting_change():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    at.slider(key="n_slider").set_value(C.N_MIN).run(timeout=TIMEOUT)         # kleines Netz: schnell
    for name in EXPERIMENTS:
        at.button(key=f"run_{name}").click().run(timeout=TIMEOUT)
        assert not at.exception, (name, [str(e) for e in at.exception])
    texts = " ".join(x.value for x in list(at.info) + list(at.warning) + list(at.success))
    for fragment in ("Netztypen liegt die Rangkorrelation", "überlappen zwischen", "Güte (AUC)", "Schon bei β", "Ankunftszeit", "Entropie"):
        assert fragment in texts, fragment
    at.slider(key="n_slider").set_value(C.N_MIN + 10).run(timeout=TIMEOUT)
    assert not at.exception
    assert sum("neu starten" in i.value for i in at.info) >= len(EXPERIMENTS)           # alle von n abhängigen Ergebnisse sind ungültig
