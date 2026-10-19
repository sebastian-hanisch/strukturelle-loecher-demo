"""Gemeinsame Fixtures und Hilfen (DEMO-PLAYBOOK §1b): Mini-Instanzen, an denen jede Einheit von Hand geprüft wird."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def make_adj(n, pairs):
    """Nachbarlisten (Tupel von sortierten Tupeln) aus einer Kantenliste."""
    sets = [set() for _ in range(n)]
    for a, b in pairs:
        if a != b:
            sets[a].add(b)
            sets[b].add(a)
    return tuple(tuple(sorted(s)) for s in sets)


@pytest.fixture
def star3():
    """Stern: Mitte 0, Blätter 1, 2, 3. Handrechnung: Constraint der Mitte 3 · (1/3)² = 1/3, der Blätter 1."""
    return make_adj(4, [(0, 1), (0, 2), (0, 3)])


@pytest.fixture
def triangle():
    """Dreieck: jeder Kontakt p = 1/2, indirekt über den dritten Knoten 1/2 · 1/2; (1/2 + 1/4)² · 2 = 1,125."""
    return make_adj(3, [(0, 1), (0, 2), (1, 2)])


@pytest.fixture
def path3():
    """Pfad 0 - 1 - 2: Constraint der Mitte 2 · (1/2)² = 0,5, der Enden 1."""
    return make_adj(3, [(0, 1), (1, 2)])


@pytest.fixture
def d3t1():
    """Knoten 0 mit drei Kontakten, davon 1 und 2 verbunden (Grad d = 3, t = 1). Handrechnung: 2 · (1/3 + 1/3 · 1/2)² + (1/3)² = 1/2 + 1/9 = 11/18."""
    return make_adj(4, [(0, 1), (0, 2), (0, 3), (1, 2)])
