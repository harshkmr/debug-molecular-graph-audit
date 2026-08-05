# Debug Make-based Molecular Graph Valence Audits

## Context

The **MolOps screening pipeline** uses a Python-based molecular graph analyzer to
validate bond graphs for small organic compounds before chemists can release a
suspect-batch report. During a recent incident hotfix, several components drifted
and the production triage job now fails.

No internet access or third-party chemistry libraries are available — all
chemistry knowledge is encoded directly in the Python source and JSON fixtures.

## Task

Repair all bugs in the codebase so that the static incident verifier (`verify.sh`)
accepts the graph algorithms, deterministic report generation, and Make-driven
audit workflow.

The code must:

1. Correctly compute **bond-order sums** for all atoms in a molecular graph
2. Use correct **standard valence values** for common organic elements
3. Properly **normalize aromatic bonds** (Kekulé alternation: alternating single/double)
4. Validate atom valences using **bond-order sums** (not neighbor counts)
5. Generate **deterministic** reports (consistent ordering across runs)
6. Have a working **Makefile** with correct targets and safe `clean` behaviour

## Known Symptoms

1. `make audit` fails to execute at all
2. When run manually, the audit reports incorrect expected valence for oxygen-containing molecules
3. Benzene fails valence checks after aromatic bond normalization
4. Molecules with double bonds report wrong actual bond-order sums
5. Running the audit multiple times may produce differently-ordered reports
6. `make clean` has destructive behaviour that removes input fixture data

## Project Layout

```
workspace/
├── molops/                    # Python package (contains bugs)
│   ├── __init__.py
│   ├── graph.py               # Molecular graph data structure
│   ├── valence.py             # Standard valence rules & validation
│   ├── normalize.py           # Aromatic bond-order normalization
│   └── report.py              # Audit report generation
├── fixtures/                  # JSON molecular graph fixtures (correct — do NOT modify)
│   ├── water.json             # H₂O
│   ├── methane.json           # CH₄
│   ├── ethanol.json           # C₂H₅OH
│   ├── benzene.json           # C₆H₆
│   └── acetic_acid.json       # CH₃COOH
├── run_audit.py               # Main audit entry point
└── Makefile                   # Build / audit workflow targets (contains bugs)
```

## Verification

From the project root:

```bash
bash verify.sh
```

All verification phases must pass for the task to be considered complete.

## Chemistry Reference

| Element | Standard Valence (total bond-order sum) |
|---------|----------------------------------------|
| H       | 1                                      |
| C       | 4                                      |
| N       | 3                                      |
| O       | 2                                      |
| S       | 2                                      |
| F       | 1                                      |
| Cl      | 1                                      |
| Br      | 1                                      |

**Aromatic bonds** (order 1.5) must be normalized to Kekulé form:
alternating double (2) and single (1) bonds around the ring.
