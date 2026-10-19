"""Strukturelle Löcher: ist ein Makler mehr als ein Hub? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Drittes Stück der Reihe „Netzwerkanalyse“: das Constraint und die effektive Größe nach Burt am Ego-Netz eines Knotens vorgerechnet, verglichen mit Grad, Betweenness, Nähe und Brücken,
dazu Granovetters Aussage über schwache Bindungen und der Informationsvorsprung von Maklern.
Aufbau und Regeln stehen im DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import slo_constants as C
from slo_evaluation import (
    Settings,
    analyse,
    arrival_rows,
    broker_rows,
    de,
    degree_rows,
    diversity_stats,
    granovetter_rows,
    verdict_arrival,
    verdict_broker,
    verdict_degree,
    verdict_diversity,
    verdict_granovetter,
    verdict_main,
    verdict_watts,
    watts_rows,
)
from slo_layout import dunkles_design, kopf_css
from slo_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from slo_scenario import link_stand
from slo_visualization import (
    build_arrival,
    build_broker,
    build_degree,
    build_diversity,
    build_ego,
    build_granovetter,
    build_network,
    build_profile,
    build_watts,
)

st.set_page_config(page_title="Strukturelle Löcher – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _degree(n, c):
    return degree_rows(n, c)


@st.cache_data(show_spinner=False)
def _broker(n, c):
    return broker_rows(n, c)


@st.cache_data(show_spinner=False)
def _gran(n):
    return granovetter_rows(n)


@st.cache_data(show_spinner=False)
def _watts(n):
    return watts_rows(n)


@st.cache_data(show_spinner=False)
def _arrival(n, c):
    return arrival_rows(n, c)


@st.cache_data(show_spinner=False)
def _diversity(n):
    return diversity_stats(n)


def experiment(name, label, key, compute, show, hint):
    """Teure Zusatzansicht erst auf Klick; das Ergebnis bleibt nur für genau diese Einstellungen stehen (Session State)."""
    state_key = f"exp_{name}"
    if st.button(label, key=f"run_{name}", help=hint):
        with st.spinner("Rechne …"):
            result = compute()
        st.session_state[state_key] = (key, result)
    state = st.session_state.get(state_key)
    if state is None:
        st.caption(f"Noch nicht gerechnet. {hint}")
        return
    if state[0] != key:
        st.info("Die Einstellungen haben sich seit der letzten Rechnung geändert. Bitte neu starten.")
        return
    show(state[1])


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in slo_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🕳️ Strukturelle Löcher: ist ein Makler mehr als ein Hub?")
st.markdown(
    """
