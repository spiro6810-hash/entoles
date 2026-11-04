import streamlit as st
import pandas as pd

st.set_page_config(page_title="Προεργασίες")

st.title("Έλεγχος Προεργασιών")

df = pd.read_excel(
    "data/ΠρογΕργασίες.xlsx",
    engine="openpyxl"
)

st.success(f"Βρέθηκαν {len(df)} εγγραφές")

st.write("Στήλες αρχείου:")

st.write(df.columns.tolist())

st.dataframe(
    df.head(20),
    use_container_width=True
)
