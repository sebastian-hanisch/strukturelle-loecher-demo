"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

# --- Netztypen -----------------------------------------------------------------------------------------------------------------------------------
T_COMMUNITIES = "Verbünde"
T_BROKER = "Makler-Beispiel (19 Knoten)"
T_RANDOM = "Zufallsnetz"
T_POWER = "Potenzgesetz-Netz"
T_BA = "Skalenfreies Netz (BA)"
T_RING = "Ring mit Abkürzungen"
T_GRID = "Gitter"
T_HUBS = "Hubs am Rand"
T_LINK = "Link-Netz von sebastianhanisch.net"

GENERATED_TYPES = (T_COMMUNITIES, T_RANDOM, T_POWER, T_BA, T_RING, T_GRID, T_HUBS)   # n und c wirken
FIXED_TYPES = (T_BROKER, T_LINK)                                                    # Handbeispiel und echtes Netz
ALL_TYPES = (T_COMMUNITIES, T_BROKER, T_RANDOM, T_POWER, T_BA, T_RING, T_GRID, T_HUBS, T_LINK)
BLOCKS = 6                                                                         # Zahl der Verbünde im Verbundnetz

C_MEANING = {
    T_COMMUNITIES: "mittlerer Grad; 80 % der Kanten bleiben im eigenen Verbund (6 Verbünde)",
    T_RANDOM: "mittlerer Grad des Zufallsnetzes",
    T_POWER: "mittlerer Grad (Gradfolge mit Potenzgesetz-Exponent 2,5, Konfigurationsmodell)",
    T_BA: "zwei Kanten je neuem Knoten, also m = c / 2 gerundet (jeder Knoten hat mindestens m Nachbarn)",
    T_RING: "Nachbarn auf dem Ring (c gerade gerundet), dazu Abkürzungen mit 5 % je Ringkante",
    T_GRID: "Nachbarschaft: unter 6 vier Nachbarn, 6 bis 7 mit einer Diagonale, ab 8 mit beiden Diagonalen",
    T_HUBS: "Kernkontakte je Randknoten (c / 3 gerundet, mindestens 2); der Rest sind Blätter an 5 Hubs",
}

N_MIN, N_MAX, DEFAULT_N = 30, 250, 120   # Slider-Maximum: Layout O(n^2 * 80), Betweenness O(n * m), Ausbreitung O(Läufe * m)
C_MIN, C_MAX, DEFAULT_C = 3, 12, 6
SEED_MAX, DEFAULT_SEED = 999999, 35
SWEEP_SEEDS = tuple(range(100000, 100008))         # feste Netze für alle Sweeps: nie ein einzelner Seed als Befund
LIVE_SEEDS = SWEEP_SEEDS[:4]                       # so viele feste Netze je Zelle rechnet die App live (die README-Zahlen nutzen alle acht)
KNOTEN_MAX = 349                                   # Obergrenze des Knotenfelds (das Link-Netz hat 350 Knoten); wirksam wird der Wert begrenzt auf n - 1
DEFAULT_KNOTEN = 100                                # Voreinstellung: der Knoten mit dem niedrigsten Constraint im Standardnetz (Seed 35)

# --- Maße und Link-Netz --------------------------------------------------------------------------------------------------------------------------
M_CONSTRAINT, M_EFFSIZE, M_DEGREE, M_BETWEENNESS, M_CLOSENESS, M_CLUSTERING = "Constraint", "Effektive Größe", "Grad", "Betweenness", "Nähe", "Clustering"
MEASURES = (M_CONSTRAINT, M_EFFSIZE, M_DEGREE, M_BETWEENNESS, M_CLOSENESS, M_CLUSTERING)
MEASURE_HELP = {
    M_CONSTRAINT: "Burt: wie stark ein Knoten in seine Nachbarschaft eingebunden ist (klein = viele Löcher, Makler).",
    M_EFFSIZE: "Burt: Zahl der Kontakte ohne die Doppelungen unter den Kontakten (groß = viele nicht verbundene Kontakte).",
    M_DEGREE: "Zahl der Kontakte.",
    M_BETWEENNESS: "Anteil der kürzesten Wege zwischen anderen Knoten, die über den Knoten laufen.",
    M_CLOSENESS: "Kehrwert des mittleren Abstands zu allen erreichbaren Knoten.",
    M_CLUSTERING: "Anteil der Paare von Kontakten, die selbst verbunden sind.",
}
NAV_COUNT, NAV_DROP = "mitzählen", "weglassen"
NAV_CHOICES = (NAV_COUNT, NAV_DROP)
NAV_PAGES = ("index.html", "kontakt.html")        # Navigationsseiten des Link-Netzes: mit allen Seiten verlinkt

