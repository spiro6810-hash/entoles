import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Έλεγχος Κενών Εντολών",
    layout="wide"
)

st.title("Σύγκριση Access και Streamlit")

# =====================================
# ΦΟΡΤΩΣΗ ΑΡΧΕΙΩΝ
# =====================================

prog = pd.read_excel(
    "data/ΠρογΕργασίες.xlsx",
    engine="openpyxl"
)

erg = pd.read_excel(
    "data/Εργασίες βάρδιας.xlsx",
    engine="openpyxl"
)

access_query = pd.read_excel(
    "data/Κενές εντολές.xlsx",
    engine="openpyxl"
)

# =====================================
# ΚΑΘΑΡΙΣΜΟΣ
# =====================================

prog["Εντολή"] = (
    prog["Εντολή"]
    .astype(str)
    .str.strip()
)

erg["Εντολή"] = (
    erg["Εντολή"]
    .astype(str)
    .str.strip()
)

access_query["Εντολή"] = (
    access_query["Εντολή"]
    .astype(str)
    .str.strip()
)

# =====================================
# JOIN
# =====================================

merged = prog.merge(
    erg[
        [
            "Εντολή",
            "Ώρες",
            "Άτομα"
        ]
    ],
    on="Εντολή",
    how="left"
)

# =====================================
# STREAMLIT QUERY
# =====================================

open_orders = merged[
    (merged["Ακύρωση"] == False)
    &
    (merged["Ώρες"].isna())
    &
    (merged["Άτομα"].isna())
].copy()

# =====================================
# ΣΥΝΟΛΑ
# =====================================

st.success(
    f"Streamlit: {len(open_orders)} εγγραφές"
)

st.success(
    f"Access Query: {len(access_query)} εγγραφές"
)

# =====================================
# ΣΥΓΚΡΙΣΗ
# =====================================

streamlit_orders = set(
    open_orders["Εντολή"]
)

access_orders = set(
    access_query["Εντολή"]
)

only_streamlit = sorted(
    streamlit_orders - access_orders
)

only_access = sorted(
    access_orders - streamlit_orders
)

# =====================================
# ΜΟΝΟ STREAMLIT
# =====================================

st.subheader(
    f"ΜΟΝΟ ΣΤΟ STREAMLIT ({len(only_streamlit)})"
)

st.dataframe(
    pd.DataFrame(
        {"Εντολή": only_streamlit}
    ),
    use_container_width=True
)

# =====================================
# ΜΟΝΟ ACCESS
# =====================================

st.subheader(
    f"ΜΟΝΟ ΣΤΗΝ ACCESS ({len(only_access)})"
)

st.dataframe(
    pd.DataFrame(
        {"Εντολή": only_access}
    ),
    use_container_width=True
)
