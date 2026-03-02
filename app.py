import io
import re
from pathlib import Path
from datetime import datetime, date

import pdfplumber
import pandas as pd
import streamlit as st


# ----------------------------
# Patterns for Access PDF lines
# Expected start:  Ημ/νία  Εντολή  Βάρδια  Τμήμα_κωδ ...
# Example:        6/7/25  434190  2       2DA1 ...
# ----------------------------
DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2}$")        # 6/7/25
ORDER_RE = re.compile(r"^\d{5,8}$")                    # 434190
SHIFT_RE = re.compile(r"^\d+$")                        # 1,2,3
DEPTCODE_RE = re.compile(r"^[123S][A-Z0-9]{2,6}$")     # 2DA1, 3DW1, 3T08, 2TS1, S...


def dept_from_access_deptcode(code: str) -> str:
    c = (code or "").strip().upper()
    if c.startswith("1"):
        return "Γραμμή 1"
    if c.startswith("2"):
        return "Γραμμή 2"
    if c.startswith("3"):
        return "Γραμμή 3"
    if c.startswith("S"):
        return "Τραμ"
    return "Άγνωστο"


def parse_access_line(line: str) -> dict | None:
    """
    Robust token parsing.
    Needs at least: date, order, shift, dept_code in the first tokens.
    """
    line = (line or "").strip()
    if not line:
        return None

    tokens = line.split()
    if len(tokens) < 4:
        return None

    # date
    if not DATE_RE.match(tokens[0]):
        return None
    # order
    if not ORDER_RE.match(tokens[1]):
        return None
    # shift
    if not SHIFT_RE.match(tokens[2]):
        return None

    # dept code normally at token[3], but we also scan a little forward just in case
    dept_code = tokens[3].strip().upper()
    if not DEPTCODE_RE.match(dept_code):
        dept_code = ""
        for t in tokens[3:10]:
            t2 = t.strip().upper()
            if DEPTCODE_RE.match(t2):
                dept_code = t2
                break

    return {
        "Τμήμα": dept_from_access_deptcode(dept_code),
        "Εντολή": tokens[1],
        "Ημ/νία": tokens[0],
        "Βάρδια": tokens[2],
        "Τμήμα_κωδ": dept_code,
        "Raw": line,
    }


def extract_open_from_access_pdf(file_bytes: bytes) -> pd.DataFrame:
    rows = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                row = parse_access_line(line)
                if row:
                    rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        df["Ημ/νία_dt"] = pd.to_datetime(df["Ημ/νία"], format="%d/%m/%y", errors="coerce")
        today = pd.Timestamp(date.today())
        df["Ημέρες_ανοικτή"] = (today - df["Ημ/νία_dt"]).dt.days
    return df


