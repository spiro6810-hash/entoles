import streamlit as st
import pandas as pd

st.set_page_config(page_title="Προεργασίες")

st.title("Έλεγχος Προεργασιών")

df = pd.read_excel(
    "data/ΠρογΕργασίες.xlsx",
    engine="openpyxl"
)

st.success(f"Βρέθηκαν {len(df)} εγγραφές")

cols = [
    "Date",
    "TSection",
    "Location",
    "WorkDescription",
    "Εντολή",
    "Υπεύθυνος Βάρδιας",
    "Ακύρωση",
    "Άκυρη"
]

st.dataframe(
    df[cols].head(100),
    use_container_width=True
)
