import streamlit as st
import pandas as pd

st.set_page_config(page_title="Κενές Εντολές")

st.title("Κενές Εντολές")

# -----------------------------
# Φόρτωση αρχείων
# -----------------------------

prog = pd.read_excel(
    "data/ΠρογΕργασίες.xlsx",
    engine="openpyxl"
)

erg = pd.read_excel(
    "data/Εργασίες βάρδιας.xlsx",
    engine="openpyxl"
)

# -----------------------------
# Καθαρισμός Εντολής
# -----------------------------

prog["Εντολή"] = prog["Εντολή"].astype(str).str.strip()
erg["Εντολή"] = erg["Εντολή"].astype(str).str.strip()

# -----------------------------
# Left Join
# -----------------------------

merged = prog.merge(
    erg[["Εντολή", "Εργασία", "Άτομα"]],
    on="Εντολή",
    how="left"
)

# -----------------------------
# Κενές εντολές
# -----------------------------

open_orders = merged[
    (merged["Ακύρωση"] == False)
    &
    (merged["Εργασία"].isna())
    &
    (merged["Άτομα"].isna())
]

st.success(
    f"Βρέθηκαν {len(open_orders)} κενές εντολές"
)

# -----------------------------
# Εμφάνιση
# -----------------------------

cols = [
    "Date",
    "TSection",
    "Location",
    "WorkDescription",
    "Εντολή",
    "Υπεύθυνος Βάρδιας"
]

cols = [c for c in cols if c in open_orders.columns]

st.dataframe(
    open_orders[cols],
    use_container_width=True
)
