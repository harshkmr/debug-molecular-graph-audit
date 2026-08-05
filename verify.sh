#!/usr/bin/env bash
# =============================================================================
# verify.sh — Static incident verifier for MolOps valence audit pipeline
#
# Runs a multi-phase check on the workspace code:
#   Phase 1  Makefile structure (references, safety, declarations)
#   Phase 2  Audit execution (make audit succeeds, report created)
#   Phase 3  Report content (all molecules present, no failures)
#   Phase 4  Valence spot-checks (specific expected/actual values)
#   Phase 5  Determinism (identical output across two runs)
#   Phase 6  Clean target safety (fixtures preserved, report removed)
#   Phase 7  Module integrity (imports, standard valence table)
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$SCRIPT_DIR/workspace"

cd "$WORKSPACE" || { echo "FATAL: Cannot cd to workspace"; exit 1; }

# ── Counters ──
PASS_COUNT=0
FAIL_COUNT=0
TOTAL=0

pass_test() {
    TOTAL=$((TOTAL + 1))
    PASS_COUNT=$((PASS_COUNT + 1))
    echo "  PASS: $1"
}

fail_test() {
    TOTAL=$((TOTAL + 1))
    FAIL_COUNT=$((FAIL_COUNT + 1))
    echo "  FAIL: $1"
}

# ── Prerequisites ──
if ! command -v make &>/dev/null; then
    echo "FATAL: 'make' not found on PATH"; exit 1
fi
PYTHON=""
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "FATAL: Neither 'python3' nor 'python' found on PATH"; exit 1
fi

echo "=== MolOps Incident Verification ==="
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Phase 1: Makefile structure
# ─────────────────────────────────────────────────────────────────────────────
echo "[Phase 1] Makefile structure"

if [ -f Makefile ]; then
    pass_test "Makefile exists"
else
    fail_test "Makefile not found"
    echo "FATAL: Cannot continue without Makefile"
    echo ""
    echo "=== Results: $PASS_COUNT/$TOTAL passed ==="
    exit 1
fi

# Must reference the correct script name
if grep -q "run_audit\.py" Makefile; then
    pass_test "Makefile references run_audit.py"
else
    fail_test "Makefile does not reference run_audit.py"
fi

# Clean target must NOT remove fixtures/
if grep -A5 "^clean" Makefile | grep -q "fixtures"; then
    fail_test "clean target references fixtures/ (destructive)"
else
    pass_test "clean target does not reference fixtures/"
fi

# .PHONY must include audit
if grep "\.PHONY" Makefile | grep -q "audit"; then
    pass_test ".PHONY includes audit"
else
    fail_test ".PHONY does not include audit"
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Phase 2: Audit execution
# ─────────────────────────────────────────────────────────────────────────────
echo "[Phase 2] Audit execution"

rm -f audit_report.txt

if make audit >/dev/null 2>&1; then
    pass_test "make audit succeeds (exit 0)"
else
    fail_test "make audit failed (non-zero exit)"
fi

if [ -f audit_report.txt ]; then
    pass_test "audit_report.txt was created"
else
    fail_test "audit_report.txt was NOT created"
    echo "FATAL: Cannot validate report content without the report file"
    echo ""
    echo "=== Results: $PASS_COUNT/$TOTAL passed ==="
    exit 1
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Phase 3: Report content — all molecules present, no failures
# ─────────────────────────────────────────────────────────────────────────────
echo "[Phase 3] Report content validation"

for mol in acetic_acid benzene ethanol methane water; do
    if grep -q "MOLECULE: $mol" audit_report.txt; then
        pass_test "Molecule '$mol' present in report"
    else
        fail_test "Molecule '$mol' missing from report"
    fi
done

FAIL_ENTRIES=$(grep -c "FAIL" audit_report.txt 2>/dev/null || true)
if [ "$FAIL_ENTRIES" -eq 0 ]; then
    pass_test "No FAIL entries in report"
else
    fail_test "Found $FAIL_ENTRIES FAIL entries in report"
fi

if grep -q "OVERALL: PASS" audit_report.txt; then
    pass_test "Overall status is PASS"
else
    fail_test "Overall status is not PASS"
fi

if grep -q "SUMMARY: 5/5 passed" audit_report.txt; then
    pass_test "Summary shows 5/5 passed"
else
    fail_test "Summary does not show 5/5 passed"
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Phase 4: Valence spot-checks — verify specific expected/actual values
# ─────────────────────────────────────────────────────────────────────────────
echo "[Phase 4] Valence spot-checks"

# Water: oxygen must have valence 2 (not 3)
if grep -A10 "MOLECULE: water" audit_report.txt | grep -q "O(0): expected=2 actual=2 PASS"; then
    pass_test "Water O(0): expected=2 actual=2 (correct O valence)"
else
    fail_test "Water O(0) valence incorrect"
fi

# Methane: carbon must have valence 4
if grep -A10 "MOLECULE: methane" audit_report.txt | grep -q "C(0): expected=4 actual=4 PASS"; then
    pass_test "Methane C(0): expected=4 actual=4"
else
    fail_test "Methane C(0) valence incorrect"
fi

# Benzene: C(0) must have bond-order sum 4 after Kekulé normalization
if grep -A20 "MOLECULE: benzene" audit_report.txt | grep -q "C(0): expected=4 actual=4 PASS"; then
    pass_test "Benzene C(0): expected=4 actual=4 (Kekulé normalization)"
else
    fail_test "Benzene C(0) valence incorrect (check aromatic normalization)"
fi

