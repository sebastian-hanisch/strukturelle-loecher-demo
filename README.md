# Strukturelle Löcher: ist ein Makler mehr als ein Hub? – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-strukturelle-loecher-demo.streamlit.app/)** -->

Drittes Stück der **Netzwerkanalyse-Reihe** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, im Struktur-Arm die **soziale Lesart der Brücken** aus der [Brücken-Demo](https://sebastianhanisch-bridges-demo.streamlit.app/) (dort: was fällt bei Ausfall einer Kante auseinander; hier: wer vermittelt zwischen Gruppen, die einander sonst nicht kennen). Anders als die Fall-Demos zeigt sie **ein** Maß an einem wachsenden Beispiel: einem Netz von Subunternehmern und Lieferanten (synthetisch; dazu das echte Link-Netz von sebastianhanisch.net).

Die Demo rechnet das **Constraint** und die **effektive Größe** nach Burt am Ego-Netz eines gewählten Knotens Schritt für Schritt vor, stellt sie Grad, Betweenness, Nähe und Brücken gegenüber und prüft drei Aussagen an Modellnetzen: Wer ist Makler? Verbinden Kanten ohne gemeinsame Bekannte (Granovetters „schwache Bindungen“) tatsächlich Verbünde? Erfahren Makler Neuigkeiten früher und aus mehr Richtungen?

## Kernfrage

**Ist ein Makler mehr als ein Knoten mit vielen Kontakten, und wann tragen Burts und Granovetters Aussagen?** Der Gesamtplan formulierte die Frage als „Brücken als Informationsvorteil“; die Vormessung widerlegte diesen Hook (siehe unten), die Kernfrage wurde mit Freigabe des Einzelplans umgestellt.

## Befunde und Korrekturen gegenüber dem Plan

- **Hook „Brücke = Makler“ widerlegt.** Im Gesamtplan stand: Brückenknoten haben ein niedriges Constraint. Im Handbeispiel (zwei Fünfer-Cliquen mit einer Verbindung, „Barbell“) stimmt das (0,478 gegen 0,629 im Inneren), in Modellnetzen nicht: die meisten Brücken führen zu Blättern, und bei Brücken zwischen Knoten mit mindestens zwei Kontakten folgt das Constraint-Perzentil dem Grad-Perzentil (siehe Tabelle).
- **Das Constraint ist in den meisten Netzen fast ein Gradmaß.** Das war nicht der Plan („Brückenknoten haben niedriges Constraint, hängt das vom Netztyp ab?“), ist aber der stärkste Befund der Messreihen; die Demo stellt ihn deshalb an den Anfang.
- **Blätter zählen als Löcher.** Im Makler-Beispiel hat ein Hub mit drei Blättern ein *kleineres* Constraint (0,301) als der Makler zwischen drei Verbünden (0,333). Die Betweenness findet den Makler (0,686, die höchste im Netz), das Constraint findet den Hub.
- **Eigene Kernroutinen statt Kopien.** Der Einzelplan sah Kopien aus `bridges-demo` und `centrality-demo` vor; die Demo enthält stattdessen kurze eigene Fassungen (Low-Link für die Brücken, Brandes für die Betweenness, Nähe nach Wasserman und Faust), die gegen `networkx` geprüft sind (`tests/test_oracle_strukturelle_loecher.py`). Der Grund: die Originale tragen Ereignisprotokolle für die Anzeige der Schritte, die hier nicht gebraucht werden.
- **Kritik von 2024 am Constraint** (Dreiecksbegriffe) nur als Randnotiz: Inhalt nicht gelesen, die Demo zeigt an einem Handbeispiel, dass das Constraint vom Grad der Nachbarn **im Dreieck** abhängt (0,611 gegen 0,521 bei sonst gleichem Ego-Netz).

## Modell

Netze ungewichtet und ungerichtet. Für den Knoten *i* mit *d*<sub>i</sub> Kontakten ist *p*<sub>ij</sub> = 1/*d*<sub>i</sub>; das **Constraint** ist die Summe über alle Kontakte *j* von (*p*<sub>ij</sub> + Σ<sub>q</sub> *p*<sub>iq</sub>·*p*<sub>qj</sub>)², wobei *q* die Kontakte von *i* sind, die *j* kennen. Ein Makler zwischen *r* getrennten Verbünden mit je einem Kontakt hat 1/*r*. Die **effektive Größe** ist *d* − 2*t*/*d* (Borgatti 1997; *t* = Kanten unter den Kontakten). Die **Überlappung** einer Kante ist der Anteil gemeinsamer Kontakte an allen Kontakten beider Enden (Onnela u. a.); „schwach“ heißt hier Überlappung 0. Formeln und Literatur stehen im 📐-Expander der App. Die Ausbreitung ist ein SI-Modell in diskreter Zeit (Ansteckung 0,3 je Schritt und Kontakt).

## Methodik

| Baustein | Inhalt |
|---|---|
| **Netze** | Generatoren aus `k-core-demo` (Stück 1) als Kopie: Verbünde (sechs, 80 % der Kanten innen), Zufallsnetz, Potenzgesetz-Netz, skalenfrei, Ring mit Abkürzungen, Gitter, Hubs am Rand; dazu Makler-Beispiel (19 Knoten) und Link-Netz von sebastianhanisch.net (Schnappschuss vom 2026-09-30, ungerichtet) mit Schalter für die beiden Navigationsseiten |
| **Maße** | Constraint, effektive Größe, Grad, Betweenness, Nähe, Clustering, Kantenüberlappung, Brücken |
| **Statistik** | Spearman mit Mittelwerträngen, partielle Rangkorrelation (Grad fest), AUC, Jaccard der Top-5-%-Mengen (Gleichstand: kleinere Knotennummer; die Zahl der Gleichstände am Rand wird gemeldet) |
| **Experiment 1** | Constraint gegen Grad, effektive Größe, Betweenness und Clustering je Netztyp |
| **Experiment 2** | Überlappung der Makler-Mengen und Rolle der Brücken |
| **Experiment 3** | Granovetter: Überlappung innerhalb und zwischen Verbünden bei dünner bis dichter Vernetzung; Watts–Strogatz über die Umverdrahtung β |
| **Experiment 4** | Ankunftszeit einer Nachricht (SI) gegen Constraint, Grad, Nähe |
| **Experiment 5** | Vielfalt der Nachbarschaft (Zahl der Verbünde, Entropie) gegen Constraint bei festem Grad |

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`. Netze der Messreihen: die acht festen Netze `SWEEP_SEEDS` je Zelle, n = 250, c = 6, wo nichts anderes steht (Experiment 3 und 5: n = 300); Spearman-Werte über die Knoten mit Kontakt, Median über die acht Netze.

| Frage | Befund |
|---|---|
| **Stimmen die Maße?** | Constraint, effektive Größe, Clustering, Nähe, Betweenness und Brücken stimmen auf 120 festen Zufallsnetzen mit `networkx` überein (Abweichung unter 10⁻⁹); die Überlappung mit der Mengenformel, Spearman mit `scipy`, die AUC mit der Aufzählung aller Paare |
| **Handwerte** | Stern mit drei Blättern: Mitte 1/3, Blatt 1; **Dreieck: 1,125** (das Constraint kann über 1 liegen); Pfad aus drei Knoten: Mitte 0,5; **Makler zwischen *r* Cliquen: 1/*r*** (0,5; 0,33; 0,25; 0,17 für *r* = 2, 3, 4, 6) |
| **Ist das Constraint ein Gradmaß?** (Rangkorrelation mit dem Grad) | In **5 von 7** Netztypen liegt sie bei −0,9 oder darunter (Verbünde −0,96, Zufallsnetz −0,99, Potenzgesetz −0,96, skalenfrei −0,97, Hubs am Rand −0,98); schwächer im Ring (−0,76) und im Gitter (−0,82, dort fast alle Grade gleich). Die effektive Größe: im Zufallsnetz −1,00 |
| **Was bleibt bei festem Grad?** (partielle Rangkorrelation) | Das Constraint steigt mit dem **Clustering**: 0,78 (Verbünde), 0,84 (Zufall), 0,88 (Potenzgesetz), 0,90 (skalenfrei), 0,84 (Hubs am Rand), 0,21 (Ring); es fällt mit der **Betweenness**: −0,49 (Verbünde), −0,27, −0,47, −0,21, −0,19 (Ring), −0,75 (Gitter), −0,79 (Hubs) |
| **Wie viel bestimmen Grad und Dreiecke?** | Knoten mit gleichem Grad (3 bis 8) und gleicher Zahl der Dreiecke (161 Gruppen, Verbundnetze): Spannweite des Constraints im Median **0,012**, bei 1,9 % der Gruppen über 0,05 |
| **Wählen die Maße dieselben Knoten?** (Jaccard der Top-5-%-Mengen: niedriges Constraint gegen hohen Grad / hohe Betweenness) | **Verbünde 0,51 / 0,37**, Hubs am Rand 0,60 / 0,50, Zufall 0,60 / 0,71, Potenzgesetz und skalenfrei 0,85 / 0,71 bzw. 0,85 / 0,85. Gitter 0 (**183** Knoten am Rand gleichauf), Ring 0,71 / 0,50 bei 49 Gleichständen: dort entscheidet die Gleichstandsregel |
| **Sind Brücken Makler?** (c = 3, damit Zufallsnetze Brücken haben) | Zufallsnetz: im Median **41,5** Brücken, davon nur **7** zwischen Knoten mit mindestens zwei Kontakten; deren Enden stehen beim Constraint im Perzentil **0,52**, beim Grad im Perzentil **0,50** (0 = bester Wert). Verbünde 44,5 / 8,5, 0,51 / 0,49; Potenzgesetz 149 / 28, 0,21 / 0,22; Hubs am Rand (c = 6) 142 / 5, 0,02 / 0,02. **Das Constraint folgt dem Grad, nicht der Brücke.** Barbell: Brückenknoten 0,478, Inneres 0,629 |
| **Verbinden schwache Bindungen die Verbünde?** (Verbünde, n = 300) | Güte (AUC) von „keine gemeinsamen Nachbarn sagt: Kante zwischen Verbünden“: **0,68 (c = 6), 0,84 (c = 10), 0,96 (c = 16)**. Kanten innerhalb ohne gemeinsamen Nachbarn: 60 %, 25 %, 3,5 %; zwischen den Verbünden 97 %, 88 %, 69 %. Echte Brücken: 0,4 % der Kanten bei c = 6, sonst keine |
| **Wenige Abkürzungen oder viele?** (Watts–Strogatz, n = 300, k = 6) | β = 0: Pfadlänge **25,4**, Clustering 0,60, Constraint 0,378. **β = 0,01: Pfadlänge 12,1, Clustering 0,59.** β = 0,1: 4,8 und 0,44 (12 % der Kanten ohne gemeinsamen Nachbarn). β = 1: 3,4 und 0,016, **92 %** ohne gemeinsamen Nachbarn, Constraint 0,19 |
| **Erfahren Makler Neuigkeiten früher?** (SI, 40 Quellen × 3 Läufe) | Ja: Rangkorrelation Ankunftszeit ~ Constraint **0,64 bis 0,89** in allen 5 Netztypen. **Aber die Nähe sagt es in 4 von 5 Typen besser voraus** (−0,84 bis −0,95; nur in „Hubs am Rand“ ist das Constraint mit 0,86 gleichauf mit dem Grad −0,87). Bei fester Nähe bleibt vom Constraint ein Rest von 0,08 bis 0,49 |
| **Haben Makler eine vielfältigere Nachbarschaft?** (Verbünde, n = 300, c = 10) | Bei festem Grad: partielle Rangkorrelation Entropie ~ Constraint **−0,54**; die Entropie hängt mit dem Grad nur schwach zusammen (0,18), mit dem Constraint stärker (−0,34); Zahl der Verbünde ~ effektive Größe 0,48 |
| **Makler-Beispiel** (19 Knoten) | Makler (Knoten 15): Constraint **0,333**, effektive Größe 3, Betweenness **0,686** (höchste im Netz). Hub mit drei Blättern (Knoten 4): Constraint **0,301**, effektive Größe 5,29. Das Constraint bevorzugt den Hub |
| **Link-Netz mit allen Seiten** (350 Knoten, 2 374 Kanten) | **Keine Brücke**, mittleres Clustering 0,94; Constraint ~ Grad −0,91; Startseite und Kontaktseite sind mit 348 Knoten verlinkt (Betweenness 0,42, Constraint 0,066); niedrigstes Constraint (Grad ≥ 2): konzepte-spieltheorie.html mit 0,055 (Grad 65) |
| **Link-Netz ohne Startseite und Kontakt** (348 Knoten, 1 679 Kanten) | **121 Brückenkanten**, 34,8 % der Knoten haben Grad 1, Clustering 0,58; Constraint ~ Grad −0,97; die Sammelseiten sind Makler: **konzepte-netzwerkfluss.html (0,040)** und **demos.html (0,043)**, demos.html mit der höchsten Betweenness (0,13) |
| **Standardnetz** (Verbünde, n = 120, c = 6, Seed 35, Knoten 100) | 360 Kanten, 1 Brücke; Constraint ~ Grad −0,87; Top-5-%-Überlappung mit dem Grad 0,33, mit der Betweenness 0,71; Knoten 100: Constraint 0,112 bei Grad 11 |

### Hypothesen des Einzelplans

| | Hypothese | Ergebnis |
|---|---|---|
| H1 | Eigenbauten stimmen mit der Definition überein | ✅ |
| H2 | Das Constraint ist kein reines Gradmaß | ⚠ in 5 von 7 Netztypen fast eines; Rest bei festem Grad: Clustering, Betweenness, Vielfalt |
| H3 | Außer vom Grad hängt es nur von den Dreiecken ab | ✅ nahezu (Spannweite 0,012) |
| H4 | Brücken sind Makler | ❌ nur im Handbeispiel |
| H5 | Makler nach Constraint, Betweenness und Grad sind verschiedene Knoten | ⚠ nur in Verbünden und (unscharf) bei Hubs am Rand |
| H6 | Schwache Bindungen verbinden Verbünde | ⚠ nur bei genug Dreiecken (AUC 0,68 → 0,96) |
| H7 | Wenige Abkürzungen verkürzen die Wege, ohne die Dreiecke zu zerstören | ✅ |
| H8 | Makler erfahren Information früher | ✅, aber die Nähe sagt es besser voraus |
| H9 | Makler haben eine vielfältigere Nachbarschaft | ✅ (bei festem Grad) |
| H10 | Im Link-Netz zeigen sich Makler | ⚠ nur ohne die Navigationsseiten |

## Ehrliche Grenzen

- **Ungewichtet und ungerichtet.** Burt rechnet mit Gewichten; das gewichtete Constraint ist ein anderer Wert. Granovetters „Stärke“ ist hier nur die Struktur (Überlappung), nicht Dauer oder Häufigkeit.
- **Das Maß unterscheidet nicht, ob Kontakte etwas wert sind.** Blätter am Hub senken das Constraint (siehe Makler-Beispiel).
- **Synthetische Netze mit geplanten Verbünden.** Die Zahlen gelten für diese Netztypen bei diesen Größen (Median über feste Netze), nicht für beliebige Netze. Das Link-Netz ist ein Sonderfall (Navigationsregeln statt Beziehungen).
- **Rangkorrelationen bei vielen gleichen Graden** (Gitter, Ring) sind unscharf, die Top-5-%-Mengen hängen dort an Gleichständen; die App meldet es und urteilt in diesem Fall nicht („Die Maße trennen hier nicht“).
- **Ausbreitung: SI mit gleicher Wahrscheinlichkeit.** Der Informationsvorsprung ist ein Modellbefund, kein Beleg für echte Nachrichten.
- **Keine Kausalität.** Dass Makler tatsächlich mehr Erfolg haben, zeigen nur Experimente an echten Personen (z. B. Rajkumar u. a. 2022: umgekehrt U-förmiger Zusammenhang zwischen Bindungsstärke und Stellenvermittlung auf LinkedIn, abhängig von der Branche); die Demo bildet das nicht nach.
- **Die genaue Formel der Überlappung** wurde im Original (Onnela u. a. 2007) nicht gelesen; die Umsetzung folgt der in der Literatur üblichen Fassung (gemeinsame Kontakte geteilt durch alle Kontakte beider Enden ohne sie selbst) und ist gegen die Mengenformel geprüft.

## Verifikation

- **Kern:** Handwerte auf Mini-Instanzen (`tests/conftest.py`, `tests/test_algorithm.py`): Stern, Dreieck, Pfad, geschlossene Form für vollständige Graphen, Makler mit *r* Cliquen, Makler-Beispiel in exakten Brüchen, Überlappung, Brücken, Rangstatistik, Ausbreitung (p = 1 gleich Breitensuche, p = 0 nie).
- **Orakel:** `tests/test_oracle_strukturelle_loecher.py` – 120 feste Zufallsnetze gegen `networkx` (Constraint, effektive Größe, Clustering, Nähe, Betweenness, Brücken), Mengenformel für die Überlappung, `scipy.stats.spearmanr` mit Gleichständen, AUC durch Aufzählung aller Paare, Ausbreitung bei p = 1 gegen den Abstand von `networkx`.
- **Netze:** gültig in allen Ecken der Regler, deterministisch je Seed (auch über Prozesse mit verschiedenem Hash-Seed), Makler-Beispiel, Link-Netz mit und ohne Navigationsseiten, Watts–Strogatz.
- **Verdikte:** jede Schwelle und jede Zahl im Text an von Hand gesetzten Werten (`tests/test_verdicts.py`), Randfälle in `tests/test_edge_cases.py`.
- **Befunde:** jede Zahl dieser README in `tests/test_claims.py`.
- **Mutationsprüfung des Kerns** (`slo_algorithm.py`, 175 Stellen): nach Ergänzung von Tests keine Überlebenden; 16 Stellen sind als äquivalent festgehalten (z. B. Sicherheitsobergrenze der Ausbreitungsschleife, `a < b` bei Kanten ohne Schleifen), vier Mutanten laufen in Endlosschleifen (Zeitüberschreitung). Zustand in `tests/mutation_state.json`.
- **Presets:** vollständig, Werte innerhalb der Reglergrenzen, jeder Preset-Knoten existiert, Standard-Preset gleich Standardeinstellung.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum, jeder Netztyp mit jedem Maß, Permalink, alle fünf Experimente) und Footer-Test.
- **Layout:** Schnellstart oben in der Seitenleiste, fester Kopf, aktives Preset hervorgehoben; jede Änderung eines Reglers hebt die Markierung auf (`tests/test_layout.py`).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `data/link_netz.json` | Link-Netz von sebastianhanisch.net (Schnappschuss vom 2026-09-30) |
| `requirements-dev.txt` | Laufzeit plus pytest, networkx, scipy (nur für die Gegenproben) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `slo_algorithm.py` | Kern: Constraint, effektive Größe, Überlappung, Brücken, Nähe, Betweenness, Rangstatistik, Ausbreitung |
| `slo_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `slo_evaluation.py` | Kennzahlen, Analyse, Verdikt-Logik, Messreihen über feste Netze |
| `slo_layout.py` | Fester Kopf (Stylesheet) |
| `slo_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `slo_scenario.py` | Netze: Generatoren (Kopie aus `k-core-demo`), Makler-Beispiel, Watts–Strogatz, Link-Netz, Anordnung |
| `slo_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Mini-Instanzen und Handwerte, Orakel, Netze, Verdikte, Randfälle, Presets, Layout, AppTest-Smoke-Test, Footer, Laufzeit-Importe, Befunde |

## Bewusst nicht umgesetzt

- **Gewichtetes und gerichtetes Constraint** (gelber Ausbau): eigene Frage mit eigener Datenlage.
- **Kausale Tests** (Umgekehrt-U nach Rajkumar u. a.): nur genannt, nicht nachgestellt; dafür braucht es Experimente an echten Personen.
- **Nachbildung der Kritik von 2024** am Constraint: Inhalt nicht gelesen.
- **Weitere Maße für Makler** (Burt-Effizienz, Brokerage-Rollen nach Gould und Fernandez): würden den Blick auf drei Maße und eine Frage verwässern.
- **Ausbreitungsmodelle jenseits SI** (Schwellenmodelle, Eindämmung): kommen in den Stücken 5 bis 7 der Reihe.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und NumPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
