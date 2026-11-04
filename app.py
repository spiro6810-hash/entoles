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
# ΦΟΡΤΩΣΗ EXCEL
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
# ΚΑΘΑΡΙΣΜΟΣ
# =====================================

prog["Εντολή"] = prog["Εντολή"].astype(str).str.strip()
erg["Εντολή"] = erg["Εντολή"].astype(str).str.strip()

prog["Date"] = pd.to_datetime(
    prog["Date"],
    errors="coerce"
)

# =====================================
# JOIN
# =====================================

merged = prog.merge(
 
    erg[
        [
            "Εντολή",
            "Εργασία",
            "Ώρες",
            "Άτομα"
        ]
    ],
    on="Εντολή",
    how="left"
)

test = merged[
    merged["Εντολή"].astype(str).str.strip() == "449892"
]

st.subheader("TEST 449892")

st.dataframe(
    test,
    use_container_width=True
)
# =====================================
# ΚΕΝΕΣ ΕΝΤΟΛΕΣ
# =====================================

open_orders = merged[
    (merged["Ακύρωση"] == False)
    &
    (merged["Ώρες"].isna())
    &
    (merged["Άτομα"].isna())
].copy()

# =====================================
# ΦΙΛΤΡΟ ΗΜΕΡΟΜΗΝΙΑΣ
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
# ΚΑΘΑΡΙΣΜΟΣ ΕΝΤΟΛΗΣ
# =====================================

open_orders["Εντολή"] = (
    pd.to_numeric(
        open_orders["Εντολή"],
        errors="coerce"
    )
    .fillna(0)
    .astype(int)
    .astype(str)
)

# =====================================
# ΣΥΝΟΛΑ
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
# ΑΝΑΖΗΤΗΣΗ
# =====================================

st.subheader("Αναζήτηση Εντολής")

search_order = st.text_input(
    "Γράψε αριθμό εντολής"
)

if search_order:

    result = open_orders[
        open_orders["Εντολή"]
        .astype(str)
        .str.contains(
            search_order,
            na=False
        )
    ]

    st.dataframe(
        result,
        use_container_width=True
    )

# =====================================
# REPORT
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
                    "Εντολή"
                ]
            ].sort_values(
                ["Date"]
            ),
            use_container_width=True
        )

# =====================================
# EXCEL EXPORT
# =====================================

output = io.BytesIO()

with pd.ExcelWriter(
    output,
    engine="openpyxl"
) as writer:

    summary_df = pd.DataFrame({
        "Τμήμα": [
            "Γραμμή 1",
            "Σεπόλια",
            "Ελληνικό"
        ],
        "Σύνολο": [
            len(
                report_df[
                    report_df["Έδρα"] == "Γραμμή 1"
                ]
            ),
            len(
                report_df[
                    report_df["Έδρα"] == "Σεπόλια"
                ]
            ),
            len(
                report_df[
                    report_df["Έδρα"] == "Ελληνικό"
                ]
            )
        ]
    })

    summary_df.loc[len(summary_df)] = [
        "ΓΕΝΙΚΟ ΣΥΝΟΛΟ",
        summary_df["Σύνολο"].sum()
    ]

    summary_df.to_excel(
        writer,
        sheet_name="Σύνοψη",
        index=False
    )

    for area in [
        "Γραμμή 1",
        "Σεπόλια",
        "Ελληνικό"
    ]:

        section = report_df[
            report_df["Έδρα"] == area
        ][
            [
                "Date",
                "Εντολή"
            ]
        ].copy()

        summary_row = pd.DataFrame({
            "Date": [f"ΣΥΝΟΛΟ: {len(section)}"],
            "Εντολή": [""]
        })

        export_df = pd.concat(
            [summary_row, section],
            ignore_index=True
        )

        sheet_name = area.replace(" ", "")

        export_df.to_excel(
            writer,
            sheet_name=sheet_name,
            index=False
        )

excel_data = output.getvalue()

st.download_button(
    "⬇️ Κατέβασε Αναφορά Excel",
    data=excel_data,
    file_name="Κενές_Εντολές.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
