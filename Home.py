import streamlit as st
import pandas as pd

st.write("Theme config loaded test ✅")

st.set_page_config(
    page_title="Data Auditing Application",
    layout="wide"
)

# Reads the CSS file and injects it into the page using a <style> tag.
# The try/except ensures the app still loads even if the CSS file is missing.
def load_css(path: str) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("style.css not found")

load_css("assets/style.css")

# Converts the uploaded file into a pandas DataFrame based on its extension.
# .lower() is used so that files named .CSV or .XLSX are still recognised correctly.
def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    if uploaded_file is None:
        return pd.DataFrame()
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if name.endswith(".xlsx") or name.endswith(".xls"):
        return pd.read_excel(uploaded_file)
    
    raise ValueError("Unsupported file type.")

st.markdown("""
    <div class="header">
        <div class="app-title">Data Auditing Application</div>
        <div class="app-subtitle">Designed to automate bias and assess data quality</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="card-row">
    <div class="card">
        <h3>Bias Detection</h3>
        <p>Highlights any gaps in the representation of demographics that could introduce bias into the analysis.</p>
    </div>
    <div class="card">
        <h3>Quality Assessment</h3>
        <p>Built to check for missingness pattern and potential outliers.</p>
    </div>
    <div class="card">
        <h3>Actionable Insights</h3>
        <p>Designed to generate a clear summary and recommendations to improve fairness and quality.</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="upload-panel">
    <h2>Upload a dataset</h2>
    <h3>Please ensure it is a CSV or Excel file</h3>
</div>
""", unsafe_allow_html=True)

# Restricts uploads to CSV and Excel only
uploaded = st.file_uploader(
    label="",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=False
)

# Streamlit re-runs the entire script on every interaction, session state is used to persist
#  the uploaded DataFrame and its name across interactions without needing to re-upload.     
if "df" not in st.session_state:
    st.session_state["df"] = None
if "dataset_name" not in st.session_state:
    st.session_state["dataset_name"] = None

if uploaded is not None:
    try:
        # Store both the DataFrame and filename so all other pages can access them.
        df = read_uploaded_file(uploaded)
        st.session_state["df"] = df
        st.session_state["dataset_name"] = uploaded.name

        st.markdown(
            f"""
            <div class="loaded-box">
                <b>Dataset loaded successfully</b>
                <div><strong>Rows:</strong> {len(df):,} &nbsp;&nbsp; <string>Columns:</strong> {df.shape[1]}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"Could not read file: {e}")

    st.markdown("""
    <div class="privacy">
        <strong>Privacy & Security</strong>
        <span>Data will not be store permenently and is only processed within the active session.</span>
    </div>
    """, unsafe_allow_html=True)