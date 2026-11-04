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
c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "Ανοιχτές Εντολές",
        len(filtered)
    )

with c2:
    st.metric(
        "Πρώτη Ημερομηνία",
        filtered["Ημερομηνία"].min().strftime("%d/%m/%Y")
    )

with c3:
    st.metric(
        "Τελευταία Ημερομηνία",
        filtered["Ημερομηνία"].max().strftime("%d/%m/%Y")
    )

df["Ημερομηνία"] = pd.to_datetime(
    df["Ημερομηνία"],
    dayfirst=True,
    errors="coerce"
)

col1, col2 = st.columns(2)

with col1:
    from_date = st.date_input(
        "Από",
        value=df["Ημερομηνία"].min().date()
    )

with col2:
    to_date = st.date_input(
        "Έως",
        value=df["Ημερομηνία"].max().date()
    )

filtered = df[
    (df["Ημερομηνία"] >= pd.Timestamp(from_date))
    &
    (df["Ημερομηνία"] <= pd.Timestamp(to_date))
]

st.write(f"Βρέθηκαν {len(filtered)} εντολές στο διάστημα")

st.dataframe(filtered, use_container_width=True)
st.subheader("Σύνοψη ανά ημερομηνία")

summary = (
    filtered.groupby("Ημερομηνία")
    .size()
    .reset_index(name="Σύνολο Εντολών")
)
summary["Ημερομηνία"] = summary["Ημερομηνία"].dt.strftime("%d/%m/%Y")

st.dataframe(
    summary.sort_values("Ημερομηνία"),
    use_container_width=True
)