def make_excel_bytes(summary_df: pd.DataFrame, details_df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Σύνοψη", index=False)
        details_df.to_excel(writer, sheet_name="Ανοιχτές_Λίστα", index=False)
    return output.getvalue()


# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Access Open Orders", layout="wide")
st.title("Ανοιχτές (Κενές) Εντολές Εργασίας από Access PDF (Repo Mode)")

DEFAULT_PDF_PATH = Path(__file__).parent / "data" / "access_open.pdf"

# Header / refresh
left, right = st.columns([3, 1])
with right:
    if st.button("🔄 Ανανέωση", use_container_width=True):
        st.rerun()

# Load PDF from repo
if DEFAULT_PDF_PATH.exists():
    file_bytes = DEFAULT_PDF_PATH.read_bytes()
    pdf_mtime = datetime.fromtimestamp(DEFAULT_PDF_PATH.stat().st_mtime)
    st.caption(
        f"📄 PDF: data/access_open.pdf — τελευταία ενημέρωση: {pdf_mtime.strftime('%d/%m/%Y %H:%M')} "
        f"— μέγεθος: {len(file_bytes)} bytes"
    )
else:
    st.error("Δεν βρέθηκε το αρχείο: data/access_open.pdf μέσα στο repo.")
    st.info("Ανέβασέ το στο GitHub στον φάκελο data/ με όνομα access_open.pdf.")
    # optional fallback uploader
    uploaded = st.file_uploader("Εναλλακτικά, ανέβασε το PDF εδώ", type=["pdf"])
    if uploaded is None:
        st.stop()
    file_bytes = uploaded.read()
    st.success(f"Ανέβηκε προσωρινά: {uploaded.name} ({len(file_bytes)} bytes)")

df_open = extract_open_from_access_pdf(file_bytes)

if df_open.empty:
    st.error("Δεν βρέθηκαν γραμμές εντολών μέσα στο PDF. (Ίσως άλλαξε το layout).")
    st.stop()

# ---------------- Quick filters ----------------
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

# ---------------- Filters ----------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    dept_options = sorted(df_open["Τμήμα"].unique().tolist())
    default_dept = dept_options
    if st.session_state.quick_dept != "Όλα" and st.session_state.quick_dept in dept_options:
        default_dept = [st.session_state.quick_dept]
    dept = st.multiselect("Τμήμα", dept_options, default=default_dept)

with col2:
    shift_options = sorted(df_open["Βάρδια"].astype(str).unique().tolist())
    shift = st.multiselect("Βάρδια", shift_options, default=shift_options)

with col3:
    age_bucket = st.selectbox("Παλαιότητα", ["Όλες", "> 7 μέρες", "> 30 μέρες"], index=0)

with col4:
    order_search = st.text_input("Αναζήτηση Εντολής (π.χ. 434190)")

filtered = df_open[df_open["Τμήμα"].isin(dept)].copy()
filtered = filtered[filtered["Βάρδια"].astype(str).isin(shift)]

if age_bucket == "> 7 μέρες":
    filtered = filtered[filtered["Ημέρες_ανοικτή"] > 7]
elif age_bucket == "> 30 μέρες":
    filtered = filtered[filtered["Ημέρες_ανοικτή"] > 30]

if order_search.strip():
    filtered = filtered[filtered["Εντολή"].astype(str).str.contains(order_search.strip(), na=False)]

# ---------------- Summary ----------------
summary = (
    filtered.groupby("Τμήμα")["Εντολή"]
    .count()
    .rename("Ανοιχτές (Access)")
    .reset_index()
    .sort_values("Τμήμα")
)

aging = (
    filtered.groupby("Τμήμα")["Ημέρες_ανοικτή"]
    .agg(
        Σύνολο="count",
        Πάνω_από_7=lambda s: int((s > 7).sum()),
        Πάνω_από_30=lambda s: int((s > 30).sum()),
        Max_ημέρες=lambda s: int(pd.to_numeric(s, errors="coerce").max()) if len(s) else 0,
    )
    .reset_index()
    .sort_values("Τμήμα")
)

st.subheader("Σύνοψη ανά τμήμα")
st.dataframe(summary, use_container_width=True)

st.subheader("Παλαιότητα ανά τμήμα")
st.dataframe(aging, use_container_width=True)

# ---------------- Details ----------------
st.subheader("Λίστα ανοιχτών")
show_cols = ["Τμήμα", "Εντολή", "Ημ/νία", "Ημέρες_ανοικτή", "Βάρδια", "Τμήμα_κωδ", "Raw"]
filtered_view = filtered[show_cols].sort_values(["Τμήμα", "Ημέρες_ανοικτή"], ascending=[True, False])
st.dataframe(filtered_view, use_container_width=True, height=520)

# ---------------- Export ----------------
excel_bytes = make_excel_bytes(aging, filtered_view)
stamp = datetime.now().strftime("%Y%m%d_%H%M")
st.download_button(
    "⬇️ Κατέβασε Excel",
    data=excel_bytes,
    file_name=f"access_open_orders_{stamp}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)






