import streamlit as st
import pandas as pd

st.set_page_config(page_title="Κενές Εντολές", layout="wide")

st.title("Κενές Εντολές")

# ----------------------------------
# Φόρτωση Excel
# ----------------------------------

prog = pd.read_excel(
    "data/ΠρογΕργασίες.xlsx",
    engine="openpyxl"
)

erg = pd.read_excel(
    "data/Εργασίες βάρδιας.xlsx",
    engine="openpyxl"
)

# ----------------------------------
# Καθαρισμός δεδομένων
# ----------------------------------

prog["Εντολή"] = prog["Εντολή"].astype(str).str.strip()
erg["Εντολή"] = erg["Εντολή"].astype(str).str.strip()

prog["Date"] = pd.to_datetime(
    prog["Date"],
    errors="coerce"
)

# ----------------------------------
# LEFT JOIN
# ----------------------------------

merged = prog.merge(
    erg[["Εντολή", "Εργασία", "Άτομα"]],
    on="Εντολή",
    how="left"
)

# ----------------------------------
# Κενές Εντολές
# ----------------------------------

open_orders = merged[
    (merged["Ακύρωση"] == False)
    &
    (merged["Εργασία"].isna())
    &
    (merged["Άτομα"].isna())
].copy()

# ----------------------------------
# Φίλτρα ημερομηνίας
# ----------------------------------

col1, col2 = st.columns(2)

with col1:
    from_date = st.date_input(
        "Από",
        value=open_orders["Date"].min().date()
    )

with col2:
    to_date = st.date_input(
        "Έ
