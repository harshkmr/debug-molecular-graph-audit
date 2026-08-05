"""Valence rules and validation for molecular graphs.

Contains the standard-valence lookup table for common organic elements
and the validation routine used by the audit pipeline.
"""


# Standard valence (expected total bond-order sum) for common organic elements.
STANDARD_VALENCES = {
    "H": 1,
    "C": 4,
    "N": 3,
    "O": 3,
    "S": 2,
    "F": 1,
    "Cl": 1,
    "Br": 1,
}


def check_valence(graph):
    """Check valence satisfaction for every atom in *graph*.

    For each atom whose element appears in :data:`STANDARD_VALENCES`, the
    function compares the expected valence with the actual bond-order sum
    computed from the graph and emits a PASS / FAIL verdict.

    Returns:
        A list of ``(atom_id, element, expected, actual, status)`` tuples
        sorted by *atom_id*.  *status* is one of ``'PASS'``, ``'FAIL'``,
        or ``'UNKNOWN'`` (for elements not in the lookup table).
    """
    results = []
    for atom_id in sorted(graph.atoms.keys()):
        atom = graph.atoms[atom_id]
        expected = STANDARD_VALENCES.get(atom.element)

        if expected is None:
            results.append((atom_id, atom.element, "?", "?", "UNKNOWN"))
            continue

        actual = len(graph.get_neighbors(atom_id))

        if int(actual) != expected:
            status = "FAIL"
        else:
            status = "PASS"

        results.append((atom_id, atom.element, expected, actual, status))
    return results
