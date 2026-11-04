import streamlit as st
import pandas as pd

st.set_page_config(page_title="Εκκρεμείς Εντολές")

st.title("Εκκρεμείς Εντολές BAAN")

# =====================
# Φόρτωση αρχείων
# =====================

baan = pd.read_excel(
    "data/New Microsoft Excel Worksheet.xlsx",
    engine="openpyxl"
)

erg = pd.read_excel(
    "data/Εργασίες βάρδιας.xlsx",
    engine="openpyxl"
)

# =====================
# Καθαρισμός εντολών
# =====================

baan["Εντολή"] = baan["Εντολή"].astype(str).str.strip()
erg["Εντολή"] = erg["Εντολή"].astype(str).str.strip()

# =====================
# Εκκρεμείς = υπάρχουν στο BAAN
# αλλά όχι στις Εργασίες Βάρδιας
# =====================

open_orders = baan[
    ~baan["Εντολή"].isin(erg["Εντολή"])
]

st.success(
    f"Βρέθηκαν {len(open_orders)} εκκρεμείς εντολές"
)

# =====================
# Εμφάνιση
# =====================

cols = [
    "Ημ/νία",
    "Τμήμα",
    "Εγκατάσταση",
    "Περιγραφή εργασίας",
    "Υπεύθυνος",
    "Εντολή"
]

available_cols = [
    c for c in cols
    if c in open_orders.columns
]

st.dataframe(
    open_orders[available_cols],
    use_container_width=True
)