# Acetic acid: C(1) with C=O double bond must show actual=4 (not neighbor count 3)
if grep -A20 "MOLECULE: acetic_acid" audit_report.txt | grep -q "C(1): expected=4 actual=4 PASS"; then
    pass_test "Acetic acid C(1): expected=4 actual=4 (bond-order sum, not neighbor count)"
else
    fail_test "Acetic acid C(1) incorrect (may be using neighbor count instead of bond-order sum)"
fi

# Acetic acid: carbonyl O(2) must have expected=2, actual=2
if grep -A20 "MOLECULE: acetic_acid" audit_report.txt | grep -q "O(2): expected=2 actual=2 PASS"; then
    pass_test "Acetic acid O(2): expected=2 actual=2 (double bond)"
else
    fail_test "Acetic acid O(2) valence incorrect"
fi

# Ethanol: O(2) must have expected=2
if grep -A20 "MOLECULE: ethanol" audit_report.txt | grep -q "O(2): expected=2 actual=2 PASS"; then
    pass_test "Ethanol O(2): expected=2 actual=2"
else
    fail_test "Ethanol O(2) valence incorrect"
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Phase 5: Determinism — two runs with different hash seeds must match
# ─────────────────────────────────────────────────────────────────────────────
echo "[Phase 5] Determinism check"

VERIFY_TMP="$WORKSPACE/.verify_tmp"
mkdir -p "$VERIFY_TMP"

rm -f audit_report.txt
PYTHONHASHSEED=13579 make audit >/dev/null 2>&1
cp audit_report.txt "$VERIFY_TMP/run1.txt" 2>/dev/null

rm -f audit_report.txt
PYTHONHASHSEED=97531 make audit >/dev/null 2>&1

if [ -f "$VERIFY_TMP/run1.txt" ] && [ -f audit_report.txt ]; then
    if diff -q audit_report.txt "$VERIFY_TMP/run1.txt" >/dev/null 2>&1; then
        pass_test "Report is deterministic across runs (different PYTHONHASHSEED)"
    else
        fail_test "Report differs between runs (non-deterministic ordering)"
    fi
else
    fail_test "Could not generate reports for determinism comparison"
fi

rm -rf "$VERIFY_TMP"

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Phase 6: Clean target safety
# ─────────────────────────────────────────────────────────────────────────────
echo "[Phase 6] Clean target safety"

# Ensure report exists before cleaning
make audit >/dev/null 2>&1
make clean >/dev/null 2>&1

# Fixtures must survive
if [ -d fixtures ] && [ -f fixtures/water.json ] && [ -f fixtures/methane.json ] \
   && [ -f fixtures/benzene.json ] && [ -f fixtures/ethanol.json ] \
   && [ -f fixtures/acetic_acid.json ]; then
    pass_test "All fixtures preserved after make clean"
else
    fail_test "Fixtures destroyed by make clean"
fi

# Report file should be removed
if [ ! -f audit_report.txt ]; then
    pass_test "audit_report.txt removed by make clean"
else
    fail_test "audit_report.txt not removed by make clean"
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Phase 7: Module integrity
# ─────────────────────────────────────────────────────────────────────────────
echo "[Phase 7] Module integrity"

if $PYTHON -c "from molops.graph import MolecularGraph, Atom, Bond" 2>/dev/null; then
    pass_test "molops.graph imports OK"
else
    fail_test "molops.graph import failed"
fi

if $PYTHON -c "from molops.valence import check_valence, STANDARD_VALENCES" 2>/dev/null; then
    pass_test "molops.valence imports OK"
else
    fail_test "molops.valence import failed"
fi

if $PYTHON -c "from molops.normalize import normalize_aromatic_bonds" 2>/dev/null; then
    pass_test "molops.normalize imports OK"
else
    fail_test "molops.normalize import failed"
fi

if $PYTHON -c "from molops.report import generate_report" 2>/dev/null; then
    pass_test "molops.report imports OK"
else
    fail_test "molops.report import failed"
fi

# Validate the standard valence table itself
if $PYTHON -c "
from molops.valence import STANDARD_VALENCES
assert STANDARD_VALENCES['H'] == 1, 'H should be 1'
assert STANDARD_VALENCES['C'] == 4, 'C should be 4'
assert STANDARD_VALENCES['N'] == 3, 'N should be 3'
assert STANDARD_VALENCES['O'] == 2, 'O should be 2'
assert STANDARD_VALENCES['S'] == 2, 'S should be 2'
assert STANDARD_VALENCES['F'] == 1, 'F should be 1'
" 2>/dev/null; then
    pass_test "STANDARD_VALENCES table is correct"
else
    fail_test "STANDARD_VALENCES table contains errors"
fi

# Validate bond_order_sum checks both sides of a bond
if $PYTHON -c "
from molops.graph import MolecularGraph, Atom, Bond
atoms = [Atom(0, 'O'), Atom(1, 'H')]
bonds = [Bond(0, 1, 1)]
g = MolecularGraph('test', 'HO', atoms, bonds)
assert g.bond_order_sum(0) == 1, 'atom1 sum wrong'
assert g.bond_order_sum(1) == 1, 'atom2 sum wrong'
" 2>/dev/null; then
    pass_test "bond_order_sum works for both atom1 and atom2"
else
    fail_test "bond_order_sum does not handle both sides of a bond"
fi

echo ""

# ═════════════════════════════════════════════════════════════════════════════
# Summary
# ═════════════════════════════════════════════════════════════════════════════
echo "========================================"
echo "  Results: $PASS_COUNT/$TOTAL passed, $FAIL_COUNT failed"
echo "========================================"
echo ""

if [ "$FAIL_COUNT" -eq 0 ]; then
    echo "VERIFICATION: PASSED"
    exit 0
else
    echo "VERIFICATION: FAILED"
    exit 1
fi