# --- Experimente ----------------------------------------------------------------------------------------------------------------------------------
TOP_FRACTION = 0.05                                # "Makler" = die besten 5 % nach einem Maß
SI_P = 0.3                                         # Ansteckung je Schritt und Kontakt (SI in diskreter Zeit)
ARR_SOURCES, ARR_RUNS = 40, 3                      # zufällige Quellen und Läufe je Quelle
ARR_TYPES = (T_RANDOM, T_COMMUNITIES, T_BA, T_RING, T_HUBS)
GRAN_DEGREES = (6, 10, 16)                         # mittlerer Grad im Verbundnetz: dünn, mittel, dicht
WS_K = 6
WS_BETAS = (0.0, 0.01, 0.03, 0.1, 0.3, 1.0)
DIVERSITY_C = 10

# --- Darstellung ---------------------------------------------------------------------------------------------------------------------------------
COLOR_EDGE = "rgba(120,120,120,0.30)"
COLOR_BRIDGE = "#e8a33d"
COLOR_SELECT = "#d62728"
COLOR_LINE = "#4c78a8"
COLOR_A = "#2F6B65"
COLOR_B = "#c4623b"
COLOR_C = "#6b5b95"
SCALE_CONSTRAINT = "Viridis"

PRESETS = {
    "Verbünde (Voreinstellung)": {"netztyp": T_COMMUNITIES, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED, "mass": M_CONSTRAINT, "knoten": DEFAULT_KNOTEN, "nav": NAV_COUNT},
    "Makler-Beispiel": {"netztyp": T_BROKER, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED, "mass": M_CONSTRAINT, "knoten": 15, "nav": NAV_COUNT},
    "Zufallsnetz": {"netztyp": T_RANDOM, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED, "mass": M_CONSTRAINT, "knoten": 12, "nav": NAV_COUNT},
    "Ring mit Abkürzungen": {"netztyp": T_RING, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED, "mass": M_CONSTRAINT, "knoten": 13, "nav": NAV_COUNT},
    "Hubs am Rand": {"netztyp": T_HUBS, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED, "mass": M_CONSTRAINT, "knoten": 12, "nav": NAV_COUNT},
    "Unser Link-Netz (alle Seiten)": {"netztyp": T_LINK, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED, "mass": M_CONSTRAINT, "knoten": 5, "nav": NAV_COUNT},
    "Link-Netz ohne Startseite und Kontakt": {"netztyp": T_LINK, "n": DEFAULT_N, "c": DEFAULT_C, "seed": DEFAULT_SEED, "mass": M_CONSTRAINT, "knoten": 5, "nav": NAV_DROP},
}
PRESET_HELP = {
    "Verbünde (Voreinstellung)": "Sechs Verbünde, 80 % der Kanten innen: das Standardnetz der Reihe. Constraint und Grad wählen hier teils verschiedene Knoten.",
    "Makler-Beispiel": "Drei Verbünde mit einem Makler (Knoten 15, je ein Kontakt in jeden Verbund) und einem Hub mit Blättern (Knoten 4): der Rechenweg des Constraints von Hand nachvollziehbar.",
    "Zufallsnetz": "Ohne jede Verbundstruktur: das Constraint folgt fast ganz dem Grad.",
    "Ring mit Abkürzungen": "Rund drei Viertel der Knoten haben denselben Grad; die wenigen Abkürzungen sind die schwachen Bindungen im Sinne Granovetters.",
    "Hubs am Rand": "Fünf Hubs mit vielen Blättern: viel Grad, aber die Blätter sind keine Makler-Kontakte.",
    "Unser Link-Netz (alle Seiten)": "Das echte Link-Netz von sebastianhanisch.net: Startseite und Kontaktseite sind mit fast allen Seiten verlinkt (nur die isolierte 404-Seite fehlt), deshalb gibt es kaum strukturelle Löcher.",
    "Link-Netz ohne Startseite und Kontakt": "Dasselbe Netz ohne die beiden Navigationsseiten: jetzt haben die Sammelseiten das niedrigste Constraint und die höchste Betweenness; sie sind zugleich die Seiten mit dem höchsten Grad.",
}
