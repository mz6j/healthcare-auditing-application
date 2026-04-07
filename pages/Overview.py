import streamlit as st
import pandas as pd

st.set_page_config(page_title="Overview", layout="wide")
st.title("Overview")
st.caption("Sprint 2")

df = st.session_state.get("df", None)
dataset_name = st.session_state.get("dataset_name", "Uploaded dataset")

if df is None:
    st.warning("Please upload a dataset first!")
    st.stop()

def dataset_summary(df: pd.DataFrame) -> dict:
    n_rows, n_cols = df.shape
    n_missing = int(df.isna().sum().sum())
    n_cells = int(n_rows * n_cols) if n_rows and n_cols else 0
    pct_missing = (n_missing / n_cells * 100) if n_cells else 0.0
    duplicates = int(df.duplicated().sum()) if n_rows else 0
    empty_cols = int((df.isna().mean() == 1.0).sum())
    constant_cols = sum(df[c].dropna().nunique() == 1 for c in df.columns)

    return {
        "Rows": n_rows,
        "Columns": n_cols,
        "Missing Cells": n_missing,
        "Missing PCT": pct_missing,
        "Duplicates": duplicates,
        "Empty Columns": empty_cols,
        "Constant Columns": int(constant_cols),
    }

def missingness_by_column(df: pd.DataFrame) -> pd.DataFrame:
    miss_count = df.isna().sum().sort_values(ascending=False)
    miss_pct = (df.isna().mean() * 100).sort_values(ascending=False)
    out = pd.DataFrame({#
        "Missing Count": miss_count,
        "Missing PCT": miss_pct
    })
    out["Missing PCT"] = out["Missing PCT"].round(2)
    out.index.name = "Column"
    return out

def schema_summary(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "Column": df.columns,
        "Data Type": [str(t) for t in df.dtypes],
        "non_null": df.notna().sum().values,
        "unique_non_null": [df[c].dropna().nunique() for c in df.columns],
    })

summary = dataset_summary(df)
miss_table = missingness_by_column(df)
schema_table = schema_summary(df)

st.subheader("Dataset Summary")
st.write(f"**Dataset:** {dataset_name}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Rows", f"{summary['Rows']:,}")
col2.metric("Columns", f"{summary['Columns']:,}")
col3.metric("Missing Cells", f"{summary['Missing Cells']:,} ({summary['Missing PCT']:.2f}%)")
col4.metric("Duplicates", f"{summary['Duplicates']:,}")

st.subheader("Flagged Quality Issues")

flags = []
if summary["Empty Columns"] > 0:
    flags.append(f"{summary['Empty Columns']} columns are completely empty")
if summary["Constant Columns"] > 0:
    flags.append(f"{summary['Constant Columns']} columns contain single repeated value")
if summary["Missing PCT"] >= 10:
    flags.append(f"{summary['Missing PCT']:.2f}% of cells are missing")
if summary["Duplicates"] > 0:
    flags.append(f"{summary['Duplicates']:,} duplicate detected")

if flags:
    for msg in flags:
        st.warning(msg)
else:
    st.success("No major quality issues detected!")

st.subheader("Missingness by Column")

max_show = min(30, summary["Columns"])
top_n = st.slider("Show top N columns with highest missingness", min_value=5, max_value=max_show, value=min(10, max_show))
st.dataframe(miss_table.head(top_n), use_container_width=True)
st.write("**Missingness chart (top columns)**")
st.bar_chart(miss_table.head(top_n)["Missing PCT"])
st.subheader("Schema Summary")
st.write("Overview of column data types and uniqueness")
st.dataframe(schema_table, use_container_width=True)

with st.expander("Preview dataset (first 10 rows)"):
    st.dataframe(df.head(10), use_container_width=True)