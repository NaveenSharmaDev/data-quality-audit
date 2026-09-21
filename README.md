# Data Quality Audit 

**Track:** Data Analytics  
**Project Type:** Data Quality & Data Validation  
**Tools & Technologies:** Python, Pandas, Tkinter, Streamlit, Plotly, Excel, CSV, JSON


---

## Project Overview

**Data Quality Audit —** is a Python-based data quality auditing application designed to identify, quantify, and manage common data quality issues in structured datasets.

The application provides a repeatable validation checklist, interactive dashboards, issue reporting, data cleaning, and multi-format export capabilities.

The project supports both a **desktop-based Tkinter GUI** and a **modern Streamlit web dashboard**, allowing users to audit CSV and Excel datasets through an easy-to-use interface.


---


## Objective

The primary objective of this project is to:

- Identify missing and blank values.
- Detect duplicate records.
- Validate numerical and business ranges.
- Identify date and time validation issues.
- Detect text formatting inconsistencies.
- Identify category case variations.
- Validate retail sales calculations.
- Generate a repeatable data quality checklist.
- Create a cleaned version of the dataset.
- Export audit results in Excel, CSV, and JSON formats.


---


## Key Features

### Data Quality Auditing

The application performs automated checks for:

- Missing values
- Blank values
- Duplicate records
- Invalid numerical ranges
- Percentage validation
- Invalid dates
- Leading/trailing whitespace
- Case inconsistencies
- Retail calculation inconsistencies


### Data Cleaning

The cleaning pipeline can:

- Remove exact duplicate records.
- Trim unnecessary whitespace.
- Convert suitable columns to numeric data types.
- Standardize valid dates.
- Remove invalid negative business measures.
- Fill numeric missing values using median values.
- Fill remaining text missing values with `Unknown`.


### Reporting

The application generates:

- Excel audit report
- Issue log CSV
- Cleaned dataset CSV
- Machine-readable JSON summary


### Interactive Dashboard

The Streamlit dashboard provides:

- KPI cards
- Data quality summary
- Issue distribution charts
- Top columns with issues
- Data preview
- Quality checklist
- Filterable issue report
- Cleaned data preview
- Downloadable reports


---

## Project Structure

```text
data-quality-audit-task24/
│
├── app.py
├── streamlit_app.py
├── audit_engine.py
├── generate_demo_data.py
├── requirements.txt
├── README.md
│
├── data/
│   └── retail_sales_demo.csv
│
├── outputs/
│   ├── audit_report.xlsx
│   ├── issue_log.csv
│   ├── cleaned_sample.csv
│   └── audit_summary.json
│
└── run_dashboard.bat
