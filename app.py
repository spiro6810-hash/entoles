import streamlit as st
import pandas as pd

st.set_page_config(page_title="Έλεγχος Excel")

st.title("Έλεγχος BAAN και Εργασιών Βάρδιας")

baan = pd.read_excel(
    "data/New Microsoft Excel Worksheet.xlsx",
    engine="openpyxl"
)

erg = pd.read_excel(
    "data/Εργασίες βάρδιας.xlsx",
    engine="openpyxl"
)

st.subheader("Στήλες BAAN")

st.write(baan.columns.tolist())

st.subheader("Στήλες Εργασιών Βάρδιας")

st.write(erg.columns.tolist())

st.subheader("Πρώτες 10 γραμμές BAAN")

st.dataframe(
    baan.head(10),
    use_container_width=True
)

st.subheader("Πρώτες 10 γραμμές Εργασιών Βάρδιας")

st.dataframe(
    erg.head(10),
    use_container_width=True
)
