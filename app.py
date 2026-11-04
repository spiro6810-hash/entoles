import streamlit as st
import pandas as pd

st.set_page_config(page_title="Έλεγχος Εκκρεμών")

st.title("Έλεγχος Εκκρεμών Εντολών")

df = pd.read_excel(
    "data/ΠρογΕργασίες.xlsx",
    engine="openpyxl"
)

# Δες μόνο εντολές χωρίς περιγραφή εργασίας
open_df = df[
    df["WorkDescription"].isna()
]

st.success(f"Βρέθηκαν {len(open_df)} εγγραφές χωρίς WorkDescription")

cols = [
    "Date",
    "TSection",
    "Location",
    "Εντολή",
    "Υπεύθυνος Βάρδιας",
    "Ακύρωση",
    "Άκυρη"
]

st.dataframe(
    open_df[cols],
    use_container_width=True
)
