import re
import io
from datetime import datetime

import pdfplumber
import pandas as pd
import streamlit as st

# ---- Business rules (όπως τα έδωσες) ----
OPEN_STATUS = "Αποδεκτο"

def department_from_installation(install: str) -> str:
    s = (install or "").strip().upper()

    # Τραμ
    if s.startswith("LS") or s.startswith("TWS"):
        return "Τραμ"

    # Μετρό
    if s.startswith("L1") or s.startswith("TW1"):
        return "Γραμμή 1"
    if s.startswith("L2") or s.startswith("TW2"):
        return "Γραμμή 2"
    if s.startswith("L3") or s.startswith("TW3"):
        return "Γραμμή 3"

    return "Άγνωστο"


def build_slices_from_header(header_line: str, columns: list[str]):
    starts = {}
    for col in columns:
        idx = header_line.find(col)
        if idx >= 0:
            starts[col] = idx

    found = [(col, starts[col]) for col in columns if col in starts]
    found.sort(key=lambda x: x[1])

    slices = {}
    for i, (col, start) in enumerate(found):
        end = found[i + 1][1] if i + 1 < len(found) else None
        slices[col] = (start, end)

    return slices


def parse_row_by_slices(line: str, slices: dict):
    out = {}
    for col, (a, b) in slices.items():
        out[col] = (line[a:b] if b is not None else line[a:]).strip()
    return out


def extract_rows_from_pdf(file_bytes: bytes) -> pd.DataFrame:
    header_mark = "Εντ.Συντήρ"
    columns = ["Εντ.Συντήρ", "Περιγραφή", "Εγκατάσταση", "Θέση", "Προτ", "Κατάστ"]

    rows = []
    current_slices = None
    in_table = False

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                # Header line
                if header_mark in line and "Κατάστ" in line:
                    current_slices = build_slices_from_header(line, columns)
                    in_table = True
                    continue

                if not in_table or not current_slices:
                    continue

                if not line.strip():
                    continue

                # data lines usually begin with digits (work order id)
                if not re.match(r"^\s*\d+", line):
                    continue

                row = parse_row_by_slices(line, current_slices)
                if row.get("Εντ.Συντήρ"):
                    rows.append(row)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    return df


def make_excel_bytes(summary_df: pd.DataFrame, open_df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Σύνοψη", index=False)
        open_df.to_excel(writer, sheet_name="Ανοιχτές_Λίστα", index=False)
    return output.getvalue()


# ---- UI ----
st.set_page_config(page_title="Baan Open Work Orders", layout="wide")
st.title("Ανοιχτές Εντολές Εργασίας ανά Τμήμα (Baan PDF)")

uploaded = st.file_uploader("Ανέβασε το PDF εκτύπωσης από Baan", type=["pdf"])

if uploaded:
    file_bytes = uploaded.read()
    df = extract_rows_from_pdf(file_bytes)

    if df.empty:
        st.error("Δεν μπόρεσα να βρω τον πίνακα μέσα στο PDF. Αν θες, στείλε μου 1 γραμμή κεφαλίδας για να το προσαρμόσω.")
        st.stop()

    # μόνο ανοιχτές
    df["Κατάστ"] = df["Κατάστ"].astype(str)
    df_open = df[df["Κατάστ"].str.strip().eq(OPEN_STATUS)].copy()

    # τμήμα
    df_open["Τμήμα"] = df_open["Εγκατάσταση"].apply(department_from_installation)

    # φίλτρα
    col1, col2, col3 = st.columns(3)
    with col1:
        dept = st.multiselect("Τμήμα", sorted(df_open["Τμήμα"].unique()), default=sorted(df_open["Τμήμα"].unique()))
    with col2:
        prio = st.multiselect("Προτεραιότητα (Προτ)", sorted(df_open["Προτ"].unique()))
    with col3:
        install_search = st.text_input("Αναζήτηση Εγκατάστασης (π.χ. L1, TWS)")

    filtered = df_open[df_open["Τμήμα"].isin(dept)]
    if prio:
        filtered = filtered[filtered["Προτ"].isin(prio)]
    if install_search.strip():
        filtered = filtered[filtered["Εγκατάσταση"].str.contains(install_search.strip(), case=False, na=False)]

    # σύνοψη
    summary = (
        filtered.groupby("Τμήμα")["Εντ.Συντήρ"]
        .count()
        .rename("Ανοιχτές (Αποδεκτο)")
        .reset_index()
        .sort_values("Τμήμα")
    )

    st.subheader("Σύνοψη")
    st.dataframe(summary, use_container_width=True)

    st.subheader("Λίστα ανοιχτών (Αποδεκτο)")
    st.dataframe(filtered, use_container_width=True, height=520)

    # export
    excel_bytes = make_excel_bytes(summary, filtered)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    st.download_button(
        "⬇️ Κατέβασε Excel",
        data=excel_bytes,
        file_name=f"open_orders_{stamp}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

else:
    st.info("Ανέβασε ένα PDF από την εκτύπωση του Baan για να δεις ανοιχτές ανά Γρ1/Γρ2/Γρ3/Τραμ.")
