import pdfplumber
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Ανοιχτές Εντολές")

st.title("Ανοιχτές Εντολές από PDF")

rows = []

with pdfplumber.open("data/access_open.pdf") as pdf:

    text = ""

    for page in pdf.pages:
        text += page.extract_text() or ""
        text += "\n"

lines = text.splitlines()

for line in lines:

    parts = line.split()

    if len(parts) == 2:

        date = parts[0]
        order = parts[1]

        if "/" in date and order.isdigit():

            rows.append(
                {
                    "Ημερομηνία": date,
                    "Εντολή": order
                }
            )

df = pd.DataFrame(rows)

st.success(f"Βρέθηκαν {len(df)} ανοιχτές εντολές")
st.write(df.tail(200))
st.dataframe(df, use_container_width=True)
