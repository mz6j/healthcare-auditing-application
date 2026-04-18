import pandas as pd
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Report", layout="wide")
st.title("Report")
st.caption("This page allows you to generate a report of your expenses.")

df = st.session_state.get("df")
dataset_name = st.session_state.get("dataset_name", "Uploaded dataset")

if df is None:
    st.warning("Please upload a dataset to generate a report.")
    st.stop()

def dataset_summary(df: pd.DataFrame) -> dict:
    n_rows, cols = df.shape
    missing_cells = int(df.isna().sum().sum())
    n_cells = int(n_rows * cols) if n_rows and cols else 0
    pct_missing = (missing_cells / n_cells * 100) if n_cells else 0.0
    duplicates = int(df.duplicated().sum()) if n_rows else 0
    empty_cols = int((df.isna().mean() == 1.0).sum())
    constant_cols = sum(df[c].dropna().nunique() == 1 for c in df.columns)

    return {
        "rows": n_rows,
        "cols": cols,
        "missing_cells": missing_cells,
        "missing_pct": pct_missing,
        "duplicates": duplicates,
        "empty_cols": empty_cols,
        "constant_cols": int(constant_cols),
    }

def missingness_by_column(df: pd.DataFrame) -> pd.DataFrame:
    miss_count = df.isna().sum().sort_values(ascending=False)
    miss_pct = (df.isna().mean() * 100).sort_values(ascending=False)
    out = pd.DataFrame({
        "Missing Count": miss_count,
        "Missing Percentage": miss_pct
    })
    out["Missing Percentage"] = out["Missing Percentage"].round(2)
    out.index.name = "column"
    return out

def clean_cat(series: pd.Series, max_levels: int = 12) -> pd.Series:
    s = series.astype("string").fillna("missing")
    counts = s.value_counts()
    if len(counts) > max_levels:
        top = counts.index[:max_levels - 1]
        s = s.where(s.isin(top), other="other")
    return s

summary = dataset_summary(df)
miss_table = missingness_by_column(df)
analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

st.subheader("Dataset Summary")

col1, col2, col3 = st.columns(3)
col1.metric("Dataset", dataset_name)
col2.metric("Date of Analysis", analysis_date)
col3.metric("Rows Analysed", f"{summary['rows']:,}")

q1, q2, q3, q4 = st.columns(4)
q1.metric("Total Columns", summary["cols"])
q2.metric("Missing Cells", f"{summary['missing_cells']:,}", f"{summary['missing_pct']:.2f}%")
q3.metric("Duplicate Rows", summary["duplicates"])
q4.metric("Empty Columns", summary["empty_cols"])

st.write("**Missingness by Column:**")
st.dataframe(miss_table.head(5), use_container_width=True)

st.subheader("Demographic Summary")

all_columns = df.columns.tolist()
demo_cols = st.multiselect("Select demographic columns to analyze", options=all_columns, default=all_columns[:3])
if demo_cols:
    for col in demo_cols:
        st.write(f"**{col}**")
        cleaned = clean_cat(df[col])
        counts = cleaned.value_counts().head(10)
        st.bar_chart(counts)
else:
    st.info("Please select at least one demographic column to analyze.")

st.subheader("Recommendations")

recommendations = []

if summary["missing_pct"] >= 20:
    recommendations.append(f"Over 20% of all data cells are missing ({summary['missing_pct']:.2f}%). "
        "This is a significant concern and the dataset may not be reliable enough for analysis")
elif summary["missing_pct"] >= 10:
    recommendations.append(f"More than 10% of data cells are missing ({summary['missing_pct']:.2f}%). "
        "Review which columns are most affected and investigate why data was not recorded.")
if summary["duplicates"] > 0:
    recommendations.append(f"The dataset contains {summary['duplicates']} duplicate row(s). "
        "Duplicate records can distort results and should be removed before the data is used for analysis.")
if summary["empty_cols"] > 0:
    recommendations.append(f"{summary['empty_cols']} column(s) contain no data at all. "
        "These columns should be removed from the dataset.")
