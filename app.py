import pdfplumber
import streamlit as st

st.set_page_config(page_title="Έλεγχος PDF")

st.title("Έλεγχος PDF Access")

try:

    with pdfplumber.open("data/access_open.pdf") as pdf:

        text = ""

        for page in pdf.pages:
            text += page.extract_text() or ""
            text += "\n\n"

    st.success("Το PDF διαβάστηκε επιτυχώς")

    st.text_area(
        "Περιεχόμενο PDF",
        text,
        height=600
    )

except Exception as e:

    st.error(f"Σφάλμα: {e}")
