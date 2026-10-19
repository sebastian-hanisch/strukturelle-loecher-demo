"""Kennzahlen, Sweeps und Verdikte der Demo „Strukturelle Löcher“. Verdikte sind reine Funktionen (Art, Text); jede Zahl im Text kommt aus der Rechnung.

Rangkorrelationen sind Spearman-Werte über alle Knoten mit mindestens einem Kontakt (Knoten ohne Kontakt haben kein Constraint). Jede Messreihe nimmt
den Median über feste Netze (`LIVE_SEEDS` in der App, `SWEEP_SEEDS` für die README-Zahlen): nie ein einzelner Seed als Befund."""

import math
import random
from dataclasses import dataclass
from statistics import median

import numpy as np

import slo_algorithm as A
import slo_constants as C
from slo_scenario import BROKER_HUB, BROKER_MAKLER, Instance, communities_of, make_instance, watts_strogatz_instance

NAN = float("nan")


def de(x, digits=1) -> str:
    """Dezimalzahl mit Komma (deutsche Texte); eine nicht definierte Zahl erscheint als Gedankenstrich."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return f"{x:.{digits}f}".replace(".", ",")


def _med(values) -> float:
    vals = [v for v in values if not math.isnan(v)]
    return float(median(vals)) if vals else NAN


# --- Maße eines Netzes ------------------------------------------------------------------------------------------------------------------------------


def measure_table(adj) -> dict:
    """Alle sechs Maße je Knoten (Listen der Länge n); Knoten ohne Kontakt haben bei Constraint und effektiver Größe `nan`."""
    return {
        C.M_CONSTRAINT: A.constraint(adj),
        C.M_EFFSIZE: A.effective_size(adj),
        C.M_DEGREE: [float(d) for d in A.degrees(adj)],
        C.M_BETWEENNESS: A.betweenness(adj),
        C.M_CLOSENESS: A.closeness(adj),
        C.M_CLUSTERING: A.clustering(adj),
    }


def _valid(adj) -> list:
    return [i for i, d in enumerate(A.degrees(adj)) if d > 0]


def _pick(values, idx):
    return [values[i] for i in idx]


def rank_stats(adj, tab=None) -> dict:
    """Rangkorrelationen des Constraints mit den einfachen Maßen und die partiellen Korrelationen bei festem Grad (nur Knoten mit Kontakt)."""
    tab = tab or measure_table(adj)
    idx = _valid(adj)
    c, e, d, b, k = (_pick(tab[m], idx) for m in (C.M_CONSTRAINT, C.M_EFFSIZE, C.M_DEGREE, C.M_BETWEENNESS, C.M_CLUSTERING))
    return {
        "c_deg": A.spearman(c, d), "c_eff": A.spearman(c, e), "eff_deg": A.spearman(e, d), "c_bet": A.spearman(c, b), "c_clu": A.spearman(c, k),
        "c_bet_deg": A.partial_spearman(c, b, d), "c_clu_deg": A.partial_spearman(c, k, d),
    }


def top_sets(adj, tab=None) -> dict:
    """Die Top-5-%-Mengen: niedriges Constraint, hohe effektive Größe, hohe Betweenness, hoher Grad; dazu die Zahl der Gleichstände am Rand je Maß."""
    tab = tab or measure_table(adj)
    n_valid = len(_valid(adj))
    k = max(1, round(C.TOP_FRACTION * n_valid)) if n_valid else 0
    out = {"k": k}
    for key, mass, largest in (("c", C.M_CONSTRAINT, False), ("e", C.M_EFFSIZE, True), ("b", C.M_BETWEENNESS, True), ("d", C.M_DEGREE, True)):
        deg = A.degrees(adj)
        values = [v if deg[i] > 0 else NAN for i, v in enumerate(tab[mass])]
        out[key], out[key + "_ties"] = A.top_set(values, k, largest)
    return out


# --- Hauptanalyse -----------------------------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Settings:
    netztyp: str = C.T_COMMUNITIES
    n: int = C.DEFAULT_N
    c: int = C.DEFAULT_C
    seed: int = C.DEFAULT_SEED
    mass: str = C.M_CONSTRAINT
    knoten: int = C.DEFAULT_KNOTEN
    nav: str = C.NAV_COUNT


@dataclass(frozen=True, eq=False)
class Analysis:
    inst: Instance
    tab: dict                 # Maß -> Liste je Knoten
    bridges: list             # Brückenkanten (a < b)
    node: int                 # das gewählte Knoten (auf n - 1 begrenzt)
    terms: list               # Rechenweg des Constraints am gewählten Knoten (ego_terms)
    profile: list             # (Maß, Wert, Anteil der Knoten mit besserem Wert) am gewählten Knoten
    stats: dict               # rank_stats
    tops: dict                # top_sets
    jac_cd: float             # Überlappung der Top-5-%-Mengen: niedriges Constraint gegen hoher Grad
    jac_cb: float             # niedriges Constraint gegen hohe Betweenness
    valid: int                # Zahl der Knoten mit mindestens einem Kontakt


def clamp_node(knoten, n) -> int:
    return max(0, min(int(knoten), n - 1))


def node_profile(tab, node) -> list:
    """Wo steht der Knoten unter allen? Anteil der Knoten mit echt besserem Wert (0 = bester), beim Constraint zählt klein als besser."""
    rows = []
    for mass, largest in ((C.M_DEGREE, True), (C.M_CONSTRAINT, False), (C.M_EFFSIZE, True), (C.M_BETWEENNESS, True), (C.M_CLOSENESS, True), (C.M_CLUSTERING, True)):
        rows.append((mass, tab[mass][node], A.share_better(tab[mass], node, largest)))
    return rows


def analyse(settings: Settings) -> Analysis:
    inst = make_instance(settings.netztyp, settings.n, settings.c, settings.seed, settings.nav)
    tab = measure_table(inst.adj)
    node = clamp_node(settings.knoten, inst.n)
    tops = top_sets(inst.adj, tab)
    return Analysis(inst, tab, A.bridges(inst.adj), node, A.ego_terms(inst.adj, node), node_profile(tab, node), rank_stats(inst.adj, tab), tops,
                    A.jaccard(tops["c"], tops["d"]), A.jaccard(tops["c"], tops["b"]), len(_valid(inst.adj)))


def tie_note(a: Analysis) -> str:
    ties = max(a.tops["c_ties"], a.tops["d_ties"], a.tops["b_ties"])
    if ties <= 0:
        return ""
    return (f" Hinweis: am Rand der Top-5-%-Auswahl liegen bis zu {ties} weitere Knoten gleichauf; die Auswahl folgt dort der Regel „kleinere Knotennummer“, der Vergleich ist unscharf.")


def verdict_main(a: Analysis) -> tuple[str, str]:
    """Verdikt der Kernfrage: ist ein Makler (niedriges Constraint) mehr als ein Knoten mit vielen Kontakten?"""
    if a.inst.m == 0 or a.valid < 3:
        return "warning", "Das Netz hat zu wenige Kanten: es gibt nichts zu vergleichen."
    cons, deg = a.tab[C.M_CONSTRAINT], a.tab[C.M_DEGREE]
    if a.tops["k"] < 3:
        low = min((i for i in range(a.inst.n) if not math.isnan(cons[i])), key=lambda i: cons[i])
        text = (f"Das Netz ist zu klein für Top-5-%-Mengen ({a.valid} Knoten mit Kontakt). Das niedrigste Constraint hat Knoten {low} ({de(cons[low], 3)}, Grad {de(deg[low], 0)}); "
                f"Constraint und Grad: ρ = {de(a.stats['c_deg'], 2)}.")
        if a.inst.typ == C.T_BROKER:
            text += (f" Der Makler (Knoten {BROKER_MAKLER}, drei Kontakte in drei Verbünden) hat {de(cons[BROKER_MAKLER], 3)}, der Hub (Knoten {BROKER_HUB}, {de(deg[BROKER_HUB], 0)} Kontakte, davon drei Blätter) "
                     f"{de(cons[BROKER_HUB], 3)}: das Constraint zählt auch Blätter als Löcher.")
        return "info", text
    if max(a.tops["c_ties"], a.tops["d_ties"], a.tops["b_ties"]) >= a.tops["k"]:
        return "warning", ("Die Maße trennen hier nicht: in der Top-5-%-Auswahl liegen mindestens so viele Knoten gleichauf wie ausgewählt werden "
                           f"({a.tops['k']}), die Auswahl folgt der Regel „kleinere Knotennummer“. Constraint und Grad: ρ = {de(a.stats['c_deg'], 2)} (viele gleiche Grade, die Rangkorrelation ist unscharf).")
    rho = a.stats["c_deg"]
    clu = a.stats["c_clu_deg"]
    clu_txt = f" Bei festem Grad hängt das Constraint mit dem Clustering mit ρ = {de(clu, 2)} zusammen." if not math.isnan(clu) else ""
    if math.isnan(rho):
        return "warning", ("Alle Knoten haben denselben Grad (oder fast): die Rangkorrelation von Constraint und Grad ist nicht definiert. "
                           f"Die Top-5-%-Mengen von niedrigem Constraint und hohem Grad überlappen zu {de(a.jac_cd, 2)} (Jaccard)." + tie_note(a))
    base = f"Constraint und Grad: ρ = {de(rho, 2)}; die Top-5-%-Mengen (niedriges Constraint, hoher Grad) überlappen zu {de(a.jac_cd, 2)}, (niedriges Constraint, hohe Betweenness) zu {de(a.jac_cb, 2)}."
    if abs(rho) >= 0.9 and a.jac_cd >= 0.7:
        return "warning", "In diesem Netz ist ein Makler **fast ein Knoten mit vielen Kontakten**. " + base + clu_txt + tie_note(a)
    if a.jac_cd < 0.6:
        return "success", "In diesem Netz wählen Constraint und Grad **verschiedene Knoten**: der Makler ist mehr als ein Hub. " + base + clu_txt + tie_note(a)
    return "info", "Constraint und Grad stimmen hier teilweise überein. " + base + clu_txt + tie_note(a)


# --- E1: Constraint gegen Grad über die Netztypen ----------------------------------------------------------------------------------------------------


def _types_for_sweeps():
    return C.GENERATED_TYPES


def degree_rows(n, c, types=None, seeds=C.LIVE_SEEDS) -> list[dict]:
    """Rangkorrelationen je Netztyp, Median über die festen Netze."""
    rows = []
    for typ in types or _types_for_sweeps():
        stats = []
        for seed in seeds:
            inst = make_instance(typ, n, c, seed, layout=False)
            if inst.m > 0:
                stats.append(rank_stats(inst.adj))
        rows.append({"typ": typ, **{key: _med([s[key] for s in stats]) for key in ("c_deg", "c_eff", "eff_deg", "c_bet", "c_clu", "c_bet_deg", "c_clu_deg")}})
    return rows


def verdict_degree(rows: list[dict]) -> tuple[str, str]:
    """Verdikt zu E1: wie nah ist das Constraint an einem Gradmaß, und was bleibt bei festem Grad?"""
    valid = [r for r in rows if not math.isnan(r["c_deg"])]
    if not valid:
        return "warning", "In keinem Netz lässt sich die Rangkorrelation von Constraint und Grad bilden (alle Grade gleich)."
    near = [r for r in valid if r["c_deg"] <= -0.9]
    far = min(valid, key=lambda r: abs(r["c_deg"]))
    clu = [r["c_clu_deg"] for r in valid if not math.isnan(r["c_clu_deg"])]
    clu_txt = f" Bei festem Grad bleibt eine Verbindung zum Clustering (partielle Rangkorrelation {de(min(clu), 2)} bis {de(max(clu), 2)})." if clu else ""
    return "info", (f"In {len(near)} von {len(valid)} Netztypen liegt die Rangkorrelation von Constraint und Grad bei −0,9 oder darunter: das Constraint ist dort **fast ein Gradmaß**. "
                    f"Am weitesten davon entfernt ist „{far['typ']}“ mit ρ = {de(far['c_deg'], 2)}." + clu_txt)


# --- E2: Wer ist Makler? ------------------------------------------------------------------------------------------------------------------------------


def broker_rows(n, c, types=None, seeds=C.LIVE_SEEDS) -> list[dict]:
    """Überlappung der Top-5-%-Mengen und Rolle der Brücken je Netztyp, Median über die festen Netze.
    Brücken ohne Blatt: beide Enden haben mindestens zwei Kontakte; ihr Constraint-Perzentil wird mit dem Grad-Perzentil verglichen (0 = bester Wert)."""
    rows = []
    for typ in types or _types_for_sweeps():
        recs = []
        for seed in seeds:
            inst = make_instance(typ, n, c, seed, layout=False)
            if inst.m == 0:
                continue
            tab = measure_table(inst.adj)
            tops = top_sets(inst.adj, tab)
            deg = A.degrees(inst.adj)
            br = A.bridges(inst.adj)
            inner = [(a, b) for a, b in br if deg[a] >= 2 and deg[b] >= 2]
            ends = sorted({x for e in inner for x in e})
            recs.append({
                "j_cb": A.jaccard(tops["c"], tops["b"]), "j_cd": A.jaccard(tops["c"], tops["d"]), "j_ed": A.jaccard(tops["e"], tops["d"]), "j_bd": A.jaccard(tops["b"], tops["d"]),
                "bridges": float(len(br)), "bridges_inner": float(len(inner)),
                "perc_c": _med([A.share_better(tab[C.M_CONSTRAINT], v, False) for v in ends]) if ends else NAN,
                "perc_d": _med([A.share_better(tab[C.M_DEGREE], v, True) for v in ends]) if ends else NAN,
                "ties": float(max(tops["c_ties"], tops["d_ties"], tops["b_ties"], tops["e_ties"])),
            })
        rows.append({"typ": typ, **{key: _med([r[key] for r in recs]) for key in ("j_cb", "j_cd", "j_ed", "j_bd", "bridges", "bridges_inner", "perc_c", "perc_d", "ties")}})
    return rows


def verdict_broker(rows: list[dict]) -> tuple[str, str]:
    """Verdikt zu E2: wählen die Maße verschiedene Knoten, und sind Brücken Makler?"""
    valid = [r for r in rows if not math.isnan(r["j_cd"])]
    if not valid:
        return "warning", "Keine Überlappung berechenbar (Netze ohne Kanten)."
    low = min(valid, key=lambda r: r["j_cd"])
    high = max(valid, key=lambda r: r["j_cd"])
    with_bridges = [r for r in valid if not math.isnan(r["perc_c"])]
    bridge_txt = ""
    if with_bridges:
        r = max(with_bridges, key=lambda x: x["bridges_inner"])
        bridge_txt = (f" Brücken führen meist zu Blättern: im Netztyp „{r['typ']}“ sind von {de(r['bridges'], 0)} Brücken nur {de(r['bridges_inner'], 0)} Brücken zwischen Knoten mit mindestens zwei Kontakten, "
                      f"und deren Enden stehen beim Constraint im Perzentil {de(r['perc_c'], 2)}, beim Grad im Perzentil {de(r['perc_d'], 2)} (0 = bester Wert).")
    tie = max((r["ties"] for r in valid if not math.isnan(r["ties"])), default=0.0)
    tie_txt = f" In Netzen mit vielen gleichen Graden (Gitter, Ring) hängt die Auswahl an Gleichständen (bis zu {de(tie, 0)} Knoten am Rand)." if tie >= 1 else ""
    return "info", (f"Die Top-5-%-Mengen von niedrigem Constraint und hohem Grad überlappen zwischen {de(low['j_cd'], 2)} („{low['typ']}“) und {de(high['j_cd'], 2)} („{high['typ']}“) (Jaccard)." + bridge_txt + tie_txt)


# --- E3: Granovetter und Watts-Strogatz ---------------------------------------------------------------------------------------------------------------


def granovetter_rows(n, degrees=C.GRAN_DEGREES, seeds=C.LIVE_SEEDS) -> list[dict]:
    """Verbundnetz (sechs Verbünde, 80 % innen) bei verschiedenem mittlerem Grad: Anteil der Kanten ohne gemeinsamen Nachbarn innerhalb und zwischen den Verbünden,
    Güte (AUC) von „kleine Überlappung sagt eine Kante zwischen Verbünden voraus“, Anteil echter Brücken. Median über die festen Netze."""
    rows = []
    group = communities_of(n, C.BLOCKS)
    for c in degrees:
        recs = []
        for seed in seeds:
            inst = make_instance(C.T_COMMUNITIES, n, c, seed, layout=False)
            inner, between = [], []
            for a, b in A.edges_of(inst.adj):
                (inner if group[a] == group[b] else between).append(A.edge_overlap(inst.adj, a, b))
            if not inner or not between:
                continue
            recs.append({"zero_inner": float(np.mean(np.array(inner) == 0)), "zero_between": float(np.mean(np.array(between) == 0)),
                         "auc": A.auc([-x for x in between], [-x for x in inner]), "bridge_share": len(A.bridges(inst.adj)) / inst.m,
                         "between_share": len(between) / (len(between) + len(inner))})
        rows.append({"c": c, **{key: _med([r[key] for r in recs]) for key in ("zero_inner", "zero_between", "auc", "bridge_share", "between_share")}})
    return rows


def verdict_granovetter(rows: list[dict]) -> tuple[str, str]:
    """Verdikt zu E3a: hängt Granovetters Aussage von der Dreiecksdichte ab?"""
    valid = [r for r in rows if not math.isnan(r["auc"])]
    if len(valid) < 2:
        return "warning", "Zu wenige Netze mit Kanten innerhalb und zwischen den Verbünden."
    first, last = valid[0], valid[-1]
    listing = ", ".join(f"c = {r['c']}: {de(r['auc'], 2)}" for r in valid)
    return "info", (f"Die Güte (AUC), mit der „keine gemeinsamen Nachbarn“ eine Kante **zwischen** Verbünden erkennt, steigt mit der Dreiecksdichte: {listing}. "
                    f"Bei c = {first['c']} haben {de(100 * first['zero_inner'], 0)} % der Kanten **innerhalb** eines Verbunds keinen gemeinsamen Nachbarn, bei c = {last['c']} nur {de(100 * last['zero_inner'], 0)} % "
                    f"(zwischen den Verbünden {de(100 * last['zero_between'], 0)} %). Echte Brücken sind selten (Anteil der Kanten {de(100 * last['bridge_share'], 1)} %).")


def watts_rows(n, betas=C.WS_BETAS, k=C.WS_K, seeds=C.LIVE_SEEDS) -> list[dict]:
    """Watts-Strogatz-Ring (n, k) bei steigender Umverdrahtung β: Clustering, Anteil der Kanten ohne gemeinsamen Nachbarn, mittleres Constraint und mittlere Pfadlänge."""
    rows = []
    for beta in betas:
        recs = []
        for seed in seeds:
            inst = watts_strogatz_instance(n, k, beta, seed)
            ov = [A.edge_overlap(inst.adj, a, b) for a, b in A.edges_of(inst.adj)]
            cons = [x for x in A.constraint(inst.adj) if not math.isnan(x)]
            recs.append({"clustering": float(np.mean(A.clustering(inst.adj))), "zero": float(np.mean(np.array(ov) == 0)) if ov else NAN,
                         "constraint": float(np.mean(cons)) if cons else NAN, "path": A.mean_path_length(inst.adj)})
        rows.append({"beta": beta, **{key: _med([r[key] for r in recs]) for key in ("clustering", "zero", "constraint", "path")}})
    return rows


def verdict_watts(rows: list[dict]) -> tuple[str, str]:
    """Verdikt zu E3b: verkürzen wenige Abkürzungen die Wege, ohne die Dreiecke zu zerstören?"""
    base = next((r for r in rows if r["beta"] == 0), None)
    few = next((r for r in rows if r["beta"] > 0), None)
    full = rows[-1]
    if base is None or few is None or few is full:
        return "warning", "Für den Vergleich braucht es β = 0, eine kleine Umverdrahtung und β = 1."
    return "info", (f"Schon bei β = {de(few['beta'], 2)} sinkt die mittlere Pfadlänge von {de(base['path'], 1)} auf {de(few['path'], 1)}, während das Clustering von {de(base['clustering'], 2)} nur auf {de(few['clustering'], 2)} fällt. "
                    f"Bei β = {de(full['beta'], 1)} haben {de(100 * full['zero'], 0)} % der Kanten keinen gemeinsamen Nachbarn (Clustering {de(full['clustering'], 2)}, mittleres Constraint {de(full['constraint'], 2)} gegen {de(base['constraint'], 2)} beim regelmäßigen Ring).")


# --- E4: Informationsvorsprung ------------------------------------------------------------------------------------------------------------------------


def arrival_rows(n, c, types=C.ARR_TYPES, seeds=C.LIVE_SEEDS, sources=C.ARR_SOURCES, runs=C.ARR_RUNS, p=C.SI_P) -> list[dict]:
    """Rangkorrelation der mittleren Ankunftszeit (SI, Ansteckung p je Schritt und Kontakt) mit Constraint, Grad, Nähe und effektiver Größe und partielle Korrelation des Constraints
    bei festem Grad bzw. fester Nähe; auf der größten Komponente jedes Netzes, Median über die festen Netze."""
    rows = []
    for typ in types:
        recs = []
        for seed in seeds:
            inst = make_instance(typ, n, c, seed, layout=False)
            sub, _ = A.largest_component(inst.adj)
            if len(sub) < 8:
                continue
            tab = measure_table(sub)
            rng = random.Random(int(seed) * 7919 + 5)
            srcs = sorted(rng.sample(range(len(sub)), min(sources, len(sub))))
            t = A.arrival_times(sub, p, srcs, runs, seed)
            idx = [i for i, x in enumerate(t) if not math.isnan(x)]
            tt, cc, dd, ll, ee = (_pick(v, idx) for v in (t, tab[C.M_CONSTRAINT], tab[C.M_DEGREE], tab[C.M_CLOSENESS], tab[C.M_EFFSIZE]))
            recs.append({"t_c": A.spearman(tt, cc), "t_d": A.spearman(tt, dd), "t_l": A.spearman(tt, ll), "t_e": A.spearman(tt, ee),
                         "pc_d": A.partial_spearman(tt, cc, dd), "pc_l": A.partial_spearman(tt, cc, ll)})
        rows.append({"typ": typ, **{key: _med([r[key] for r in recs]) for key in ("t_c", "t_d", "t_l", "t_e", "pc_d", "pc_l")}})
    return rows


def verdict_arrival(rows: list[dict]) -> tuple[str, str]:
    """Verdikt zu E4: bekommen Makler Information früher, und ist das mehr als ein Effekt der Nähe?"""
    valid = [r for r in rows if not math.isnan(r["t_c"]) and not math.isnan(r["t_l"])]
    if not valid:
        return "warning", "Keine Ankunftszeiten berechenbar (Netze zu klein)."
    earlier = [r for r in valid if r["t_c"] > 0]
    closer = [r for r in valid if abs(r["t_l"]) > abs(r["t_c"])]
    lo = min(r["t_c"] for r in valid)
    hi = max(r["t_c"] for r in valid)
    res = [r["pc_l"] for r in valid if not math.isnan(r["pc_l"])]
    rest = f" Bei fester Nähe bleibt vom Constraint ein Rest (partiell {de(min(res), 2)} bis {de(max(res), 2)})." if res else ""
    return "info", (f"Knoten mit niedrigem Constraint erfahren Neuigkeiten in {len(earlier)} von {len(valid)} Netztypen früher (Rangkorrelation Ankunftszeit ~ Constraint {de(lo, 2)} bis {de(hi, 2)}). "
                    f"Die Nähe sagt die Ankunftszeit in {len(closer)} von {len(valid)} Netztypen besser voraus als das Constraint." + rest)


# --- E5: Vielfalt der Nachbarschaft -------------------------------------------------------------------------------------------------------------------


def diversity_stats(n, c=C.DIVERSITY_C, seeds=C.LIVE_SEEDS) -> dict:
    """Verbundnetz: Zahl der verschiedenen Verbünde unter den Kontakten und die Entropie der Anteile je Knoten gegen effektive Größe, Constraint und Grad (Median über die festen Netze)."""
    group = communities_of(n, C.BLOCKS)
    recs = []
    for seed in seeds:
        inst = make_instance(C.T_COMMUNITIES, n, c, seed, layout=False)
        tab = measure_table(inst.adj)
        idx = _valid(inst.adj)
        if len(idx) < 3:
            continue
        div, ent = [], []
        for i in idx:
            counts = np.bincount([group[j] for j in inst.adj[i]], minlength=C.BLOCKS) / len(inst.adj[i])
            counts = counts[counts > 0]
            div.append(float(len(counts)))
            ent.append(float(-(counts * np.log(counts)).sum()))
        cons, eff, deg = (_pick(tab[m], idx) for m in (C.M_CONSTRAINT, C.M_EFFSIZE, C.M_DEGREE))
        recs.append({"div_eff": A.spearman(div, eff), "div_cons": A.spearman(div, cons), "div_deg": A.spearman(div, deg),
                     "ent_eff": A.spearman(ent, eff), "ent_cons": A.spearman(ent, cons), "ent_deg": A.spearman(ent, deg), "ent_cons_deg": A.partial_spearman(ent, cons, deg)})
    keys = ("div_eff", "div_cons", "div_deg", "ent_eff", "ent_cons", "ent_deg", "ent_cons_deg")
    return {key: _med([r[key] for r in recs]) for key in keys}


def verdict_diversity(stats: dict) -> tuple[str, str]:
    """Verdikt zu E5: trägt ein niedriges Constraint bei gleichem Grad vielfältigere Nachbarschaft?"""
    part = stats["ent_cons_deg"]
    if math.isnan(part):
        return "warning", "Die partielle Korrelation ist in diesem Netz nicht definiert."
    kind = "success" if part <= -0.3 else "info"
    return kind, (f"Die Entropie der Verbund-Anteile unter den Kontakten hängt mit dem Grad nur schwach zusammen (ρ = {de(stats['ent_deg'], 2)}), mit dem Constraint stärker (ρ = {de(stats['ent_cons'], 2)}). "
                  f"Bei festem Grad ist die partielle Korrelation {de(part, 2)}: ein niedrigeres Constraint geht mit vielfältigerer Nachbarschaft einher. Zahl der Verbünde unter den Kontakten ~ effektive Größe: ρ = {de(stats['div_eff'], 2)}.")


# --- Zusatz: Streuung des Constraints bei gleichem Grad und gleicher Dreieckszahl ---------------------------------------------------------------------


def equal_degree_spread(n, c, seeds=C.LIVE_SEEDS, degrees=(3, 8), min_group=3, wide=0.05) -> dict:
    """Knoten mit gleichem Grad d (zwischen den Grenzen) und gleicher Zahl t der Kanten unter den Kontakten bilden eine Gruppe; gemessen wird die Spannweite des Constraints je Gruppe
    (Verbundnetz, alle festen Netze zusammen, Gruppen ab `min_group` Knoten): Zahl der Gruppen, Median der Spannweite und Anteil der Gruppen mit Spannweite über `wide`."""
    spreads = []
    for seed in seeds:
        inst = make_instance(C.T_COMMUNITIES, n, c, seed, layout=False)
        cons = A.constraint(inst.adj)
        groups = {}
        for i, nb in enumerate(inst.adj):
            if degrees[0] <= len(nb) <= degrees[1]:
                groups.setdefault((len(nb), A.triangles_at(inst.adj, i)), []).append(cons[i])
        spreads += [max(v) - min(v) for v in groups.values() if len(v) >= min_group]
    return {"groups": len(spreads), "median": _med(spreads), "share_wide": (sum(1 for s in spreads if s > wide) / len(spreads)) if spreads else NAN}
