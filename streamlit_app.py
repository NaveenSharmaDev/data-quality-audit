import io
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from audit_engine import DataQualityAuditor


# Configuration

st.set_page_config(
    page_title="Data Quality Audit | Task 24",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Styling

st.markdown(
    """
    <style>
        :root {
            --navy: #102b50;
            --blue: #1267e8;
            --light: #f4f8fc;
            --border: #dce6f2;
        }

        .block-container {
            padding-top: 1rem;
            padding-bottom: 1.5rem;
            max-width: 1500px;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(
                180deg,
                #0e2b50 0%,
                #12375f 100%
            );
        }

        [data-testid="stSidebar"] * {
            color: #ffffff !important;
        }

        .hero {
            background: linear-gradient(
                110deg,
                #102b50,
                #1f4d82
            );
            padding: 18px 26px;
            border-radius: 16px;
            color: white;
            margin-bottom: 14px;
            box-shadow: 0 6px 18px rgba(16, 43, 80, 0.12);
        }

        .hero h1 {
            margin: 0;
            font-size: 32px;
        }

        .hero p {
            margin: 4px 0 0;
            opacity: 0.9;
        }

        .metric-card {
            background: white;
            border: 1px solid var(--border);
            border-radius: 15px;
            padding: 16px 18px;
            min-height: 118px;
            box-shadow: 0 3px 12px rgba(20, 50, 90, 0.06);
        }

        .metric-title {
            color: #30435e;
            font-size: 15px;
        }

        .metric-value {
            color: #0c1e38;
            font-size: 30px;
            font-weight: 750;
            margin-top: 3px;
        }

        .metric-note {
            color: #72839a;
            font-size: 12px;
        }

        .section-card {
            background: white;
            border: 1px solid var(--border);
            border-radius: 15px;
            padding: 14px 16px;
            box-shadow: 0 3px 12px rgba(20, 50, 90, 0.05);
        }

        .small-note {
            color: #64748b;
            font-size: 13px;
        }

        div[data-testid="stFileUploader"] {
            background: white;
            border-radius: 12px;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 10px;
            font-weight: 600;
        }

        .footer {
            background: #e8f8ef;
            padding: 11px 16px;
            border-radius: 12px;
            color: #155d38;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# Session State

DEFAULT_STATE = {
    "df": None,
    "source_name": "",
    "result": None,
    "cleaned": None,
    "actions": [],
}


for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# Helper Functions

def load_dataset(uploaded_file):
    """Load CSV or Excel dataset."""
    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    return pd.read_excel(uploaded_file)


def normalize_columns(df):
    """Remove unnecessary spaces from column names."""
    cleaned_df = df.copy()
    cleaned_df.columns = [str(column).strip() for column in cleaned_df.columns]
    return cleaned_df


def get_issue_table(result):
    """Convert audit issues into a DataFrame."""
    return pd.DataFrame(result["issues"])


def create_excel_report(df, result, cleaned_df):
    """Create downloadable Excel audit report."""
    buffer = io.BytesIO()

    issues = get_issue_table(result)
    checklist = pd.DataFrame(result["checklist"])

    missing_values = pd.DataFrame(
        [
            {
                "Column": column,
                "Missing_Count": count,
            }
            for column, count in result["missing_by_column"].items()
        ]
    )

    summary = pd.DataFrame(
        [
            {
                "Project": "Data Quality Audit — Task 24",
                "Source": st.session_state.source_name,
                "Audit Time": result["audited_at"],
                "Rows": result["row_count"],
                "Columns": result["column_count"],
                "Total Issues": result["total_issues"],
                "Quality Score (%)": round(result["quality_score"], 2),
            }
        ]
    )

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        summary.to_excel(
            writer,
            sheet_name="Summary",
            index=False,
        )

        issues.to_excel(
            writer,
            sheet_name="Issue Log",
            index=False,
        )

        checklist.to_excel(
            writer,
            sheet_name="Checklist",
            index=False,
        )

        missing_values.to_excel(
            writer,
            sheet_name="Missing Values",
            index=False,
        )

        df.head(5000).to_excel(
            writer,
            sheet_name="Original Sample",
            index=False,
        )

        cleaned_df.head(5000).to_excel(
            writer,
            sheet_name="Cleaned Sample",
            index=False,
        )

    return buffer.getvalue()


def run_audit():
    """Run data quality audit and cleaning."""
    if st.session_state.df is None or st.session_state.df.empty:
        st.error("Please load a non-empty dataset first.")
        return

    auditor = DataQualityAuditor()

    st.session_state.result = auditor.audit(
        st.session_state.df
    )

    (
        st.session_state.cleaned,
        st.session_state.actions,
    ) = auditor.clean(
        st.session_state.df
    )


def reset_dataset(df, source_name):
    """Update dataset-related session state."""
    st.session_state.df = normalize_columns(df)
    st.session_state.source_name = source_name
    st.session_state.result = None
    st.session_state.cleaned = None
    st.session_state.actions = []


# Sidebar

with st.sidebar:
    st.markdown("## 🗄️ Data Quality Audit")
    st.caption("Task 24 • Data Analytics")
    st.divider()

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Upload Data",
            "Data Overview",
            "Quality Checks",
            "Issue Report",
            "Cleaned Data",
            "Downloads",
            "Help",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown("### Dataset")

    uploaded_file = st.file_uploader(
        "Upload CSV / Excel",
        type=["csv", "xlsx", "xls"],
        key="sidebar_upload",
    )

    if uploaded_file is not None:
        try:
            dataset = load_dataset(uploaded_file)

            reset_dataset(
                dataset,
                uploaded_file.name,
            )

            st.success(
                f"Loaded {len(dataset):,} rows"
            )

        except Exception as exc:
            st.error(
                f"Could not load file: {exc}"
            )

    if st.button(
        "Use Demo Retail Data",
        width="stretch",
    ):
        demo_path = (
            Path(__file__).resolve().parent
            / "data"
            / "retail_sales_demo_large.csv"
        )

        if demo_path.exists():
            demo_df = pd.read_csv(demo_path)

            reset_dataset(
                demo_df,
                demo_path.name,
            )

            st.rerun()

    if st.session_state.df is not None:
        if st.button(
            "▶ Run All Quality Checks",
            type="primary",
            width="stretch",
        ):
            run_audit()
            st.session_state.page_force = "Dashboard"
            st.rerun()

    st.markdown("---")
    st.caption("Quality Data Builds Better Solutions")
    st.caption("© 2026 | VEDA Technology")


# Main Header

st.markdown(
    """
    <div class="hero">
        <h1>🗄️ Data Quality Audit</h1>
        <p>
            Clean Data &nbsp;•&nbsp;
            Better Insights &nbsp;•&nbsp;
            Trusted Decisions
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


header_left, header_right = st.columns([4, 1])

with header_left:
    st.markdown("## Welcome, Naveen 👋")
    st.markdown("**Data Quality Audit | Task 24**")
    st.caption(
        "Audit a dataset for missing, duplicate, "
        "range, and consistency issues."
    )

with header_right:
    if st.session_state.df is not None:
        st.info(
            f"📄 {st.session_state.source_name}"
        )


# Dashboard

if page == "Dashboard":

    if st.session_state.df is None:
        st.info(
            "Load a CSV/Excel file from the sidebar "
            "or click **Use Demo Retail Data**."
        )
        st.stop()

    if st.session_state.result is None:
        run_audit()

    result = st.session_state.result
    df = st.session_state.df
    issues = get_issue_table(result)

    metric_columns = st.columns(5)

    metrics = [
        (
            "🗄️",
            "Total Records",
            f"{len(df):,}",
            "Rows in dataset",
        ),
        (
            "✓",
            "Total Columns",
            f"{len(df.columns):,}",
            "Features detected",
        ),
        (
            "⚠️",
            "Data Issues",
            f"{result['total_issues']:,}",
            "Audit findings",
        ),
        (
            "👥",
            "Duplicate Records",
            f"{result['counts']['Duplicate']:,}",
            "Duplicate rule findings",
        ),
        (
            "◔",
            "Missing Values",
            f"{sum(result['missing_by_column'].values()):,}",
            "Across all columns",
        ),
    ]

    for column, metric in zip(
        metric_columns,
        metrics,
    ):
        icon, title, value, note = metric

        with column:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">
                        {icon} {title}
                    </div>
                    <div class="metric-value">
                        {value}
                    </div>
                    <div class="metric-note">
                        {note}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")

    left, middle, right = st.columns(
        [1.05, 1.05, 0.85]
    )

    # Quality Summary

    with left:
        st.markdown(
            '<div class="section-card">',
            unsafe_allow_html=True,
        )

        st.subheader("Data Quality Summary")

        total_cells = max(
            1,
            len(df) * len(df.columns),
        )

        missing_count = sum(
            result["missing_by_column"].values()
        )

        duplicate_count = (
            result["counts"]["Duplicate"]
        )

        range_issues = (
            result["counts"]["Range"]
        )

        consistency_issues = (
            result["counts"]["Consistency"]
        )

        invalid_cells = min(
            total_cells,
            missing_count
            + range_issues
            + consistency_issues,
        )

        valid_percentage = max(
            0,
            100
            * (total_cells - invalid_cells)
            / total_cells,
        )

        summary_df = pd.DataFrame(
            {
                "Status": [
                    "Valid Data",
                    "Missing Values",
                    "Duplicates",
                    "Invalid/Out of Range",
                ],
                "Count": [
                    max(
                        0,
                        int(
                            total_cells
                            - invalid_cells
                        ),
                    ),
                    missing_count,
                    duplicate_count,
                    range_issues,
                ],
            }
        )

        figure = px.pie(
            summary_df,
            names="Status",
            values="Count",
            hole=0.58,
            title=(
                f"{valid_percentage:.1f}% Valid Data"
            ),
        )

        figure.update_layout(
            height=330,
            margin=dict(
                l=10,
                r=10,
                t=55,
                b=10,
            ),
            showlegend=True,
        )

        st.plotly_chart(
            figure,
            width="stretch",
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    # Issues by Type

    with middle:
        st.markdown(
            '<div class="section-card">',
            unsafe_allow_html=True,
        )

        st.subheader("Issues by Type")

        issue_type_counts = pd.DataFrame(
            {
                "Issue Type": [
                    "Missing Values",
                    "Duplicates",
                    "Out of Range",
                    "Data Inconsistency",
                ],
                "Count": [
                    missing_count,
                    duplicate_count,
                    range_issues,
                    consistency_issues,
                ],
            }
        )

        figure = px.bar(
            issue_type_counts,
            x="Issue Type",
            y="Count",
            text="Count",
        )

        figure.update_traces(
            textposition="outside"
        )

        figure.update_layout(
            height=330,
            margin=dict(
                l=10,
                r=10,
                t=20,
                b=10,
            ),
            xaxis_title="",
            yaxis_title="",
        )

        st.plotly_chart(
            figure,
            width="stretch",
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    # Top Columns

    with right:
        st.markdown(
            '<div class="section-card">',
            unsafe_allow_html=True,
        )

        st.subheader("Top 5 Columns with Issues")

        if not issues.empty:

            column_issues = (
                issues[
                    issues["column"] != "__row__"
                ]
                .groupby("column")
                .size()
                .reset_index(name="Issues")
                .sort_values(
                    "Issues",
                    ascending=False,
                )
                .head(5)
            )

            figure = px.bar(
                column_issues.sort_values(
                    "Issues"
                ),
                x="Issues",
                y="column",
                orientation="h",
                text="Issues",
            )

            figure.update_traces(
                textposition="outside"
            )

            figure.update_layout(
                height=330,
                margin=dict(
                    l=5,
                    r=20,
                    t=20,
                    b=10,
                ),
                xaxis_title="",
                yaxis_title="",
            )

            st.plotly_chart(
                figure,
                width="stretch",
            )

        else:
            st.success("No issues found.")

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    # Validation and Preview

    st.write("")

    validation_column, preview_column = st.columns(
        [1.05, 1.2]
    )

    with validation_column:
        st.markdown(
            '<div class="section-card">',
            unsafe_allow_html=True,
        )

        st.subheader(
            "Recent Validation Results"
        )

        if issues.empty:
            st.success(
                "No audit issues detected."
            )
        else:
            preview = issues[
                [
                    "column",
                    "type",
                    "description",
                    "severity",
                ]
            ].head(10).copy()

            preview.columns = [
                "Column",
                "Check Type",
                "Issues Found / Description",
                "Status",
            ]

            st.dataframe(
                preview,
                width="stretch",
                hide_index=True,
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    with preview_column:
        st.markdown(
            '<div class="section-card">',
            unsafe_allow_html=True,
        )

        st.subheader("Data Preview")

        st.dataframe(
            df.head(8),
            width="stretch",
            hide_index=True,
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    st.write("")

    st.markdown(
        """
        <div class="footer">
            🍀 Data cleaning today, better decisions tomorrow!
            <span style="float:right">
                Built with ❤️ using Python & Streamlit
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Upload Data

elif page == "Upload Data":

    st.header("Upload Data")

    st.write(
        "Upload a CSV or Excel dataset. "
        "The application automatically profiles it "
        "and prepares it for validation."
    )

    uploaded_file = st.file_uploader(
        "Choose dataset",
        type=["csv", "xlsx", "xls"],
        key="main_upload",
    )

    if uploaded_file:

        try:
            dataset = load_dataset(
                uploaded_file
            )

            reset_dataset(
                dataset,
                uploaded_file.name,
            )

            st.success(
                f"Loaded **{len(dataset):,} rows × "
                f"{len(dataset.columns):,} columns**."
            )

            st.dataframe(
                dataset.head(20),
                width="stretch",
            )

        except Exception as exc:
            st.error(str(exc))


# Data Overview

elif page == "Data Overview":

    st.header("Data Overview")

    if st.session_state.df is None:
        st.warning("Load a dataset first.")

    else:
        df = st.session_state.df

        row_metric, column_metric, numeric_metric, text_metric = (
            st.columns(4)
        )

        row_metric.metric(
            "Rows",
            f"{len(df):,}",
        )

        column_metric.metric(
            "Columns",
            f"{len(df.columns):,}",
        )

        numeric_metric.metric(
            "Numeric",
            f"{len(df.select_dtypes(include='number').columns):,}",
        )

        text_metric.metric(
            "Text",
            f"{len(df.select_dtypes(include=['object', 'string']).columns):,}",
        )

        st.subheader("Dataset Preview")

        st.dataframe(
            df,
            width="stretch",
            height=480,
        )

        st.subheader("Column Profile")

        profile = pd.DataFrame(
            {
                "Column": df.columns,
                "Data Type": [
                    str(df[column].dtype)
                    for column in df.columns
                ],
                "Non-Null": [
                    int(df[column].notna().sum())
                    for column in df.columns
                ],
                "Missing": [
                    int(df[column].isna().sum())
                    for column in df.columns
                ],
                "Unique": [
                    int(
                        df[column]
                        .nunique(dropna=True)
                    )
                    for column in df.columns
                ],
            }
        )

        st.dataframe(
            profile,
            width="stretch",
            hide_index=True,
        )


# Quality Checks

elif page == "Quality Checks":

    st.header("Quality Checks")

    if st.session_state.df is None:
        st.warning("Load a dataset first.")

    else:

        if st.button(
            "▶ Run All Quality Checks",
            type="primary",
        ):
            run_audit()

        if st.session_state.result:

            result = st.session_state.result

            st.success(
                f"Audit completed at "
                f"{result['audited_at']} • "
                f"Quality Score: "
                f"{result['quality_score']:.1f}%"
            )

            checklist = pd.DataFrame(
                result["checklist"]
            )

            st.dataframe(
                checklist,
                width="stretch",
                hide_index=True,
            )

            st.subheader(
                "Validation Rules"
            )

            st.markdown(
                """
                - **Missing:** null and blank values by column.
                - **Duplicate:** exact duplicate records.
                - **Range:** negative values in common business measures; 0–100 for percentage fields.
                - **Date validity:** unparseable values in likely date/time columns.
                - **Text consistency:** leading/trailing whitespace and case-only category variants.
                - **Retail arithmetic:** Sales versus Quantity × Unit Price when those columns exist.
                """
            )


# Issue Report

elif page == "Issue Report":

    st.header("Issue Report")

    if st.session_state.df is None:
        st.warning("Load a dataset first.")

    else:

        if st.session_state.result is None:
            run_audit()

        issues = get_issue_table(
            st.session_state.result
        )

        if issues.empty:
            st.success(
                "No issues detected."
            )

        else:

            filter_type = st.selectbox(
                "Filter issue type",
                [
                    "All",
                    "Missing",
                    "Duplicate",
                    "Range",
                    "Consistency",
                ],
            )

            if filter_type == "All":
                displayed_issues = issues
            else:
                displayed_issues = issues[
                    issues["type"] == filter_type
                ]

            st.metric(
                "Findings displayed",
                len(displayed_issues),
            )

            st.dataframe(
                displayed_issues,
                width="stretch",
                height=520,
                hide_index=True,
            )


# Cleaned Data

elif page == "Cleaned Data":

    st.header("Cleaned Data")

    if st.session_state.df is None:
        st.warning("Load a dataset first.")

    else:

        if st.session_state.result is None:
            run_audit()

        if st.session_state.cleaned is None:

            auditor = DataQualityAuditor()

            (
                st.session_state.cleaned,
                st.session_state.actions,
            ) = auditor.clean(
                st.session_state.df
            )

        for action in st.session_state.actions:
            st.write("✓", action)

        before, after = st.columns(2)

        before.metric(
            "Original rows",
            f"{len(st.session_state.df):,}",
        )

        after.metric(
            "Cleaned rows",
            f"{len(st.session_state.cleaned):,}",
        )

        st.dataframe(
            st.session_state.cleaned,
            width="stretch",
            height=500,
        )


# Downloads

elif page == "Downloads":

    st.header("Downloads")

    if st.session_state.df is None:
        st.warning("Load a dataset first.")

    else:

        if st.session_state.result is None:
            run_audit()

        auditor = DataQualityAuditor()

        if st.session_state.cleaned is None:

            (
                st.session_state.cleaned,
                st.session_state.actions,
            ) = auditor.clean(
                st.session_state.df
            )

        result = st.session_state.result
        issues = get_issue_table(result)

        st.subheader(
            "Submission Deliverables"
        )

        st.write(
            "Export the files below for your "
            "VEDA Technology Task 24 submission."
        )

        st.download_button(
            "⬇ Download Cleaned Data (CSV)",
            st.session_state.cleaned
            .to_csv(index=False)
            .encode("utf-8"),
            "cleaned_sample.csv",
            "text/csv",
            width="stretch",
        )

        st.download_button(
            "⬇ Download Issue Log (CSV)",
            issues
            .to_csv(index=False)
            .encode("utf-8"),
            "issue_log.csv",
            "text/csv",
            width="stretch",
        )

        st.download_button(
            "📊 Generate Audit Report (Excel)",
            create_excel_report(
                st.session_state.df,
                result,
                st.session_state.cleaned,
            ),
            "audit_report.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )

        st.download_button(
            "🧾 Download Audit Summary (JSON)",
            json.dumps(
                result,
                indent=2,
                default=str,
            ).encode("utf-8"),
            "audit_summary.json",
            "application/json",
            width="stretch",
        )


# Help

elif page == "Help":

    st.header("Help & Interview Guide")

    st.subheader(
        "What makes a quality rule useful?"
    )

    st.write(
        "A useful rule is measurable, repeatable, "
        "business-relevant, and has a clear "
        "threshold or pass/fail condition."
    )

    st.subheader(
        "How do you prioritize issues?"
    )

    st.write(
        "Prioritize by business impact, severity, "
        "affected-record volume, downstream "
        "analytical impact, and remediation urgency."
    )

    st.subheader(
        "Recommended submission flow"
    )

    st.code(
        "Upload Dataset → Run All Quality Checks → "
        "Review Dashboard → Issue Report → "
        "Cleaned Data → Downloads"
    )