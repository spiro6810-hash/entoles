import streamlit as st
import pandas as pd
import io

# =====================================
# ΡΥΘΜΙΣΕΙΣ
# =====================================

st.set_page_config(
    page_title="Κενές Εντολές",
    layout="wide"
)

st.title("Κενές Εντολές")

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

# =====================================
# ΚΑΘΑΡΙΣΜΟΣ ΔΕΔΟΜΕΝΩΝ
# =====================================

prog["Εντολή"] = prog["Εντολή"].astype(str).str.strip()
erg["Εντολή"] = erg["Εντολή"].astype(str).str.strip()

prog["Date"] = pd.to_datetime(
    prog["Date"],
    errors="coerce"
)

# =====================================
# LEFT JOIN
# =====================================

merged = prog.merge(
    erg[["Εντολή", "Εργασία", "Άτομα"]],
    on="Εντολή",
    how="left"
)

# =====================================
# ΚΕΝΕΣ ΕΝΤΟΛΕΣ
# =====================================

open_orders = merged[
    (merged["Ακύρωση"] == False)
    &
    (merged["Εργασία"].isna())
    &
    (merged["Άτομα"].isna())
].copy()

# =====================================
# ΦΙΛΤΡΑ ΗΜΕΡΟΜΗΝΙΑΣ
# =====================================

col1, col2 = st.columns(2)

with col1:
    from_date = st.date_input(
        "Από",
        value=open_orders["Date"].min().date()
    )

with col2:
    to_date = st.date_input(
        "Έως",
        value=open_orders["Date"].max().date()
    )

open_orders = open_orders[
    (open_orders["Date"] >= pd.Timestamp(from_date))
    &
    (open_orders["Date"] <= pd.Timestamp(to_date))
]

# =====================================
# ΒΑΡΔΙΑ ΑΠΟ ΩΡΑ ΕΝΑΡΞΗΣ
# =====================================

def get_shift(value):

    if pd.isna(value):
        return ""

    value = str(value)

    if value.startswith("06"):
        return "1"

    if value.startswith("14"):
        return "2"

    if value.startswith("22"):
        return "3"

    if value.startswith("00"):
        return "3"

    if value.startswith("01"):
        return "3"

    if value.startswith("02"):
        return "3"

    if value.startswith("03"):
        return "3"

    if value.startswith("04"):
        return "3"

    if value.startswith("05"):
        return "3"

    return ""

open_orders["Βάρδια"] = open_orders["Start"].apply(get_shift)

# =====================================
# ΕΔΡΑ
# =====================================

open_orders["Έδρα"] = (
    open_orders["TSection"]
    .astype(str)
    .str[0]
    .replace({
        "1": "Γραμμή 1",
        "2": "Σεπόλια",
        "3": "Ελληνικό",
        "S": "Ελληνικό"
    })
)

# =====================================
# ΜΕΤΡΗΤΕΣ
# =====================================

st.success(
    f"Βρέθηκαν {len(open_orders)} κενές εντολές"
)

c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "Γραμμή 1",
        len(
            open_orders[
                open_orders["Έδρα"] == "Γραμμή 1"
            ]
        )
    )

with c2:
    st.metric(
        "Σεπόλια",
        len(
            open_orders[
                open_orders["Έδρα"] == "Σεπόλια"
            ]
        )
    )

with c3:
    st.metric(
        "Ελληνικό",
        len(
            open_orders[
                open_orders["Έδρα"] == "Ελληνικό"
            ]
        )
    )

# =====================================
# ΑΝΑΛΥΤΙΚΗ ΑΝΑΦΟΡΑ
# =====================================

report_df = open_orders.copy()

report_df["Date"] = pd.to_datetime(
    report_df["Date"]
).dt.strftime("%d/%m/%Y")

for area in [
    "Γραμμή 1",
    "Σεπόλια",
    "Ελληνικό"
]:

    section = report_df[
        report_df["Έδρα"] == area
    ].copy()

    st.subheader(
        f"{area} - Σύνολο {len(section)}"
    )

    if len(section) > 0:

        st.dataframe(
            section[
                [
                    "Date",
                    "Βάρδια",
                    "Εντολή"
                ]
            ].sort_values(
                ["Date", "Βάρδια"]
            ),
            use_container_width=True
        )
        # =====================================
# ΕΞΑΓΩΓΗ EXCEL
# =====================================

output = io.BytesIO()

with pd.ExcelWriter(output, engine="openpyxl") as writer:

    report_df[
        report_df["Έδρα"] == "Γραμμή 1"
    ][
        ["Date", "Βάρδια", "Εντολή"]
    ].to_excel(
        writer,
        sheet_name="Γραμμή1",
        index=False
    )

    report_df[
        report_df["Έδρα"] == "Σεπόλια"
    ][
        ["Date", "Βάρδια", "Εντολή"]
    ].to_excel(
        writer,
        sheet_name="Σεπόλια",
        index=False
    )

    report_df[
        report_df["Έδρα"] == "Ελληνικό"
    ][
        ["Date", "Βάρδια", "Εντολή"]
    ].to_excel(
        writer,
        sheet_name="Ελληνικό",
        index=False
    )

excel_data = output.getvalue()

st.download_button(
    label="⬇️ Κατέβασε Αναφορά Excel",
    data=excel_data,
    file_name="Κενές_Εντολές.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
