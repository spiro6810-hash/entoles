import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Κενές Εντολές",
    layout="wide"
)

st.title("Κενές Εντολές")

# =====================================
# Φόρτωση Excel
# =====================================

prog = pd.read_excel(
    "data/ΠρογΕργασίες.xlsx",
    engine="openpyxl"
)

erg = pd.read_excel(
    "data/Εργασίες βάρδιας.xlsx",
    engine="openpyxl"
)

# =====================================
# Καθαρισμός δεδομένων
# =====================================

prog["Εντολή"] = prog["Εντολή"].astype(str).str.strip()
erg["Εντολή"] = erg["Εντολή"].astype(str).str.strip()

prog["Date"] = pd.to_datetime(
    prog["Date"],
    errors="coerce"
)

# =====================================
# LEFT JOIN
# =====================================

merged = prog.merge(
    erg[["Εντολή", "Εργασία", "Άτομα"]],
    on="Εντολή",
    how="left"
)

# =====================================
# Κενές εντολές
# =====================================

open_orders = merged[
    (merged["Ακύρωση"] == False)
    &
    (merged["Εργασία"].isna())
    &
    (merged["Άτομα"].isna())
].copy()

# =====================================
# Φίλτρα ημερομηνίας
# =====================================

col1, col2 = st.columns(2)

with col1:
    from_date = st.date_input(
        "Από",
        value=open_orders["Date"].min().date()
    )

with col2:
    to_date = st.date_input(
        "Έως",
        value=open_orders["Date"].max().date()
    )

open_orders = open_orders[
    (open_orders["Date"] >= pd.Timestamp(from_date))
    &
    (open_orders["Date"] <= pd.Timestamp(to_date))
]

# =====================================
# Μετρητής
# =====================================

st.success(
    f"Βρέθηκαν {len(open_orders)} κενές εντολές"
)

# =====================================
# Σύνολο ανά TSection
# =====================================

section_summary = (
    open_orders.groupby("TSection")
    .size()
    .reset_index(name="Σύνολο")
    .sort_values("Σύνολο", ascending=False)
)

st.subheader("Σύνολο ανά TSection")

st.dataframe(
    section_summary,
    use_container_width=True
)

# =====================================
# Λίστα εντολών
# =====================================

show_cols = [
    "Date",
    "TSection",
    "Location",
    "WorkDescription",
    "Εντολή"
]

show_cols = [
    c for c in show_cols
    if c in open_orders.columns
]

st.subheader("Λίστα Κενών Εντολών")

st.dataframe(
    open_orders[show_cols]
    .sort_values("Date"),
    use_container_width=True
)
