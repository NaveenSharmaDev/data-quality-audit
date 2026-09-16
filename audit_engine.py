import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd


class DataQualityAuditor:
    """Repeatable data-quality audit engine for CSV/Excel datasets."""

    def audit(self, df: pd.DataFrame) -> dict:
        work = df.copy()
        issues = []
        issue_id = 1

        if work.empty:
            issues.append(
                self._issue(
                    issue_id,
                    "Consistency",
                    "",
                    0,
                    "",
                    "Critical",
                    "Dataset contains no records."
                )
            )
            issue_id += 1

        missing_by_col = {}

        for col in work.columns:
            blank = work[col].isna()

            if work[col].dtype == "object":
                blank = (
                    blank
                    | work[col].astype("string").str.strip().eq("")
                )

            count = int(blank.sum())
            missing_by_col[str(col)] = count

            if count:
                severity = (
                    "Medium"
                    if count < max(10, len(work) * 0.10)
                    else "High"
                )

                issues.append(
                    self._issue(
                        issue_id,
                        "Missing",
                        str(col),
                        "-",
                        f"{count} missing",
                        severity,
                        f"{count:,} missing/blank value(s) found "
                        f"in column '{col}'."
                    )
                )

                issue_id += 1

        dup_mask = work.duplicated(keep=False)
        dup_count = int(work.duplicated().sum())

        if dup_count:
            issues.append(
                self._issue(
                    issue_id,
                    "Duplicate",
                    "__row__",
                    "-",
                    f"{dup_count} duplicate row(s)",
                    "High",
                    f"{dup_count:,} exact duplicate record(s) found."
                )
            )

            issue_id += 1

        numeric_cols = work.select_dtypes(
            include="number"
        ).columns.tolist()

        range_count = 0
        range_examples = []

        for col in numeric_cols:
            series = work[col]
            bad = pd.Series(
                False,
                index=work.index
            )

            col_lower = str(col).lower()

            keywords = [
                "qty",
                "quantity",
                "price",
                "sales",
                "revenue",
                "amount",
                "cost",
                "profit",
                "age",
                "stock"
            ]

            if any(
                keyword in col_lower
                for keyword in keywords
            ):
                bad = series < 0

            if (
                "percent" in col_lower
                or "%" in col_lower
            ):
                bad = (
                    (series < 0)
                    | (series > 100)
                )

            count = int(bad.sum())

            if count:
                range_count += count

                examples = (
                    work.loc[bad, col]
                    .head(5)
                    .tolist()
                )

                range_examples.extend(
                    examples
                )

                issues.append(
                    self._issue(
                        issue_id,
                        "Range",
                        str(col),
                        "-",
                        str(examples),
                        "High",
                        f"{count:,} value(s) violate "
                        "the inferred non-negative/"
                        "percentage range rule."
                    )
                )

                issue_id += 1

        date_count = 0
        date_cols = []

        for col in work.columns:
            name = str(col).lower()

            if any(
                keyword in name
                for keyword in [
                    "date",
                    "time",
                    "timestamp"
                ]
            ):
                date_cols.append(col)

                parsed = pd.to_datetime(
                    work[col],
                    errors="coerce"
                )

                invalid = (
                    work[col].notna()
                    & parsed.isna()
                )

                count = int(
                    invalid.sum()
                )

                if count:
                    date_count += count

                    values = (
                        work.loc[invalid, col]
                        .head(5)
                        .tolist()
                    )

                    issues.append(
                        self._issue(
                            issue_id,
                            "Consistency",
                            str(col),
                            "-",
                            str(values),
                            "High",
                            f"{count:,} non-empty date "
                            "value(s) cannot be parsed."
                        )
                    )

                    issue_id += 1

        consistency_count = 0

        text_cols = work.select_dtypes(
            include=["object", "string"]
        ).columns.tolist()

        for col in text_cols:
            series = work[col].astype("string")

            whitespace = (
                series.notna()
                & (series != series.str.strip())
            )

            whitespace_count = int(
                whitespace.sum()
            )

            if whitespace_count:
                consistency_count += whitespace_count

                issues.append(
                    self._issue(
                        issue_id,
                        "Consistency",
                        str(col),
                        "-",
                        f"{whitespace_count} whitespace variant(s)",
                        "Low",
                        f"{whitespace_count:,} text value(s) "
                        "contain leading/trailing whitespace."
                    )
                )

                issue_id += 1

            values = (
                series
                .dropna()
                .str.strip()
            )

            if (
                len(values)
                and values.nunique() <= 50
            ):
                normalized = values.str.lower()

                if (
                    normalized.nunique()
                    < values.nunique()
                ):
                    consistency_count += 1

                    issues.append(
                        self._issue(
                            issue_id,
                            "Consistency",
                            str(col),
                            "-",
                            (
                                f"{values.nunique()} raw / "
                                f"{normalized.nunique()} normalized"
                            ),
                            "Medium",
                            "Column contains case-only "
                            "category variants after trimming."
                        )
                    )

                    issue_id += 1

        col_map = {
            str(column).lower().replace(" ", "_"): column
            for column in work.columns
        }

        qty_col = self._find_col(
            col_map,
            ["quantity", "qty"]
        )

        price_col = self._find_col(
            col_map,
            ["unit_price", "price"]
        )

        sales_col = self._find_col(
            col_map,
            [
                "sales",
                "revenue",
                "amount",
                "total_sales"
            ]
        )

        if qty_col and price_col and sales_col:
            quantity = pd.to_numeric(
                work[qty_col],
                errors="coerce"
            )

            price = pd.to_numeric(
                work[price_col],
                errors="coerce"
            )

            sales = pd.to_numeric(
                work[sales_col],
                errors="coerce"
            )

            calculated_sales = quantity * price

            valid = (
                quantity.notna()
                & price.notna()
                & sales.notna()
            )

            mismatch = (
                valid
                & (
                    (sales - calculated_sales).abs()
                    > (
                        0.01
                        + calculated_sales.abs() * 0.02
                    )
                )
            )

            count = int(
                mismatch.sum()
            )

            if count:
                consistency_count += count

                examples = (
                    work.loc[mismatch, sales_col]
                    .head(5)
                    .tolist()
                )

                issues.append(
                    self._issue(
                        issue_id,
                        "Consistency",
                        str(sales_col),
                        "-",
                        str(examples),
                        "High",
                        f"{count:,} row(s) have Sales "
                        "different from Quantity × Unit Price "
                        "beyond 2% tolerance."
                    )
                )

                issue_id += 1

        counts = {
            "Missing": len(
                [
                    issue
                    for issue in issues
                    if issue["type"] == "Missing"
                ]
            ),
            "Duplicate": len(
                [
                    issue
                    for issue in issues
                    if issue["type"] == "Duplicate"
                ]
            ),
            "Range": len(
                [
                    issue
                    for issue in issues
                    if issue["type"] == "Range"
                ]
            ),
            "Consistency": len(
                [
                    issue
                    for issue in issues
                    if issue["type"] == "Consistency"
                ]
            )
        }

        affected = len(issues)

        penalty = min(
            100,
            affected
            / max(1, len(work.columns))
            * 8
        )

        if dup_count:
            penalty += min(
                20,
                dup_count
                / max(1, len(work))
                * 100
            )

        if range_count:
            penalty += min(
                20,
                range_count
                / max(1, len(work))
                * 100
            )

        if date_count:
            penalty += min(
                15,
                date_count
                / max(1, len(work))
                * 100
            )

        quality_score = max(
            0.0,
            min(
                100.0,
                100.0 - penalty
            )
        )

        total_missing = sum(
            missing_by_col.values()
        )

        checklist = [
            self._check(
                "Completeness — missing values",
                "Missing",
                (
                    "PASS"
                    if total_missing == 0
                    else "REVIEW"
                ),
                total_missing,
                "Null/blank values are quantified per column."
            ),

            self._check(
                "Uniqueness — exact duplicates",
                "Duplicate",
                (
                    "PASS"
                    if dup_count == 0
                    else "REVIEW"
                ),
                dup_count,
                "Exact duplicate records are identified."
            ),

            self._check(
                "Validity — numeric ranges",
                "Range",
                (
                    "PASS"
                    if range_count == 0
                    else "REVIEW"
                ),
                range_count,
                "Common business measures are checked "
                "for invalid negative values."
            ),

            self._check(
                "Validity — date parsing",
                "Consistency",
                (
                    "PASS"
                    if date_count == 0
                    else "REVIEW"
                ),
                date_count,
                "Likely date columns are checked "
                "for unparseable values."
            ),

            self._check(
                "Consistency — text formatting",
                "Consistency",
                (
                    "PASS"
                    if consistency_count == 0
                    else "REVIEW"
                ),
                consistency_count,
                "Whitespace/case variants and retail "
                "arithmetic consistency are checked."
            )
        ]

        return {
            "audited_at": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "row_count": int(len(work)),
            "column_count": int(len(work.columns)),
            "numeric_columns": int(
                len(numeric_cols)
            ),
            "text_columns": int(
                len(text_cols)
            ),
            "total_issues": int(
                len(issues)
            ),
            "quality_score": float(
                quality_score
            ),
            "counts": counts,
            "missing_by_column": missing_by_col,
            "issues": issues,
            "checklist": checklist,
            "columns": [
                str(column)
                for column in work.columns
            ]
        }

    def clean(self, df: pd.DataFrame):
        clean = df.copy()
        actions = []

        before = len(clean)

        clean = (
            clean
            .drop_duplicates()
            .reset_index(drop=True)
        )

        removed = before - len(clean)

        actions.append(
            f"Removed {removed:,} exact duplicate row(s)."
        )

        text_cols = clean.select_dtypes(
            include=["object", "string"]
        ).columns

        for col in text_cols:
            clean[col] = (
                clean[col]
                .astype("string")
                .str.strip()
            )

            clean[col] = clean[col].replace(
                {
                    "": pd.NA,
                    "nan": pd.NA,
                    "None": pd.NA
                }
            )

        actions.append(
            f"Trimmed whitespace in "
            f"{len(text_cols):,} text column(s)."
        )

        date_changed = 0

        for col in clean.columns:
            if any(
                keyword in str(col).lower()
                for keyword in [
                    "date",
                    "time",
                    "timestamp"
                ]
            ):
                parsed = pd.to_datetime(
                    clean[col],
                    errors="coerce"
                )

                valid_original = (
                    clean[col].notna()
                )

                clean[col] = (
                    parsed.dt.strftime("%Y-%m-%d")
                )

                date_changed += int(
                    (
                        valid_original
                        & parsed.notna()
                    ).sum()
                )

        if date_changed:
            actions.append(
                f"Standardized {date_changed:,} "
                "parseable date value(s) to YYYY-MM-DD."
            )

        for col in clean.columns:
            if clean[col].dtype == "object":
                converted = pd.to_numeric(
                    clean[col],
                    errors="coerce"
                )

                original_non_null = (
                    clean[col].notna().sum()
                )

                if (
                    original_non_null
                    and converted.notna().sum()
                    >= max(
                        3,
                        int(
                            original_non_null
                            * 0.8
                        )
                    )
                ):
                    clean[col] = converted

        removed_invalid = 0

        for col in clean.select_dtypes(
            include="number"
        ).columns:

            name = str(col).lower()

            keywords = [
                "qty",
                "quantity",
                "price",
                "sales",
                "revenue",
                "amount",
                "cost",
                "profit",
                "stock"
            ]

            if any(
                keyword in name
                for keyword in keywords
            ):
                bad = clean[col] < 0

                removed_invalid += int(
                    bad.sum()
                )

                clean = (
                    clean.loc[~bad]
                    .copy()
                )

        if removed_invalid:
            actions.append(
                f"Removed {removed_invalid:,} row(s) "
                "with invalid negative business measures."
            )

        for col in clean.columns:
            if clean[col].isna().any():

                if pd.api.types.is_numeric_dtype(
                    clean[col]
                ):
                    median = clean[col].median()

                    if pd.notna(median):
                        clean[col] = (
                            clean[col]
                            .fillna(median)
                        )

                else:
                    clean[col] = (
                        clean[col]
                        .fillna("Unknown")
                    )

        actions.append(
            "Filled remaining missing numeric values "
            "with column median and text values with 'Unknown'."
        )

        return (
            clean.reset_index(drop=True),
            actions
        )

    def export(
        self,
        original,
        result,
        cleaned,
        folder,
        source_name="dataset"
    ):
        Path(folder).mkdir(
            parents=True,
            exist_ok=True
        )

        issue_df = pd.DataFrame(
            result["issues"]
        )

        checklist_df = pd.DataFrame(
            result["checklist"]
        )

        missing_df = pd.DataFrame(
            [
                {
                    "column": column,
                    "missing_count": count
                }
                for column, count
                in result["missing_by_column"].items()
            ]
        )

        issue_df.to_csv(
            os.path.join(
                folder,
                "issue_log.csv"
            ),
            index=False
        )

        cleaned.to_csv(
            os.path.join(
                folder,
                "cleaned_sample.csv"
            ),
            index=False
        )

        summary = {
            "project": "Data Quality Audit — Task 24",
            "source": source_name,
            **{
                key: value
                for key, value
                in result.items()
                if key not in [
                    "issues",
                    "checklist"
                ]
            }
        }

        with open(
            os.path.join(
                folder,
                "audit_summary.json"
            ),
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                summary,
                file,
                indent=2,
                default=str
            )

        report_path = os.path.join(
            folder,
            "audit_report.xlsx"
        )

        with pd.ExcelWriter(
            report_path,
            engine="openpyxl"
        ) as writer:

            pd.DataFrame(
                [
                    {
                        "Project": (
                            "Data Quality Audit — Task 24"
                        ),
                        "Source": source_name,
                        "Audit Time": (
                            result["audited_at"]
                        ),
                        "Rows": (
                            result["row_count"]
                        ),
                        "Columns": (
                            result["column_count"]
                        ),
                        "Total Issues": (
                            result["total_issues"]
                        ),
                        "Quality Score (%)": round(
                            result["quality_score"],
                            2
                        )
                    }
                ]
            ).to_excel(
                writer,
                sheet_name="Summary",
                index=False
            )

            issue_df.to_excel(
                writer,
                sheet_name="Issue Log",
                index=False
            )

            checklist_df.to_excel(
                writer,
                sheet_name="Checklist",
                index=False
            )

            missing_df.to_excel(
                writer,
                sheet_name="Missing Values",
                index=False
            )

            original.head(1000).to_excel(
                writer,
                sheet_name="Original Sample",
                index=False
            )

            cleaned.head(1000).to_excel(
                writer,
                sheet_name="Cleaned Sample",
                index=False
            )

    @staticmethod
    def _find_col(
        col_map,
        candidates
    ):
        for candidate in candidates:
            if candidate in col_map:
                return col_map[candidate]

        return None

    @staticmethod
    def _issue(
        issue_id,
        issue_type,
        column,
        row,
        value,
        severity,
        description
    ):
        return {
            "id": issue_id,
            "type": issue_type,
            "column": column,
            "row": row,
            "value": str(value),
            "severity": severity,
            "description": description
        }

    @staticmethod
    def _check(
        rule,
        issue_type,
        status,
        affected,
        description
    ):
        return {
            "rule": rule,
            "type": issue_type,
            "status": status,
            "affected": int(affected),
            "description": description
        }