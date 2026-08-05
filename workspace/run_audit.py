#!/usr/bin/env python3
"""MolOps Valence Audit Runner.

Loads molecular graph fixtures from JSON, normalizes aromatic bond orders,
validates atom valences against standard rules, and writes a deterministic
audit report.

Exit codes:
    0 — all molecules pass valence validation
    1 — one or more molecules fail
    2 — configuration / I/O error
"""

import argparse
import json
import os
import sys

from molops.graph import MolecularGraph, Atom, Bond
from molops.normalize import normalize_aromatic_bonds
from molops.valence import check_valence
from molops.report import generate_report


def load_fixture(filepath):
    """Load a molecular graph from a JSON fixture file.

    Args:
        filepath: Path to a ``.json`` file with keys ``name``, ``formula``,
                  ``atoms``, and ``bonds``.

    Returns:
        A :class:`MolecularGraph` instance.
    """
    with open(filepath, "r") as f:
        data = json.load(f)

    atoms = [Atom(a["id"], a["element"]) for a in data["atoms"]]
    bonds = [Bond(b["atom1"], b["atom2"], b["order"]) for b in data["bonds"]]

    return MolecularGraph(data["name"], data["formula"], atoms, bonds)


def main():
    parser = argparse.ArgumentParser(
        description="MolOps Valence Audit — validate molecular bond graphs"
    )
    parser.add_argument(
        "--fixtures",
        default="fixtures/",
        help="Path to the directory containing JSON fixture files",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path for the generated audit report",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Load fixtures
    # ------------------------------------------------------------------
    fixtures_dir = args.fixtures
    if not os.path.isdir(fixtures_dir):
        print(
            f"Error: Fixtures directory not found: {fixtures_dir}",
            file=sys.stderr,
        )
        sys.exit(2)

    molecules = []
    for filename in sorted(os.listdir(fixtures_dir)):
        if filename.endswith(".json"):
            filepath = os.path.join(fixtures_dir, filename)
            mol = load_fixture(filepath)
            molecules.append(mol)

    if not molecules:
        print("Error: No fixture files found", file=sys.stderr)
        sys.exit(2)

    # ------------------------------------------------------------------
    # Normalize aromatic bonds (Kekulé conversion)
    # ------------------------------------------------------------------
    for mol in molecules:
        normalize_aromatic_bonds(mol)

    # ------------------------------------------------------------------
    # Validate valences
    # ------------------------------------------------------------------
    results = {}
    for mol in molecules:
        valence_results = check_valence(mol)
        results[mol.name] = {
            "formula": mol.formula,
            "atoms": valence_results,
            "status": (
                "PASS"
                if all(r[4] == "PASS" for r in valence_results)
                else "FAIL"
            ),
        }

    # ------------------------------------------------------------------
    # Generate and write report
    # ------------------------------------------------------------------
    report = generate_report(results)

    with open(args.output, "w") as f:
        f.write(report)

    # ------------------------------------------------------------------
    # Exit code reflects overall pass / fail
    # ------------------------------------------------------------------
    overall_pass = all(r["status"] == "PASS" for r in results.values())
    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()
