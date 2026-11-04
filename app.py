import streamlit as st
import pandas as pd

st.set_page_config(page_title="Προεργασίες")

st.title("Έλεγχος Προεργασιών")

# ======================
# Διάβασμα Excel
# ======================

df = pd.read_excel(
    "data/ΠρογΕργασίες.xlsx",
    engine="openpyxl"
)

st.success(f"Βρέθηκαν {len(df)} εγγραφές")

# ======================
# Στήλες αρχείου
# ======================

st.subheader("Στήλες αρχείου")

st.write(df.columns.tolist())

# ======================
# Έλεγχος βασικών πεδίων
# ======================

st.subheader("Έλεγχος βασικών πεδίων")

cols = [
    "Date",
    "TSection",
    "Εντολή",
    "Υπεύθυνος Βάρδιας",
    "Ακύρωση",
    "Άκυρη"
]

st.dataframe(
    df[cols].head(50),
    use_container_width=True
)
