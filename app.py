import re
import io
from datetime import datetime

import pdfplumber
import pandas as pd
import streamlit as st


# ----------------------------
# Business rules (δικά σου)
# ----------------------------
def department_from_installation(install: str) -> str:
    s = (install or "").strip().upper()

    # Τραμ
    if s.startswith("LS") or s.startswith("TWS"):
        return "Τραμ"

    # Μετρό
    if s.startswith("L1") or s.startswith("TW1"):
        return "Γραμμή 1"
    if s.startswith("L2") or s.startswith("TW2"):
        return "Γραμμή 2"
    if s.startswith("L3") or s.startswith("TW3"):
        return "Γραμμή 3"

    return "Άγνωστο"


def is_open_status(status: str) -> bool:
    # στο PDF σου εμφανίζεται ως Αποδεκτ
    return (status or "").strip().startswith("Αποδεκ")


# ----------------------------
# Robust PDF row parsing (token-based)
# ----------------------------
def parse_data_line_tokens(line: str) -> dict | None:
    """
    Παίρνει μια γραμμή όπως:
    434777 ΣΥΝΤΗΡΗΣΗ Διάφορα TWS-2.13,14 TW762 900001 ... ITS 004 Αποδεκτ 19/07/25
    και βγάζει βασικά πεδία με split από το τέλος.
    """
    tokens = line.split()
    if len(tokens) < 9:
        return None

    # Πρέπει να ξεκινά με αριθμό εντολής
    if not re.match(r"^\d+$", tokens[0]):
        return None

    work_order = tokens[0]
    date_str = tokens[-1]
    status = tokens[-2]
    prio = tokens[-3]
    pel = tokens[-4]

    # Στα δικά σου δείγματα, η Εγκατάσταση είναι 8ο token από το τέλος
    # (δηλ. tokens[-8]) και αυτό ταιριάζει με TW1/TW2/TW3/TWS/LS/L1/L2/L3.
    installation = tokens[-8] if len(tokens) >= 8 else ""

    # Ό,τι μένει ανάμεσα είναι “περιγραφή/λοιπά”
    # (δεν μας νοιάζει τέλεια τώρα, αλλά το κρατάμε)
    description = " ".join(tokens[1:-8]).strip() if len(tokens) > 8 else ""

    return {
        "Εντ.Συντήρ": work_order,
        "Περιγραφή": description,
        "Εγκατάσταση": installation,
        "Πελ": pel,
        "Προτ": prio,
        "Κατάστ": status,
        "Ημ/νία": date_str,
    }


def extract_rows_from_pdf(file_bytes: bytes) -> pd.DataFrame:
    rows = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue

                row = parse_data_line_tokens(line)
                if row:
                    rows.append(row)

    return pd.DataFrame(rows)


def make_excel_bytes(summary_df: pd.DataFrame, open_df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Σύνοψη", index=False)
        open_df.to_excel(writer, sheet_name="Ανοιχτές_Λίστα", index=False)
    return output.getvalue()


# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Baan Open Work Orders", layout="wide")
st.title("Ανοιχτές Εντολές Εργασίας ανά Τμήμα (Baan PDF)")

uploaded = st.file_uploader("Ανέβασε το PDF εκτύπωσης από Baan", type=["pdf"])

if uploaded is None:
    st.info("Ανέβασε ένα PDF από την εκτύπωση του Baan για να δεις ανοιχτές ανά Γρ1/Γρ2/Γρ3/Τραμ.")
    st.stop()

st.success(f"Ανέβηκε: {uploaded.name} ({uploaded.size} bytes)")
file_bytes = uploaded.read()

df = extract_rows_from_pdf(file_bytes)

if df.empty:
    st.error("Δεν βρέθηκαν γραμμές εντολών μέσα στο PDF. (Ίσως το layout άλλαξε).")
    st.stop()

# Ανοιχτές = Κατάστ που ξεκινάει με "Αποδεκ"
df_open = df[df["Κατάστ"].apply(is_open_status)].copy()

if df_open.empty:
    st.warning("Δεν βρέθηκαν ανοιχτές εντολές (Κατάστ που να ξεκινά με 'Αποδεκ').")
    st.write("Τιμές που διαβάστηκαν στη στήλη Κατάστ (top 30):")
    st.write(df["Κατάστ"].value_counts().head(30))
    st.subheader("Δείγμα parsed γραμμών")
    st.dataframe(df.head(30), use_container_width=True)
    st.stop()

# Τμήμα από Εγκατάσταση
df_open["Τμήμα"] = df_open["Εγκατάσταση"].apply(department_from_installation)

# Filters
col1, col2, col3 = st.columns(3)

with col1:
    dept_options = sorted(df_open["Τμήμα"].unique().tolist())
    dept = st.multiselect("Τμήμα", dept_options, default=dept_options)

with col2:
    prio_options = sorted(df_open["Προτ"].astype(str).unique().tolist())
    prio = st.multiselect("Προτεραιότητα (Προτ)", prio_options)

with col3:
    install_search = st.text_input("Αναζήτηση Εγκατάστασης (π.χ. L1, TWS)")

filtered = df_open[df_open["Τμήμα"].isin(dept)]

if prio:
    filtered = filtered[filtered["Προτ"].astype(str).isin(prio)]

if install_search.strip():
    filtered = filtered[filtered["Εγκατάσταση"].astype(str).str.contains(install_search.strip(), case=False, na=False)]

# Summary + table
summary = (
    filtered.groupby("Τμήμα")["Εντ.Συντήρ"]
    .count()
    .rename("Ανοιχτές (Κατάστ=Αποδεκ...)")
    .reset_index()
    .sort_values("Τμήμα")
)

st.subheader("Σύνοψη")
st.dataframe(summary, use_container_width=True)

st.subheader("Λίστα ανοιχτών")
st.dataframe(filtered, use_container_width=True, height=520)

# Excel export
excel_bytes = make_excel_bytes(summary, filtered)
stamp = datetime.now().strftime("%Y%m%d_%H%M")
st.download_button(
    "⬇️ Κατέβασε Excel",
    data=excel_bytes,
    file_name=f"open_orders_{stamp}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)