if summary["constant_cols"] > 0:
    recommendations.append(f"{summary['constant_cols']} column(s) contain the same value in every row. "
        "These columns do not provide any useful information and should be removed.")

top_missing = miss_table[miss_table["Missing Percentage"] > 30]
if not top_missing.empty:
    cols_listed = ", ".join(top_missing.index.tolist())
    recommendations.append("Focus on addressing columns with over 30% missing data.")

if demo_cols:
    for col in demo_cols:
        if pd.api.types.is_numeric_dtype(df[col]):
            continue
        if df[col].nunique() > len(df) * 0.5:
            continue
        cat = clean_cat(df[col])
        counts = cat.value_counts()
        pct = counts / counts.sum() * 100
        small = pct[pct < 5].index.tolist()
        if small:
            recommendations.append(f"In the '{col}' column, the following group(s) make up less than 5% of the dataset: "
                f"{', '.join(map(str, small))}. "
                "Small groups like these may not be well represented in the data, which could affect the fairness of any conclusions drawn from it."
)

if recommendations:
    for i, rec in enumerate(recommendations, 1):
        st.warning(f"{i}. {rec}")
else:
    st.success("No major issues detected. Your dataset looks good for analysis!")

st.subheader("Report Download")

st.info("You can download a detailed report of this analysis, including dataset summary, missingness details, demographic breakdowns, and recommendations.")

all_columns = df.columns.tolist()

demo_cols = st.multiselect(
        "Select demographic columns to include in the report",
        options=all_columns
)

def generate_report(dataset_name, analysis_date, summary, miss_table, demo_cols, df, recommendations):
    miss_rows = ""
    demo_html = ""
    rec_html = ""

    for col, row in miss_table.head(5).iterrows():
        miss_rows += f"<tr><td>{col}</td><td>{int(row['Missing Count'])}</td><td>{row['Missing Percentage']}%</td></tr>"

    if demo_cols:
        for col in demo_cols:
            cat = clean_cat(df[col])
            rep = cat.value_counts(dropna=False).rename_axis("group").reset_index(name="count")
            rep["pct"] = (rep["count"] / rep["count"].sum() * 100).round(2)
            demo_html += f"<h4>{col}</h4><table><tr><th>Group</th><th>Count</th><th>Percentage</th></tr>"
            for _, r in rep.iterrows():
                demo_html += f"<tr><td>{r['group']}</td><td>{r['count']}</td><td>{r['pct']}%</td></tr>"
            demo_html += "</table>"

    if recommendations:
        rec_html = "<ul>"
        for rec in recommendations:
            rec_html += f"<li>{rec}</li>"
        rec_html += "</ul>"
    else:
        rec_html = "<p>No major issues detected.</p>"

    demo_section = demo_html if demo_html else "<p>No demographic columns selected.</p>"

    html = f"""<html>
<head>
    <title>Data Report - {dataset_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Data Report</h1>
    <p><strong>Dataset:</strong> {dataset_name}</p>
    <p><strong>Analysis Date:</strong> {analysis_date}</p>

    <h2>Dataset Summary</h2>
    <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Total Rows</td><td>{summary["rows"]:,}</td></tr>
        <tr><td>Total Columns</td><td>{summary["cols"]}</td></tr>
        <tr><td>Missing Cells</td><td>{summary["missing_cells"]:,} ({summary["missing_pct"]:.2f}%)</td></tr>
        <tr><td>Duplicate Rows</td><td>{summary["duplicates"]}</td></tr>
        <tr><td>Empty Columns</td><td>{summary["empty_cols"]}</td></tr>
    </table>

    <h2>Top 5 Columns by Missingness</h2>
    <table>
        <tr><th>Column</th><th>Missing Count</th><th>Missing %</th></tr>
        {miss_rows}
    </table>

    <h2>Demographic Summary</h2>
    {demo_section}

    <h2>Recommendations</h2>
    {rec_html}

</body>
</html>"""

    return html

html_report = generate_report(dataset_name, analysis_date, summary, miss_table, demo_cols, df, recommendations)

st.download_button(
    label="Download Report",
    data=html_report,
    file_name=f"{dataset_name}_report.html",
    mime="text/html"
)
