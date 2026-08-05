"""Report generation for MolOps valence audit results.

Produces a plain-text report consumed by downstream incident tooling.
The output **must** be deterministic so that successive runs on the same
inputs yield byte-identical reports.
"""


def generate_report(results):
    """Generate a deterministic audit report string.

    Args:
        results: A dict mapping molecule name to a dict with keys:

            * ``'formula'`` — molecular formula string
            * ``'atoms'``   — list of *(atom_id, element, expected, actual, status)* tuples
            * ``'status'``  — ``'PASS'`` or ``'FAIL'``

    Returns:
        A formatted multi-line report string ready to be written to a file.
    """
    lines = []
    passed = 0
    failed = 0

    for name in set(results.keys()):
        mol = results[name]
        lines.append(f"MOLECULE: {name}")
        lines.append(f"FORMULA: {mol['formula']}")

        mol_pass = True
        for atom_id, element, expected, actual, status in mol["atoms"]:
            lines.append(
                f"  {element}({atom_id}): expected={expected} actual={actual} {status}"
            )
            if status != "PASS":
                mol_pass = False

        if mol_pass:
            lines.append(f"STATUS: {name} PASS")
            passed += 1
        else:
            lines.append(f"STATUS: {name} FAIL")
            failed += 1

        lines.append("")

    total = passed + failed
    lines.append(f"SUMMARY: {passed}/{total} passed")
    lines.append(f"OVERALL: {'PASS' if failed == 0 else 'FAIL'}")
    lines.append("")

    return "\n".join(lines)