**Drittes Stück** der Reihe „Netzwerkanalyse“, im Struktur-Arm die **soziale Lesart der Brücken** aus der [Brücken-Demo](https://sebastianhanisch-bridges-demo.streamlit.app/): dort fällt ein Netz bei Ausfall einer Kante auseinander, hier geht es um Betriebe, die zwischen Gruppen vermitteln, die einander sonst nicht kennen. Ein Netz von Subunternehmern und Lieferanten zeigt, wie **Burt** einen solchen **Makler** misst (Constraint, effektive Größe) und wie **Granovetter** „schwache Bindungen“ fasst (Kanten ohne gemeinsame Bekannte). Anders als die Fall-Demos zeigt diese Demo **ein** Maß an einem wachsenden Beispiel.

Die Kernfrage: **Ist ein Makler mehr als ein Knoten mit vielen Kontakten, und wann tragen Burts und Granovetters Aussagen?** Wählen Sie unten einen Knoten: die Demo rechnet sein Constraint Schritt für Schritt vor.

Weiter unten: fünf Experimente (**🔬**), der Abschnitt **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So lesen Sie die Maße", expanded=True):
    st.markdown(
        """
1. **Ego-Netz:** ein Knoten mit seinen Kontakten und den Verbindungen, die diese Kontakte untereinander haben. Sind die Kontakte untereinander **nicht** verbunden, liegen zwischen ihnen *strukturelle Löcher*; der Knoten ist der Makler, über den sie sich erreichen.
2. **Constraint (Burt):** wie stark ein Knoten in seine Nachbarschaft eingebunden ist. Jeder Kontakt bekommt den Anteil *p*<sub>ij</sub> = 1/Grad; dazu kommt der Umweg über gemeinsame Kontakte. Die **Quadrate** dieser Anteile werden addiert. Ein Makler zwischen *r* getrennten Verbünden hat 1/*r*; ein Knoten, dessen Kontakte alle einander kennen, hat viel mehr (ein Dreieck: 1,125, der Wert kann also über 1 liegen).
3. **Effektive Größe (Burt, in der Fassung von Borgatti):** Grad minus 2·*t*/Grad, wobei *t* die Zahl der Verbindungen unter den Kontakten ist: die Zahl der Kontakte ohne die Doppelungen.
4. **Überlappung einer Kante (Onnela u. a.):** die gemeinsamen Kontakte beider Enden geteilt durch alle ihre Kontakte. **Überlappung 0** heißt: kein gemeinsamer Bekannter, das ist hier die „schwache Bindung“ im Sinne Granovetters (ungewichtet, nur nach der Struktur).
5. **Brücke:** eine Kante, ohne die das Netz auseinanderfällt (aus der Brücken-Demo). Eine Kante ohne gemeinsamen Bekannten ist nicht unbedingt eine Brücke: oft gibt es einen Umweg über mehrere Schritte.
6. **Vergleichsmaße:** Grad (Zahl der Kontakte), Betweenness (Anteil der kürzesten Wege, die über den Knoten laufen), Nähe (Kehrwert des mittleren Abstands) und Clustering (Anteil der verbundenen Kontaktpaare).
        """,
        unsafe_allow_html=True,
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Netz zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Netz**")
    typ = st.selectbox("Netztyp", C.ALL_TYPES, key="netztyp_select", help="Welches Netz erzeugt oder geladen wird. Makler-Beispiel und Link-Netz sind feste Netze.")
    fixed = typ in C.FIXED_TYPES
    n = st.slider("Knoten n", *bounds("n_slider"), key="n_slider", disabled=fixed, help="Zahl der Knoten (beim Gitter auf ein Quadrat gerundet).")
    c = st.slider("Verbindungen je Knoten c", *bounds("c_slider"), key="c_slider", disabled=fixed, help="Was c bedeutet, hängt vom Netztyp ab (siehe darunter).")
    st.caption(C.C_MEANING[typ] if typ in C.C_MEANING else "Dieses Netz ist fest: n, c und Zufalls-Seed wirken hier nicht.")
    seed = st.number_input("Zufalls-Seed des Netzes", *bounds("seed_input"), key="seed_input", step=1, disabled=fixed)
    st.button("🎲 Neues Netz würfeln", width="stretch", on_click=randomize_seed, disabled=fixed)
    nav = st.selectbox("Navigationsseiten (wirkt nur beim Link-Netz)", C.NAV_CHOICES, key="nav_select",
                       help="Startseite und Kontaktseite sind mit allen Seiten verlinkt. Mitgezählt gibt es kaum strukturelle Löcher; weggelassen zeigen sich die Sammelseiten als Makler.")
    st.markdown("**Ansicht**")
    mass = st.selectbox("Knoten färben nach", C.MEASURES, key="mass_select", help="Welches Maß die Farbe der Knoten im Netz bestimmt.")
    st.caption(C.MEASURE_HELP[mass])
    knoten = st.number_input("Knoten für das Ego-Netz", *bounds("knoten_input"), key="knoten_input", step=1,
                             help="Nummer des Knotens, dessen Constraint vorgerechnet wird. Zu große Nummern werden auf den letzten Knoten begrenzt.")

sync_query_params({"netztyp_select": typ, "n_slider": int(n), "c_slider": int(c), "seed_input": int(seed), "mass_select": mass, "knoten_input": int(knoten), "nav_select": nav})

settings = Settings(typ, int(n), int(c), int(seed), mass, int(knoten), nav)
a = _analysis(settings)
if typ == C.T_LINK:
    st.info(f"Das echte Link-Netz von sebastianhanisch.net, Schnappschuss vom {link_stand()} (ungerichtet zusammengefasst): 50 Seiten und 300 Demos. Die Zahlen gelten für diesen Stand, nicht für die heutige Website.")
if int(knoten) != a.node:
    st.warning(f"Knoten {int(knoten)} gibt es in diesem Netz nicht (höchste Nummer {a.inst.n - 1}); gezeigt wird Knoten {a.node}.")
name = a.inst.labels[a.node] if a.inst.labels else str(a.node)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Das Netz und sein Ego-Netz")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Knoten / Kanten", f"{a.inst.n} / {a.inst.m}")
m2.metric("Brückenkanten", len(a.bridges))
m3.metric("Knoten ohne Kontakt", a.inst.n - a.valid)
m4.metric("Rangkorrelation Constraint ~ Grad", de(a.stats["c_deg"], 2))
left, right = st.columns([5, 4])
left.markdown(f"**Netz, gefärbt nach: {mass}** (rot umrandet: Knoten {name}; orange: Brückenkanten)")
left.plotly_chart(build_network(a.inst, a.tab[mass], mass, a.bridges, a.node), width="stretch", key="net_chart")
right.markdown(f"**Ego-Netz von Knoten {name}** ({len(a.inst.adj[a.node])} Kontakte)")
right.plotly_chart(build_ego(a.inst, a.node, a.terms), width="stretch", key="ego_chart")
right.caption("Farbe der Kontakte: ihr Beitrag zum Constraint (Quadrat der Summe aus direktem und indirektem Anteil). Grüne Linien: Kontakte, die einander kennen.")

st.markdown(f"### Der Rechenweg des Constraints von Knoten {name}")
if a.terms:
    rows = []
    for j, direct, indirect, total, square in a.terms:
        label = a.inst.labels[j] if a.inst.labels else str(j)
        rows.append({
            "Kontakt j": label, "Grad von j": len(a.inst.adj[j]), "direkter Anteil p_ij": de(direct, 3),
            "indirekt über gemeinsame Kontakte q (p_iq · p_qj)": ", ".join(f"{a.inst.labels[q] if a.inst.labels else q}: {de(t, 3)}" for q, t in indirect) or "–",
            "Summe": de(total, 3), "Quadrat": de(square, 3),
        })
    st.dataframe(rows, hide_index=True, width="stretch", height=min(420, 36 * (len(rows) + 1) + 3))
    cval = a.tab[C.M_CONSTRAINT][a.node]
    st.markdown(f"**Constraint = Summe der Quadrate = {de(cval, 3)}.** Effektive Größe: {de(a.tab[C.M_EFFSIZE][a.node], 2)} (bei {len(a.inst.adj[a.node])} Kontakten).")
else:
    st.info("Dieser Knoten hat keine Kontakte: sein Constraint ist nicht definiert.")
st.markdown("**Wo steht der Knoten unter allen?**")
st.plotly_chart(build_profile(a.profile), width="stretch", key="profile_chart")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Ist ein Makler mehr als ein Knoten mit vielen Kontakten?")
kind, text = verdict_main(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

n_exp, c_exp = settings.n, settings.c
st.subheader("🔬 Experiment 1: Ist das Constraint ein Gradmaß?")
st.caption(f"Rangkorrelation (Spearman) des Constraints mit Grad und effektiver Größe, dazu bei festem Grad mit dem Clustering. Median über {len(C.LIVE_SEEDS)} feste Netze je Netztyp, n = {n_exp}, c = {c_exp} (Seitenleiste).")


def show_degree(rows):
    st.plotly_chart(build_degree(rows), width="stretch", key="degree_chart")
    st.dataframe([{"Netztyp": r["typ"], "Constraint ~ Grad": de(r["c_deg"], 2), "Constraint ~ eff. Größe": de(r["c_eff"], 2), "Constraint ~ Betweenness": de(r["c_bet"], 2),
                   "Constraint ~ Betweenness (Grad fest)": de(r["c_bet_deg"], 2), "Constraint ~ Clustering (Grad fest)": de(r["c_clu_deg"], 2)} for r in rows], hide_index=True, width="stretch")
    kind_, text_ = verdict_degree(rows)
    getattr(st, kind_)(text_)


experiment("degree", "Netztypen vergleichen", (n_exp, c_exp), lambda: _degree(n_exp, c_exp), show_degree, "Rechnet sieben Netztypen mit je vier Netzen, wenige Sekunden.")

st.markdown("---")

st.subheader("🔬 Experiment 2: Wer ist Makler, und sind Brücken Makler?")
st.caption(f"Überlappung (Jaccard) der Top-5-%-Mengen je Maß; Brücken, die keine Blätter anbinden (beide Enden mit mindestens zwei Kontakten), mit dem Perzentil ihrer Enden beim Constraint und beim Grad. "
           f"n = {n_exp}, c = {c_exp}. Bei c = 3 haben auch Zufallsnetze Brücken.")


def show_broker(rows):
    st.plotly_chart(build_broker(rows), width="stretch", key="broker_chart")
    st.dataframe([{"Netztyp": r["typ"], "Brücken": de(r["bridges"], 0), "davon ohne Blatt": de(r["bridges_inner"], 0), "Perzentil Constraint": de(r["perc_c"], 2), "Perzentil Grad": de(r["perc_d"], 2),
                   "Gleichstände am Rand": de(r["ties"], 0)} for r in rows], hide_index=True, width="stretch")
    kind_, text_ = verdict_broker(rows)
    getattr(st, kind_)(text_)


experiment("broker", "Makler vergleichen", (n_exp, c_exp), lambda: _broker(n_exp, c_exp), show_broker, "Rechnet sieben Netztypen mit je vier Netzen, wenige Sekunden.")

st.markdown("---")

st.subheader("🔬 Experiment 3: Verbinden schwache Bindungen die Verbünde?")
st.caption(f"Teil a: Verbundnetz (sechs Verbünde, 80 % der Kanten innen), n = {n_exp}, bei dünner, mittlerer und dichter Vernetzung (c = 6, 10, 16). Teil b: Ring mit je {C.WS_K} Nachbarn und zunehmend umverdrahteten Kanten (Watts und Strogatz).")


def show_gran(rows):
    st.plotly_chart(build_granovetter(rows), width="stretch", key="gran_chart")
    kind_, text_ = verdict_granovetter(rows)
    getattr(st, kind_)(text_)


def show_watts(rows):
    st.plotly_chart(build_watts(rows), width="stretch", key="watts_chart")
    st.dataframe([{"β": de(r["beta"], 2), "Clustering": de(r["clustering"], 3), "Anteil Kanten ohne gemeinsamen Nachbarn": de(r["zero"], 3), "mittleres Constraint": de(r["constraint"], 3),
                   "mittlere Pfadlänge": de(r["path"], 1)} for r in rows], hide_index=True, width="stretch")
    kind_, text_ = verdict_watts(rows)
    getattr(st, kind_)(text_)


experiment("gran", "Teil a rechnen", n_exp, lambda: _gran(n_exp), show_gran, "Rechnet drei Dichten mit je vier Netzen.")
experiment("watts", "Teil b rechnen", n_exp, lambda: _watts(n_exp), show_watts, "Rechnet sechs Umverdrahtungsanteile mit je vier Netzen.")

st.markdown("---")

st.subheader("🔬 Experiment 4: Erfahren Makler Neuigkeiten früher?")
st.caption(f"Eine Nachricht startet an {C.ARR_SOURCES} zufälligen Knoten und springt je Schritt mit Wahrscheinlichkeit {de(C.SI_P, 1)} über jeden Kontakt (SI in diskreter Zeit, {C.ARR_RUNS} Läufe je Quelle). "
           f"Gezeigt wird der Betrag der Rangkorrelation der mittleren Ankunftszeit mit dem jeweiligen Maß; n = {n_exp}, c = {c_exp}.")


def show_arrival(rows):
    st.plotly_chart(build_arrival(rows), width="stretch", key="arrival_chart")
    st.dataframe([{"Netztyp": r["typ"], "Zeit ~ Constraint": de(r["t_c"], 2), "Zeit ~ Grad": de(r["t_d"], 2), "Zeit ~ Nähe": de(r["t_l"], 2), "Zeit ~ eff. Größe": de(r["t_e"], 2),
                   "Constraint bei festem Grad": de(r["pc_d"], 2), "Constraint bei fester Nähe": de(r["pc_l"], 2)} for r in rows], hide_index=True, width="stretch")
    kind_, text_ = verdict_arrival(rows)
    getattr(st, kind_)(text_)


experiment("arrival", "Ausbreitung rechnen", (n_exp, c_exp), lambda: _arrival(n_exp, c_exp), show_arrival, "Rechnet fünf Netztypen mit je vier Netzen und 120 Läufen, einige Sekunden.")

st.markdown("---")

st.subheader("🔬 Experiment 5: Haben Makler eine vielfältigere Nachbarschaft?")
st.caption(f"Verbundnetz (sechs Verbünde), n = {n_exp}, c = {C.DIVERSITY_C}: für jeden Knoten die Zahl der verschiedenen Verbünde unter seinen Kontakten und die Entropie ihrer Anteile.")


def show_diversity(stats):
    st.plotly_chart(build_diversity(stats), width="stretch", key="diversity_chart")
    kind_, text_ = verdict_diversity(stats)
    getattr(st, kind_)(text_)


experiment("diversity", "Vielfalt rechnen", n_exp, lambda: _diversity(n_exp), show_diversity, "Rechnet vier Netze.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Ungewichtet, ungerichtet** | Burt rechnet mit Gewichten (Zeit, Umsatz): das gewichtete Constraint ist ein anderer Wert. Hier zählt jeder Kontakt gleich, Granovetters „Stärke“ ist nur die Struktur (Überlappung), nicht die Dauer oder Häufigkeit. | – |
| **Blätter zählen als Löcher** | Ein Hub mit drei Kontakten, die sonst niemanden kennen, hat im Makler-Beispiel ein *kleineres* Constraint als der Makler zwischen drei Verbünden: das Maß unterscheidet nicht, ob die Kontakte etwas wert sind. | – |
| **Synthetische Netze mit bekannten Verbünden** | „Verbund“ ist die geplante Einteilung des Generators. In echten Netzen gibt es keine Wahrheit; die Zahlen gelten für diese Netztypen bei diesen Größen (Median über feste Netze). | Stück 2 (Blockmodell) |
| **Rangkorrelation bei vielen gleichen Graden** | Im Gitter und im Ring haben fast alle Knoten denselben Grad: Rangkorrelationen und Top-5-%-Mengen hängen dann an Gleichständen (Regel: kleinere Knotennummer) und sind unscharf. Die Demo meldet es. | – |
| **Ausbreitung: SI mit gleicher Wahrscheinlichkeit** | Der Informationsvorsprung ist ein Modellbefund (jeder Kontakt gleich wahrscheinlich, keine Verzögerung, keine Gegenkräfte). Er sagt nichts über echte Nachrichten. | Stück 5, Stück 13 |
| **Link-Netz als Sonderfall** | Seiten und Demos verlinken sich nach Navigationsregeln, nicht nach Beziehungen. Es dient als Prüfstein, nicht als Beleg für soziale Netze. | – |
| **Kausalität** | Ob Makler tatsächlich mehr Erfolg haben, zeigen Experimente an echten Personen, nicht diese Messungen. Rajkumar u. a. (2022) fanden bei LinkedIn einen umgekehrt U-förmigen Zusammenhang zwischen Bindungsstärke und Stellenvermittlung, der von der Branche abhängt; die Demo bildet das **nicht** nach. | – |
| **Kritik am Constraint** | Eine Arbeit von 2024 (Strategy Science) kritisiert, dass das Constraint Dreiecksbegriffe nicht verlässlich erfasst (Inhalt nicht gelesen). Die Demo zeigt nur, dass es vom Grad der Nachbarn **im Dreieck** abhängt (Rechenweg oben). | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Anteil eines Kontakts.** Für den Knoten $i$ mit Kontakten $N(i)$ und Grad $d_i$ ist (ungewichtet)

$$p_{ij} = \frac{1}{d_i} \quad (j \in N(i))$$

**Constraint** (Burt):

$$C_i = \sum_{j \in N(i)} \Bigl( p_{ij} + \sum_{q \ne i,j} p_{iq}\, p_{qj} \Bigr)^2$$

Ein Makler zwischen $r$ getrennten Verbünden mit je einem Kontakt hat $C_i = r \cdot (1/r)^2 = 1/r$.

**Effektive Größe** (Borgatti 1997 für ungewichtete, ungerichtete Netze; $t_i$ = Zahl der Kanten zwischen den Kontakten von $i$):

$$\mathrm{ES}_i = d_i - \frac{2\, t_i}{d_i}$$

**Überlappung einer Kante** $\{i, j\}$:

$$O_{ij} = \frac{|N(i) \cap N(j)|}{|(N(i) \cup N(j)) \setminus \{i, j\}|}$$

**Rangkorrelation** (Spearman, Mittelwertränge bei Gleichstand): die Pearson-Korrelation der Ränge,

$$\rho_{xy} = \mathrm{corr}\bigl(\mathrm{rang}(x), \mathrm{rang}(y)\bigr)$$

**Partielle Rangkorrelation** bei festem $z$:

$$\rho_{xy \cdot z} = \frac{\rho_{xy} - \rho_{xz}\, \rho_{yz}}{\sqrt{(1 - \rho_{xz}^2)(1 - \rho_{yz}^2)}}$$

**Güte (AUC)**, mit der ein Wert $S$ zwei Klassen trennt:

$$\mathrm{AUC} = P(S_+ > S_-) + \tfrac{1}{2}\, P(S_+ = S_-)$$

**Vielfalt der Nachbarschaft** (Entropie der Anteile $q_b$ der Kontakte in Verbund $b$):

$$H_i = -\sum_b q_b \ln q_b$$

**Literatur.**
- Burt, R. S. (1992): *Structural Holes: The Social Structure of Competition.* Harvard University Press. (Constraint und effektive Größe.)
- Burt, R. S. (2004): *Structural Holes and Good Ideas.* American Journal of Sociology 110(2), 349–399.
- Borgatti, S. P. (1997): *Structural holes: Unpacking Burt's redundancy measures.* Connections 20(1), 35–38. (Vereinfachte effektive Größe; hier über die Dokumentation von networkx geprüft.)
- Granovetter, M. S. (1973): *The Strength of Weak Ties.* American Journal of Sociology 78(6), 1360–1380.
- Onnela, J.-P. u. a. (2007): *Structure and tie strengths in mobile communication networks.* PNAS 104(18), 7332–7336. (Überlappung der Nachbarschaften; die genaue Formel im Original nicht gelesen, hier wie im Text oben umgesetzt.)
- Watts, D. J., Strogatz, S. H. (1998): *Collective dynamics of ‘small-world’ networks.* Nature 393, 440–442.
- Rajkumar, K., Saint-Jacques, G., Bojinov, I., Brynjolfsson, E., Aral, S. (2022): *A causal test of the strength of weak ties.* Science 377, 1304–1310.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
