"""Molecular graph data structure for bond-graph representation.

Provides Atom, Bond, and MolecularGraph classes used throughout the
MolOps valence-audit pipeline.
"""


class Atom:
    """Represents an atom in a molecular graph."""

    def __init__(self, id, element):
        self.id = id
        self.element = element

    def __repr__(self):
        return f"Atom({self.id}, {self.element})"


class Bond:
    """Represents a covalent bond between two atoms.

    Attributes:
        atom1_id: ID of the first atom in the bond.
        atom2_id: ID of the second atom in the bond.
        order: Bond order (1 = single, 2 = double, 3 = triple, 1.5 = aromatic).
    """

    def __init__(self, atom1_id, atom2_id, order):
        self.atom1_id = atom1_id
        self.atom2_id = atom2_id
        self.order = order

    def __repr__(self):
        return f"Bond({self.atom1_id}-{self.atom2_id}, order={self.order})"


class MolecularGraph:
    """Graph representation of a molecule.

    Atoms are stored in a dict keyed by atom ID for O(1) lookup.
    Bonds are stored as a flat list; adjacency queries iterate over all bonds.
    """

    def __init__(self, name, formula, atoms, bonds):
        self.name = name
        self.formula = formula
        self.atoms = {a.id: a for a in atoms}
        self.bonds = bonds

    def bond_order_sum(self, atom_id):
        """Calculate the sum of bond orders for a given atom.

        This value equals the atom's effective valence when all bonds
        are represented with integer or half-integer orders.

        Returns:
            Numeric total of bond orders incident on *atom_id*.
        """
        total = 0
        for bond in self.bonds:
            if bond.atom1_id == atom_id:
                total += bond.order
        return total

    def get_neighbors(self, atom_id):
        """Return the IDs of all atoms directly bonded to *atom_id*."""
        neighbors = []
        for bond in self.bonds:
            if bond.atom1_id == atom_id:
                neighbors.append(bond.atom2_id)
            elif bond.atom2_id == atom_id:
                neighbors.append(bond.atom1_id)
        return neighbors

    def __repr__(self):
        return (
            f"MolecularGraph({self.name}, "
            f"{len(self.atoms)} atoms, {len(self.bonds)} bonds)"
        )
