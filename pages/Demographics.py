import streamlit as st
import pandas as pd

st.set_page_config(page_title="Demographics", layout="wide")
st.title("Demographics")

df = st.session_state.get("df")
if df is None:
    st.warning("Please upload a dataset first!")
    st.stop()

# Tidies up a column by filling blank values with the word "Missing"
# and grouping any rare categories beyond the top 12 into one "Other" bucket
# so the chart does not get too cluttered.
def clean_cat(s: pd.Series, max_levels: int = 12) -> pd.Series:
    s = s.astype("string").fillna("Missing")
    vc = s.value_counts()
    if len(vc) > max_levels:
        top = vc.nlargest(max_levels).index
        s = s.where(s.isin(top), other="Other")
    return s

st.subheader("Categorical Columns")
cols = df.columns[df.dtypes == "object"].tolist()

demo_cols = st.multiselect("Select categorical columns to clean", options=cols, default=cols)
if not demo_cols:
    st.info("No columns selected.")
    st.stop()

st.subheader("Cleaned Categorical Data")
for col in demo_cols:
    st.markdown(f"**{col}**")
    if pd.api.types.is_numeric_dtype(df[col]):
        # Instead of showing every individual age, pd.cut groups numbers
        # into ranges like "20-29" and "30-39" to make the chart readable.
        band = st.slider(f"Age band size for {col} (optional)", 5, 20, 10, key=f"band_{col}")
        x = pd.to_numeric(df[col], errors="coerce")
        if x.notna().sum() == 0:
            st.warning(f"Column {col} could not be converted to numeric. Skipping.")
            continue
        min, max = int(x.min()), int(x.max())
        bins = list(range((min // band) * band, ((max // band) + 1) * band + 1, band))
        labels = [f"{b}-{b+band-1}" for b in bins[:-1]]
        cat = pd.cut(x, bins=bins, labels=labels, include_lowest=True).astype("string").fillna("Missing")
    else:
        cat = clean_cat(df[col])

# dropna=False makes sure missing values show up as their own row.
    rep = cat.value_counts(dropna=False).rename_axis("group").reset_index(name="count")
    rep["pct"] = (rep["count"] / rep["count"].sum() * 100).round(2)
    left, right = st.columns(2)
    with left:
        st.dataframe(rep, use_container_width=True)
    with right:
        st.bar_chart(rep.set_index("group")["count"], use_container_width=True)

st.subheader("Subgroup Analysis")
group_col = st.selectbox("Select a column to group by", options=demo_cols)
group = clean_cat(df[group_col])

candidate = [c for c in df.columns.tolist() if c not in demo_cols]
if not candidate:
    st.warning("No non-demographic columns available for subgroup analysis.")
    st.stop()

focus = st.selectbox(
    "Select a column to analyze by group",
    options=candidate,
    index=0
)

tmp = pd.DataFrame({"group": group, "miss": df[focus].isna()})

group_missing = tmp.groupby("group")["miss"].mean().reset_index()
group_missing["missing_pct"] = (group_missing["miss"] * 100).round(2)

st.dataframe(group_missing[["group", "missing_pct"]], use_container_width=True)
st.bar_chart(group_missing.set_index("group")["missing_pct"], use_container_width=True)

st.subheader("Flags and Issues")
flags = []

# Any group below 5% of the dataset is flagged as potentially under-represented.
for col in demo_cols:
    if pd.api.types.is_numeric_dtype(df[col]):
        continue
    cat = clean_cat(df[col])
    vc = cat.value_counts(dropna=False)
    pct = (vc / vc.sum() * 100).round(2)
    small = pct[pct < 5].index.tolist()
    if small:
        flags.append(f"Column '{col}' has small groups: {', '.join(small)}")

# A missingness gap of 15% or more between the highest and lowest group
# is flagged as a potential fairness risk.
if len(group_missing) >= 2:
    gap = float(group_missing["missing_pct"].max() - group_missing["missing_pct"].min())
    if gap >= 15:
        flags.append(f"Missingness gap of {gap:.2f}% between groups in column '{group_col}'")
        

if flags:
    for f in flags:
        st.warning(f)
else:
    st.success("No major issues detected in demographics analysis!")
