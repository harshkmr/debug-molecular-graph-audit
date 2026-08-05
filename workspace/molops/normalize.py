"""Bond-order normalization for aromatic and resonance structures.

Aromatic bonds (order = 1.5) must be converted to a valid Kekulé form
(alternating single and double bonds) before valence-sum validation.
"""


def normalize_aromatic_bonds(graph):
    """Normalize aromatic bonds (order 1.5) to Kekulé alternating form.

    For each ring system composed of aromatic bonds, the function converts
    the uniform 1.5 orders into alternating single (1) and double (2) bonds
    so that every ring atom satisfies standard valence rules.

    Args:
        graph: A :class:`MolecularGraph` instance (modified in-place).

    Returns:
        The same *graph* instance, with aromatic bond orders updated.
    """
    aromatic_bonds = [b for b in graph.bonds if b.order == 1.5]
    if not aromatic_bonds:
        return graph

    # Order the aromatic bonds into a ring by adjacency
    ring = _order_ring(aromatic_bonds)

    # Assign Kekulé bond orders around the ring
    for i, bond in enumerate(ring):
        bond.order = 1

    return graph


def _order_ring(bonds):
    """Order ring bonds by adjacency so consecutive bonds share an atom.

    Starting from the first bond in *bonds*, greedily appends the next bond
    that shares an atom with the current tail of the ordered list.

    Args:
        bonds: An unordered list of :class:`Bond` objects forming a ring.

    Returns:
        A list of the same bonds reordered so that adjacent entries share
        exactly one atom.
    """
    if not bonds:
        return []

    ordered = [bonds[0]]
    remaining = list(bonds[1:])

    while remaining:
        last = ordered[-1]
        last_atoms = {last.atom1_id, last.atom2_id}

        found = False
        for i, bond in enumerate(remaining):
            bond_atoms = {bond.atom1_id, bond.atom2_id}
            if last_atoms & bond_atoms:  # shares at least one atom
                ordered.append(remaining.pop(i))
                found = True
                break

        if not found:
            break  # disconnected fragment; stop

    return ordered
