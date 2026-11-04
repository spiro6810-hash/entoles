import pdfplumber
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Ανοιχτές Εντολές")

st.title("Ανοιχτές Εντολές από PDF")

# =====================
# Διάβασμα PDF
# =====================

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

# =====================
# Μετατροπή ημερομηνίας
# =====================

df["Ημερομηνία"] = pd.to_datetime(
    df["Ημερομηνία"],
    dayfirst=True,
    errors="coerce"
)

# =====================
# Σύνολο
# =====================

st.success(f"Βρέθηκαν {len(df)} ανοιχτές εντολές")

# =====================
# Φίλτρα ημερομηνίας
# =====================

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

# =====================
# Dashboard
# =====================

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

# =====================
# Λίστα εντολών
# =====================

filtered_display = filtered.copy()

filtered_display["Ημερομηνία"] = (
    filtered_display["Ημερομηνία"]
    .dt.strftime("%d/%m/%Y")
)

st.subheader("Λίστα Ανοιχτών Εντολών")

st.dataframe(
    filtered_display,
    use_container_width=True
)

# =====================
# Σύνοψη ανά ημερομηνία
# =====================

summary = (
    filtered.groupby("Ημερομηνία")
    .size()
    .reset_index(name="Σύνολο Εντολών")
)

summary["Ημερομηνία"] = (
    summary["Ημερομηνία"]
    .dt.strftime("%d/%m/%Y")
)

st.subheader("Σύνοψη ανά ημερομηνία")

st.dataframe(
    summary,
    use_container_width=True
)
