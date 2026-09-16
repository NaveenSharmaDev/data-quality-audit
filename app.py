import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pandas as pd

from audit_engine import DataQualityAuditor


class DataQualityAuditGUI(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Data Quality Audit | Task 24")
        self.geometry("1250x780")
        self.minsize(1050, 680)

        self.df = None
        self.auditor = DataQualityAuditor()
        self.audit_result = None
        self.cleaned_df = None
        self.source_path = None

        self.setup_style()
        self.build_ui()
        self.load_demo_on_start()

    def setup_style(self):
        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 18, "bold")
        )

        style.configure(
            "SubTitle.TLabel",
            font=("Segoe UI", 10)
        )

        style.configure(
            "Card.TFrame",
            relief="solid",
            borderwidth=1
        )

        style.configure(
            "Treeview",
            rowheight=26
        )

        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold")
        )

        style.configure(
            "Accent.TButton",
            font=("Segoe UI", 10, "bold")
        )

        style.configure(
            "Metric.TLabel",
            font=("Segoe UI", 17, "bold")
        )

    def build_ui(self):
        header = ttk.Frame(self, padding=(18, 14))
        header.pack(fill="x")

        ttk.Label(
            header,
            text="Data Quality Audit",
            style="Title.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            header,
            text=(
                "Task 24 • Repeatable validation checklist • "
                "Missing • Duplicate • Range • Consistency"
            ),
            style="SubTitle.TLabel"
        ).pack(anchor="w", pady=(3, 0))

        toolbar = ttk.Frame(self, padding=(18, 5))
        toolbar.pack(fill="x")

        ttk.Button(
            toolbar,
            text="Load CSV / Excel",
            command=self.load_file
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            toolbar,
            text="Use Demo Retail Data",
            command=self.load_demo
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            toolbar,
            text="Run Audit",
            style="Accent.TButton",
            command=self.run_audit
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            toolbar,
            text="Clean Data",
            command=self.clean_data
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            toolbar,
            text="Export Outputs",
            command=self.export_outputs
        ).pack(side="left")

        self.status_var = tk.StringVar(value="Ready")

        ttk.Label(
            toolbar,
            textvariable=self.status_var
        ).pack(side="right")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=(5, 18)
        )

        self.dashboard_tab = ttk.Frame(
            self.notebook,
            padding=12
        )

        self.preview_tab = ttk.Frame(
            self.notebook,
            padding=12
        )

        self.issues_tab = ttk.Frame(
            self.notebook,
            padding=12
        )

        self.checklist_tab = ttk.Frame(
            self.notebook,
            padding=12
        )

        self.rules_tab = ttk.Frame(
            self.notebook,
            padding=12
        )

        self.notebook.add(
            self.dashboard_tab,
            text="Dashboard"
        )

        self.notebook.add(
            self.preview_tab,
            text="Data Preview"
        )

        self.notebook.add(
            self.issues_tab,
            text="Issue Log"
        )

        self.notebook.add(
            self.checklist_tab,
            text="Quality Checklist"
        )

        self.notebook.add(
            self.rules_tab,
            text="Validation Rules"
        )

        self.build_dashboard()
        self.build_preview()
        self.build_issues()
        self.build_checklist()
        self.build_rules()

    def build_dashboard(self):
        self.metrics = {}

        cards = ttk.Frame(self.dashboard_tab)
        cards.pack(fill="x", pady=(0, 12))

        metric_names = [
            ("Rows", "rows"),
            ("Columns", "columns"),
            ("Issues", "issues"),
            ("Quality Score", "score")
        ]

        for title, key in metric_names:
            card = ttk.Frame(
                cards,
                style="Card.TFrame",
                padding=14
            )

            card.pack(
                side="left",
                fill="x",
                expand=True,
                padx=5
            )

            ttk.Label(
                card,
                text=title
            ).pack(anchor="w")

            value = tk.StringVar(value="—")
            self.metrics[key] = value

            ttk.Label(
                card,
                textvariable=value,
                style="Metric.TLabel"
            ).pack(
                anchor="w",
                pady=(5, 0)
            )

        info = ttk.LabelFrame(
            self.dashboard_tab,
            text="Audit Summary",
            padding=12
        )

        info.pack(
            fill="both",
            expand=True
        )

        self.summary_text = tk.Text(
            info,
            wrap="word",
            font=("Consolas", 10)
        )

        self.summary_text.pack(
            fill="both",
            expand=True
        )

        self.summary_text.insert(
            "1.0",
            "Load a dataset and click Run Audit.\n\n"
            "The built-in demo dataset is already loaded for testing."
        )

        self.summary_text.configure(
            state="disabled"
        )

    def build_preview(self):
        top = ttk.Frame(self.preview_tab)
        top.pack(
            fill="x",
            pady=(0, 8)
        )

        self.preview_info = tk.StringVar(
            value="No dataset loaded."
        )

        ttk.Label(
            top,
            textvariable=self.preview_info
        ).pack(side="left")

        frame = ttk.Frame(self.preview_tab)
        frame.pack(
            fill="both",
            expand=True
        )

        self.preview_tree = self.create_tree(frame)

    def build_issues(self):
        top = ttk.Frame(self.issues_tab)
        top.pack(
            fill="x",
            pady=(0, 8)
        )

        ttk.Label(
            top,
            text="Detected issues with quantified impact."
        ).pack(side="left")

        self.issue_filter = tk.StringVar(
            value="All"
        )

        combo = ttk.Combobox(
            top,
            textvariable=self.issue_filter,
            values=[
                "All",
                "Missing",
                "Duplicate",
                "Range",
                "Consistency"
            ],
            state="readonly",
            width=14
        )

        combo.pack(side="right")

        combo.bind(
            "<<ComboboxSelected>>",
            lambda event: self.render_issues()
        )

        frame = ttk.Frame(self.issues_tab)
        frame.pack(
            fill="both",
            expand=True
        )

        self.issue_tree = self.create_tree(frame)

    def build_checklist(self):
        ttk.Label(
            self.checklist_tab,
            text="Repeatable Quality Checklist",
            font=("Segoe UI", 14, "bold")
        ).pack(
            anchor="w",
            pady=(0, 8)
        )

        self.check_tree = ttk.Treeview(
            self.checklist_tab,
            columns=(
                "rule",
                "type",
                "status",
                "affected",
                "description"
            ),
            show="headings"
        )

        headings = {
            "rule": "Rule",
            "type": "Type",
            "status": "Status",
            "affected": "Affected",
            "description": "Description"
        }

        widths = {
            "rule": 210,
            "type": 110,
            "status": 100,
            "affected": 90,
            "description": 500
        }

        for column in headings:
            self.check_tree.heading(
                column,
                text=headings[column]
            )

            self.check_tree.column(
                column,
                width=widths[column],
                anchor="w"
            )

        self.check_tree.pack(
            fill="both",
            expand=True
        )

    def build_rules(self):
        ttk.Label(
            self.rules_tab,
            text="Validation Rules Used by the Audit Engine",
            font=("Segoe UI", 14, "bold")
        ).pack(
            anchor="w",
            pady=(0, 8)
        )

        rules = [
            (
                "Missing Values",
                "Completeness",
                "Count null and blank values by column."
            ),
            (
                "Duplicate Rows",
                "Uniqueness",
                "Detect exact duplicate records."
            ),
            (
                "Numeric Range",
                "Validity",
                "Detect negative quantity, price, sales and other invalid numeric values."
            ),
            (
                "Date Validity",
                "Validity",
                "Detect values that cannot be parsed as dates."
            ),
            (
                "Text Consistency",
                "Consistency",
                "Trim whitespace and detect inconsistent categorical formatting."
            ),
            (
                "Sales Consistency",
                "Consistency",
                "Compare Sales with Quantity × Unit_Price."
            ),
            (
                "Column Structure",
                "Schema",
                "Check that the dataset contains columns and non-empty records."
            )
        ]

        tree = ttk.Treeview(
            self.rules_tab,
            columns=(
                "rule",
                "type",
                "description"
            ),
            show="headings"
        )

        columns = [
            ("rule", "Rule", 220),
            ("type", "Type", 130),
            ("description", "Description", 650)
        ]

        for column, heading, width in columns:
            tree.heading(
                column,
                text=heading
            )

            tree.column(
                column,
                width=width,
                anchor="w"
            )

        for rule in rules:
            tree.insert(
                "",
                "end",
                values=rule
            )

        tree.pack(
            fill="both",
            expand=True
        )

    def create_tree(self, parent):
        container = ttk.Frame(parent)
        container.pack(
            fill="both",
            expand=True
        )

        tree = ttk.Treeview(
            container,
            show="headings"
        )

        vertical_scroll = ttk.Scrollbar(
            container,
            orient="vertical",
            command=tree.yview
        )

        horizontal_scroll = ttk.Scrollbar(
            container,
            orient="horizontal",
            command=tree.xview
        )

        tree.configure(
            yscrollcommand=vertical_scroll.set,
            xscrollcommand=horizontal_scroll.set
        )

        tree.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        vertical_scroll.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        horizontal_scroll.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        container.rowconfigure(
            0,
            weight=1
        )

        container.columnconfigure(
            0,
            weight=1
        )

        return tree

    def load_demo_on_start(self):
        self.load_demo()

    def load_demo(self):
        path = os.path.join(
            os.path.dirname(__file__),
            "data",
            "retail_sales_demo.csv"
        )

        try:
            self.df = pd.read_csv(path)
            self.source_path = path
            self.cleaned_df = None

            self.show_preview(self.df)

            self.status_var.set(
                "Demo dataset loaded"
            )

            self.run_audit()

        except Exception as exc:
            messagebox.showerror(
                "Load Error",
                str(exc)
            )

    def load_file(self):
        path = filedialog.askopenfilename(
            title="Select Dataset",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx *.xls"),
                ("All supported", "*.csv *.xlsx *.xls")
            ]
        )

        if not path:
            return

        try:
            if path.lower().endswith(".csv"):
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)

            self.df = df
            self.source_path = path
            self.cleaned_df = None
            self.audit_result = None

            self.show_preview(df)
            self.reset_outputs()

            self.status_var.set(
                f"Loaded: {os.path.basename(path)}"
            )

        except Exception as exc:
            messagebox.showerror(
                "Load Error",
                f"Could not load dataset:\n{exc}"
            )

    def show_preview(self, df, max_rows=100):
        self.preview_info.set(
            f"{len(df):,} rows × {len(df.columns):,} columns"
        )

        tree = self.preview_tree

        tree.delete(
            *tree.get_children()
        )

        columns = [
            str(column)
            for column in df.columns
        ]

        tree["columns"] = columns

        for column in columns:
            tree.heading(
                column,
                text=column
            )

            tree.column(
                column,
                width=max(
                    110,
                    min(
                        220,
                        len(column) * 12
                    )
                ),
                anchor="w"
            )

        for row in df.head(max_rows).itertuples(
            index=False,
            name=None
        ):
            values = [
                "" if pd.isna(value)
                else str(value)
                for value in row
            ]

            tree.insert(
                "",
                "end",
                values=values
            )

    def run_audit(self):
        if self.df is None or self.df.empty:
            messagebox.showwarning(
                "No Data",
                "Load a non-empty CSV or Excel dataset first."
            )
            return

        try:
            self.audit_result = self.auditor.audit(
                self.df
            )

            self.update_dashboard()
            self.render_issues()
            self.render_checklist()

            self.status_var.set(
                "Audit completed"
            )

            self.notebook.select(
                self.dashboard_tab
            )

        except Exception as exc:
            messagebox.showerror(
                "Audit Error",
                str(exc)
            )

    def clean_data(self):
        if self.df is None:
            messagebox.showwarning(
                "No Data",
                "Load a dataset first."
            )
            return

        try:
            self.cleaned_df, actions = (
                self.auditor.clean(self.df)
            )

            self.show_preview(
                self.cleaned_df
            )

            self.status_var.set(
                "Cleaning completed"
            )

            messagebox.showinfo(
                "Cleaning Completed",
                "Cleaned sample created.\n\n"
                + "\n".join(
                    f"• {action}"
                    for action in actions
                )
            )

        except Exception as exc:
            messagebox.showerror(
                "Cleaning Error",
                str(exc)
            )

    def export_outputs(self):
        if self.audit_result is None:
            self.run_audit()

        if self.audit_result is None:
            return

        if self.cleaned_df is None:
            self.cleaned_df, _ = (
                self.auditor.clean(self.df)
            )

        folder = filedialog.askdirectory(
            title="Choose Output Folder"
        )

        if not folder:
            return

        try:
            self.auditor.export(
                self.df,
                self.audit_result,
                self.cleaned_df,
                folder,
                source_name=os.path.basename(
                    self.source_path or "dataset"
                )
            )

            messagebox.showinfo(
                "Export Complete",
                f"Outputs saved to:\n{folder}\n\n"
                "• audit_report.xlsx\n"
                "• issue_log.csv\n"
                "• cleaned_sample.csv\n"
                "• audit_summary.json"
            )

            self.status_var.set(
                f"Outputs exported to {folder}"
            )

        except Exception as exc:
            messagebox.showerror(
                "Export Error",
                str(exc)
            )

    def update_dashboard(self):
        result = self.audit_result

        self.metrics["rows"].set(
            f"{result['row_count']:,}"
        )

        self.metrics["columns"].set(
            f"{result['column_count']:,}"
        )

        self.metrics["issues"].set(
            f"{result['total_issues']:,}"
        )

        self.metrics["score"].set(
            f"{result['quality_score']:.1f}%"
        )

        source = os.path.basename(
            self.source_path or "dataset"
        )

        text = (
            f"Source: {source}\n"
            f"Audited at: {result['audited_at']}\n\n"

            f"QUALITY SCORE\n"
            f"{result['quality_score']:.1f}%\n\n"

            f"ISSUE BREAKDOWN\n"
            f"Missing values : {result['counts']['Missing']:,}\n"
            f"Duplicate rows : {result['counts']['Duplicate']:,}\n"
            f"Range issues   : {result['counts']['Range']:,}\n"
            f"Consistency    : {result['counts']['Consistency']:,}\n\n"

            f"DATA PROFILE\n"
            f"Rows           : {result['row_count']:,}\n"
            f"Columns        : {result['column_count']:,}\n"
            f"Numeric columns: {result['numeric_columns']}\n"
            f"Text columns   : {result['text_columns']}\n\n"

            f"RECOMMENDED ACTIONS\n"
            f"1. Review high-impact missing values.\n"
            f"2. Remove exact duplicate records after business confirmation.\n"
            f"3. Correct invalid numeric/date values before analysis.\n"
            f"4. Standardize categorical text and date formats.\n"
            f"5. Re-run the audit after cleaning to verify improvement."
        )

        self.summary_text.configure(
            state="normal"
        )

        self.summary_text.delete(
            "1.0",
            "end"
        )

        self.summary_text.insert(
            "1.0",
            text
        )

        self.summary_text.configure(
            state="disabled"
        )

    def render_issues(self):
        tree = self.issue_tree

        tree.delete(
            *tree.get_children()
        )

        columns = (
            "id",
            "type",
            "column",
            "row",
            "value",
            "severity",
            "description"
        )

        tree["columns"] = columns

        headers = {
            "id": "ID",
            "type": "Type",
            "column": "Column",
            "row": "Row",
            "value": "Value",
            "severity": "Severity",
            "description": "Description"
        }

        widths = {
            "id": 55,
            "type": 110,
            "column": 160,
            "row": 75,
            "value": 160,
            "severity": 90,
            "description": 520
        }

        for column in columns:
            tree.heading(
                column,
                text=headers[column]
            )

            tree.column(
                column,
                width=widths[column],
                anchor="w"
            )

        if not self.audit_result:
            return

        selected = self.issue_filter.get()

        for issue in self.audit_result["issues"]:

            if (
                selected != "All"
                and issue["type"] != selected
            ):
                continue

            tree.insert(
                "",
                "end",
                values=(
                    issue["id"],
                    issue["type"],
                    issue["column"],
                    issue["row"],
                    issue["value"],
                    issue["severity"],
                    issue["description"]
                )
            )

    def render_checklist(self):
        self.check_tree.delete(
            *self.check_tree.get_children()
        )

        if not self.audit_result:
            return

        for item in self.audit_result["checklist"]:
            self.check_tree.insert(
                "",
                "end",
                values=(
                    item["rule"],
                    item["type"],
                    item["status"],
                    item["affected"],
                    item["description"]
                )
            )

    def reset_outputs(self):
        for key in self.metrics:
            self.metrics[key].set("—")

        self.summary_text.configure(
            state="normal"
        )

        self.summary_text.delete(
            "1.0",
            "end"
        )

        self.summary_text.insert(
            "1.0",
            "Dataset loaded. Click Run Audit."
        )

        self.summary_text.configure(
            state="disabled"
        )

        self.issue_tree.delete(
            *self.issue_tree.get_children()
        )

        self.check_tree.delete(
            *self.check_tree.get_children()
        )


if __name__ == "__main__":
    app = DataQualityAuditGUI()
    app.mainloop()