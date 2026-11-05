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

st.title("Κενές Εντολές Access")

# =====================================
# ΦΟΡΤΩΣΗ EXCEL
# =====================================

df = pd.read_excel(
    "data/Κενές εντολές.xlsx",
    engine="openpyxl"
)

prog = pd.read_excel(
    "data/ΠρογΕργασίες.xlsx",
    engine="openpyxl"
)

# =====================================
# ΚΑΘΑΡΙΣΜΟΣ ΕΝΤΟΛΩΝ
# =====================================

df["Εντολή"] = (
    pd.to_numeric(
        df["Εντολή"],
        errors="coerce"
    )
    .fillna(0)
    .astype(int)
    .astype(str)
)

prog["Εντολή"] = (
    pd.to_numeric(
        prog["Εντολή"],
        errors="coerce"
    )
    .fillna(0)
    .astype(int)
    .astype(str)
)

# =====================================
# ΗΜΕΡΟΜΗΝΙΑ
# =====================================

df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
)

# =====================================
# ΠΡΟΣΘΗΚΗ START
# =====================================

df = df.merge(
    prog[
        [
            "Εντολή",
            "Start"
        ]
    ],
    on="Εντολή",
    how="left"
)

# =====================================
# ΒΑΡΔΙΑ
# =====================================

def get_shift(value):

    if pd.isna(value):
        return ""

    value = str(value)

    if value.startswith("06"):
        return "1"

    if value.startswith("14"):
        return "2"

    return "3"


df["Βάρδια"] = df["Start"].apply(
    get_shift
)

# =====================================
# ΕΔΡΑ
# =====================================

df["Έδρα"] = (
    df["TSection"]
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
# ΦΙΛΤΡΑ ΗΜΕΡΟΜΗΝΙΑΣ
# =====================================

col1, col2 = st.columns(2)

with col1:
    from_date = st.date_input(
        "Από",
        value=df["Date"].min().date()
    )

with col2:
    to_date = st.date_input(
        "Έως",
        value=df["Date"].max().date()
    )

df = df[
    (df["Date"] >= pd.Timestamp(from_date))
    &
    (df["Date"] <= pd.Timestamp(to_date))
]

# =====================================
# ΣΥΝΟΛΑ
# =====================================

st.success(
    f"Σύνολο Κενών Εντολών: {len(df)}"
)

c1, c2, c3 = st.columns(3)

with c1:
    st.metric(
        "Γραμμή 1",
        len(
            df[
                df["Έδρα"] == "Γραμμή 1"
            ]
        )
    )

with c2:
    st.metric(
        "Σεπόλια",
        len(
            df[
                df["Έδρα"] == "Σεπόλια"
            ]
        )
    )

with c3:
    st.metric(
        "Ελληνικό",
        len(
            df[
                df["Έδρα"] == "Ελληνικό"
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

    result = df[
        df["Εντολή"]
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

report_df = df.copy()

report_df["Date"] = (
    pd.to_datetime(
        report_df["Date"]
    )
    .dt.strftime("%d/%m/%Y")
)

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

        shift_summary = (
            section.groupby("Βάρδια")
            .size()
            .reset_index(name="Σύνολο")
            .sort_values("Βάρδια")
        )

        st.write("Ανά Βάρδια")

        st.dataframe(
            shift_summary,
            use_container_width=True
        )

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
                "Βάρδια",
                "Εντολή"
            ]
        ].copy()

        summary_row = pd.DataFrame({
            "Date": [f"ΣΥΝΟΛΟ: {len(section)}"],
            "Βάρδια": [""],
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
