import re
import io
from datetime import datetime, date

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
    # στο PDF σου εμφανίζεται ως Αποδεκτ (ή Αποδεκτο)
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

    if not re.match(r"^\d+$", tokens[0]):
        return None

    work_order = tokens[0]
    date_str = tokens[-1]
    status = tokens[-2]
    prio = tokens[-3]
    pel = tokens[-4]

    # Στα δικά σου δείγματα, η Εγκατάσταση είναι 8ο token από το τέλος
    installation = tokens[-8] if len(tokens) >= 8 else ""
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


def parse_baan_date(s: str) -> pd.Timestamp:
    """
    Το PDF σου δείχνει ημερομηνίες σαν 21/07/25 (dd/mm/yy).
    """
    s = (s or "").strip()
    if not s:
        return pd.NaT
    try:
        return pd.to_datetime(s, format="%d/%m/%y", errors="coerce")
    except Exception:
        return pd.NaT


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

# Μόνο ανοιχτές
df_open = df[df["Κατάστ"].apply(is_open_status)].copy()
if df_open.empty:
    st.warning("Δεν βρέθηκαν ανοιχτές εντολές (Κατάστ που να ξεκινά με 'Αποδεκ').")
    st.write("Τιμές στη στήλη Κατάστ (top 30):")
    st.write(df["Κατάστ"].value_counts().head(30))
    st.dataframe(df.head(30), use_container_width=True)
    st.stop()

# Τμήμα
df_open["Τμήμα"] = df_open["Εγκατάσταση"].apply(department_from_installation)

# Παλαιότητα
today = pd.Timestamp(date.today())
df_open["Ημ/νία_dt"] = df_open["Ημ/νία"].apply(parse_baan_date)
df_open["Ημέρες_ανοικτή"] = (today - df_open["Ημ/νία_dt"]).dt.days

# αν κάτι δεν parse-αρίστηκε σωστά, βγαίνει NaN
# το αφήνουμε, αλλά θα το δείχνουμε/ταξινομούμε με ασφάλεια
# ------------------------------------------------------------

# ----------------------------
# Quick filters (κουμπιά)
# ----------------------------
st.subheader("Γρήγορα φίλτρα")
c1, c2, c3, c4, c5 = st.columns(5)
if "quick_dept" not in st.session_state:
    st.session_state.quick_dept = "Όλα"

with c1:
    if st.button("Όλα", use_container_width=True):
        st.session_state.quick_dept = "Όλα"
with c2:
    if st.button("Μόνο Γραμμή 1", use_container_width=True):
        st.session_state.quick_dept = "Γραμμή 1"
with c3:
    if st.button("Μόνο Γραμμή 2", use_container_width=True):
        st.session_state.quick_dept = "Γραμμή 2"
with c4:
    if st.button("Μόνο Γραμμή 3", use_container_width=True):
        st.session_state.quick_dept = "Γραμμή 3"
with c5:
    if st.button("Μόνο Τραμ", use_container_width=True):
        st.session_state.quick_dept = "Τραμ"

# ----------------------------
# Filters (αναλυτικά)
# ----------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    dept_options = sorted(df_open["Τμήμα"].unique().tolist())
    default_dept = dept_options

    # αν πατήθηκε quick filter, το κάνουμε default σε εκείνο
    if st.session_state.quick_dept != "Όλα" and st.session_state.quick_dept in dept_options:
        default_dept = [st.session_state.quick_dept]

    dept = st.multiselect("Τμήμα", dept_options, default=default_dept)

with col2:
    prio_options = sorted(df_open["Προτ"].astype(str).unique().tolist())
    prio = st.multiselect("Προτεραιότητα (Προτ)", prio_options)

with col3:
    install_search = st.text_input("Αναζήτηση Εγκατάστασης (π.χ. L1, TWS)")

with col4:
    age_bucket = st.selectbox(
        "Παλαιότητα",
        ["Όλες", "> 7 μέρες", "> 30 μέρες"],
        index=0
    )

filtered = df_open[df_open["Τμήμα"].isin(dept)]

if prio:
    filtered = filtered[filtered["Προτ"].astype(str).isin(prio)]

if install_search.strip():
    filtered = filtered[filtered["Εγκατάσταση"].astype(str).str.contains(install_search.strip(), case=False, na=False)]

if age_bucket == "> 7 μέρες":
    filtered = filtered[filtered["Ημέρες_ανοικτή"] > 7]
elif age_bucket == "> 30 μέρες":
    filtered = filtered[filtered["Ημέρες_ανοικτή"] > 30]

# ----------------------------
# Σύνοψη + Παλαιότητα
# ----------------------------
summary = (
    filtered.groupby("Τμήμα")["Εντ.Συντήρ"]
    .count()
    .rename("Ανοιχτές (Κατάστ=Αποδεκ...)")
    .reset_index()
    .sort_values("Τμήμα")
)

# aging summary
aging = (
    filtered.groupby("Τμήμα")["Ημέρες_ανοικτή"]
    .agg(
        Σύνολο="count",
        Πάνω_από_7=lambda s: int((s > 7).sum()),
        Πάνω_από_30=lambda s: int((s > 30).sum()),
        Μέση_ηλικία_ημέρες=lambda s: round(float(pd.to_numeric(s, errors="coerce").mean()), 1) if len(s) else 0.0,
        Max_ημέρες=lambda s: int(pd.to_numeric(s, errors="coerce").max()) if len(s) else 0,
    )
    .reset_index()
    .sort_values("Τμήμα")
)

st.subheader("Σύνοψη")
st.dataframe(summary, use_container_width=True)

st.subheader("Παλαιότητα ανά τμήμα")
st.dataframe(aging, use_container_width=True)

# ----------------------------
# Λίστα
# ----------------------------
st.subheader("Λίστα ανοιχτών")
# ωραία στήλη σειράς/ταξινόμησης: πιο παλιές πρώτες
display_cols = ["Τμήμα", "Εντ.Συντήρ", "Εγκατάσταση", "Προτ", "Κατάστ", "Ημ/νία", "Ημέρες_ανοικτή", "Περιγραφή"]
for c in display_cols:
    if c not in filtered.columns:
        filtered[c] = ""

filtered_view = filtered[display_cols].copy()
filtered_view["Ημέρες_ανοικτή"] = pd.to_numeric(filtered_view["Ημέρες_ανοικτή"], errors="coerce")
filtered_view = filtered_view.sort_values(["Τμήμα", "Ημέρες_ανοικτή"], ascending=[True, False])

st.dataframe(filtered_view, use_container_width=True, height=520)

# ----------------------------
# Excel export
# ----------------------------
excel_bytes = make_excel_bytes(aging, filtered_view)
stamp = datetime.now().strftime("%Y%m%d_%H%M")
st.download_button(
    "⬇️ Κατέβασε Excel",
    data=excel_bytes,
    file_name=f"open_orders_with_aging_{stamp}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)




