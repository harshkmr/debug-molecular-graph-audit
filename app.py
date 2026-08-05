import os
import sys
import json
import streamlit as st

# Add workspace directory to Python path to import molops package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "workspace"))

from molops.graph import MolecularGraph, Atom, Bond

# Set Streamlit Page Config
st.set_page_config(
    page_title="MolOps - Molecular Graph Valence Auditor",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished UI
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 700;
        color: #0f3460;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #555555;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #0f3460;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .status-pass {
        color: #2e7d32;
        font-weight: bold;
        background-color: #e8f5e9;
        padding: 4px 12px;
        border-radius: 15px;
    }
    .status-fail {
        color: #c62828;
        font-weight: bold;
        background-color: #ffebee;
        padding: 4px 12px;
        border-radius: 15px;
    }
    </style>
""",
    unsafe_allow_allow_html=True if hasattr(st, "markdown") else False,
)

# Chemistry Reference Values
STANDARD_VALENCES_FIXED = {
    "H": 1,
    "C": 4,
    "N": 3,
    "O": 2,
    "S": 2,
    "F": 1,
    "Cl": 1,
    "Br": 1,
}

STANDARD_VALENCES_BUGGY = {
    "H": 1,
    "C": 4,
    "N": 3,
    "O": 3,  # Bug: Oxygen set to 3
    "S": 2,
    "F": 1,
    "Cl": 1,
    "Br": 1,
}


def calculate_bond_order_sum(graph, atom_id, mode="Fixed"):
    """Calculate bond order sum for an atom."""
    if mode == "Buggy (Incident Hotfix)":
        # Buggy mode: only checks atom1_id
        return sum(b.order for b in graph.bonds if b.atom1_id == atom_id)
    else:
        # Fixed mode: checks both atom1_id and atom2_id
        return sum(
            b.order
            for b in graph.bonds
            if b.atom1_id == atom_id or b.atom2_id == atom_id
        )


def normalize_aromatic_bonds_app(graph, mode="Fixed"):
    """Normalize aromatic bonds (1.5) to Kekulé form."""
    aromatic_bonds = [b for b in graph.bonds if b.order == 1.5]
    if not aromatic_bonds:
        return

    # Order ring bonds by adjacency
    ordered = [aromatic_bonds[0]]
    remaining = list(aromatic_bonds[1:])
    while remaining:
        last = ordered[-1]
        last_atoms = {last.atom1_id, last.atom2_id}
        found = False
        for i, bond in enumerate(remaining):
            bond_atoms = {bond.atom1_id, bond.atom2_id}
            if last_atoms & bond_atoms:
                ordered.append(remaining.pop(i))
                found = True
                break
        if not found:
            break

    if mode == "Buggy (Incident Hotfix)":
        # Buggy mode: sets all aromatic bonds to 1
        for b in ordered:
            b.order = 1
    else:
        # Fixed mode: alternating double (2) and single (1)
        for i, b in enumerate(ordered):
            b.order = 2 if i % 2 == 0 else 1


def audit_molecule(graph, mode="Fixed"):
    """Audit valence for all atoms in a molecule graph."""
    valences = (
        STANDARD_VALENCES_BUGGY
        if mode == "Buggy (Incident Hotfix)"
        else STANDARD_VALENCES_FIXED
    )
    results = []

    for atom_id in sorted(graph.atoms.keys()):
        atom = graph.atoms[atom_id]
        expected = valences.get(atom.element)

        if expected is None:
            results.append({
                "Atom ID": atom_id,
                "Element": atom.element,
                "Expected Valence": "?",
                "Actual Bond Sum": "?",
                "Status": "UNKNOWN",
            })
            continue

        if mode == "Buggy (Incident Hotfix)":
            # Bug: uses neighbor count instead of bond order sum
            actual = len(graph.get_neighbors(atom_id))
        else:
            actual = calculate_bond_order_sum(graph, atom_id, mode="Fixed")

        status = "PASS" if actual == expected else "FAIL"
        results.append({
            "Atom ID": atom_id,
            "Element": atom.element,
            "Expected Valence": expected,
            "Actual Bond Sum": actual,
            "Status": status,
        })

    return results


def main():
    st.markdown(
        '<div class="main-title">🧪 MolOps Molecular Graph Valence Auditor</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-title">Screening pipeline for small organic compounds & bond graph valence verification</div>',
        unsafe_allow_html=True,
    )

    # Sidebar Options
    st.sidebar.header("⚙️ Audit Configuration")

    engine_mode = st.sidebar.radio(
        "Select Audit Engine Mode:",
        ["Fixed / Patched Engine", "Buggy (Incident Hotfix) Engine"],
        help="Switch between the production hotfix buggy state and the patched baseline engine.",
    )

    st.sidebar.markdown("---")
    st.sidebar.header("📁 Molecular Fixtures")

    fixtures_dir = os.path.join(
        os.path.dirname(__file__), "workspace", "fixtures"
    )
    sample_files = []
    if os.path.exists(fixtures_dir):
        sample_files = sorted(
            [f for f in os.listdir(fixtures_dir) if f.endswith(".json")]
        )

    fixture_source = st.sidebar.radio(
        "Source:", ["Sample Fixtures", "Upload Custom JSON"]
    )

    selected_data = None
    file_name = ""

    if fixture_source == "Sample Fixtures":
        selected_sample = st.sidebar.selectbox(
            "Select Sample Molecule:",
            sample_files,
            format_func=lambda x: f"🧬 {x.replace('.json', '').replace('_', ' ').title()} ({x})",
        )
        if selected_sample:
            file_path = os.path.join(fixtures_dir, selected_sample)
            with open(file_path, "r") as f:
                selected_data = json.load(f)
            file_name = selected_sample
    else:
        uploaded_file = st.sidebar.file_uploader(
            "Upload JSON Fixture", type=["json"]
        )
        if uploaded_file:
            selected_data = json.load(uploaded_file)
            file_name = uploaded_file.name

    if not selected_data:
        st.info(
            "👈 Select a sample molecule or upload a custom JSON fixture from the sidebar to begin auditing."
        )
        return

    # Parse Graph
    atoms = [Atom(a["id"], a["element"]) for a in selected_data["atoms"]]
    bonds = [
        Bond(b["atom1"], b["atom2"], b["order"]) for b in selected_data["bonds"]
    ]
    graph = MolecularGraph(
        selected_data["name"], selected_data["formula"], atoms, bonds
    )

    # Normalize Aromatic Bonds
    has_aromatic = any(b.order == 1.5 for b in bonds)
    normalize_aromatic_bonds_app(graph, mode=engine_mode)

    # Perform Audit
    audit_results = audit_molecule(graph, mode=engine_mode)

    passed_count = sum(1 for r in audit_results if r["Status"] == "PASS")
    failed_count = sum(1 for r in audit_results if r["Status"] == "FAIL")
    overall_status = "PASS" if failed_count == 0 else "FAIL"

    # Display Top Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Molecule Name", value=graph.name.capitalize())
    with col2:
        st.metric(label="Formula", value=graph.formula)
    with col3:
        st.metric(label="Total Atoms", value=len(graph.atoms))
    with col4:
        status_color = "🟢 PASS" if overall_status == "PASS" else "🔴 FAIL"
        st.metric(label="Overall Audit Status", value=status_color)

    st.markdown("---")

    # Main Tabs
    tab1, tab2, tab3 = st.tabs(
        ["📊 Atom Valence Audit", "🔗 Bond Structure", "📄 Raw Fixture & Report"]
    )

    with tab1:
        st.subheader("Atom Valence Verification Results")
        if has_aromatic:
            st.success(
                "✨ Aromatic bonds detected (order 1.5) and normalized to Kekulé alternating form."
            )

        # Style table status
        formatted_results = []
        for r in audit_results:
            row = dict(r)
            row["Status"] = "✅ PASS" if r["Status"] == "PASS" else "❌ FAIL"
            formatted_results.append(row)

        st.dataframe(formatted_results, use_container_width=True)

        if overall_status == "FAIL":
            st.error(
                f"⚠️ {failed_count} atom(s) failed valence validation. Check bond orders and standard valence rules."
            )
        else:
            st.success(
                "🎉 All atoms satisfied standard valence constraints perfectly!"
            )

    with tab2:
        st.subheader("Bond Order Breakdown")
        bonds_data = [
            {
                "Bond Pair": f"{graph.atoms[b.atom1_id].element}({b.atom1_id}) — {graph.atoms[b.atom2_id].element}({b.atom2_id})",
                "Atom 1 ID": b.atom1_id,
                "Atom 2 ID": b.atom2_id,
                "Bond Order": b.order,
                "Type": (
                    "Single"
                    if b.order == 1
                    else "Double" if b.order == 2 else "Aromatic (1.5)"
                ),
            }
            for b in graph.bonds
        ]
        st.dataframe(bonds_data, use_container_width=True)

    with tab3:
        st.subheader("Generated Report")
        report_lines = [
            f"MOLECULE: {graph.name}",
            f"FORMULA: {graph.formula}",
        ]
        for r in audit_results:
            report_lines.append(
                f"  {r['Element']}({r['Atom ID']}): expected={r['Expected Valence']} actual={r['Actual Bond Sum']} {r['Status']}"
            )
        report_lines.append(
            f"STATUS: {graph.name} {'PASS' if overall_status=='PASS' else 'FAIL'}"
        )
        report_lines.append(
            f"\nSUMMARY: {passed_count}/{len(audit_results)} passed"
        )
        report_lines.append(f"OVERALL: {overall_status}")

        report_text = "\n".join(report_lines)
        st.code(report_text, language="text")

        st.download_button(
            label="📥 Download Audit Report (.txt)",
            data=report_text,
            file_name=f"audit_report_{graph.name}.txt",
            mime="text/plain",
        )

        st.subheader("Raw JSON Fixture")
        st.json(selected_data)


if __name__ == "__main__":
    main()
