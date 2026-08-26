from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from types import SimpleNamespace
from html import escape
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QTableWidget, QTableWidgetItem, QTextEdit, QDialog, QPushButton, QFrame,
    QHeaderView
)

class TraceDetailDialog(QDialog):

    def __init__(self, trace_report):
        super().__init__()

        self.setWindowTitle(f"📊 Trace Violation Audit · ID {trace_report.trace_id}")
        self.resize(800, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # =====================================================
        # HEADER INFO BLOCK
        # =====================================================
        info_block = QFrame()
        info_block.setObjectName("ToolBlock")
        info_layout = QVBoxLayout(info_block)
        info_layout.setSpacing(6)

        mutation_lbl = QLabel(f"🧬 MUTATION EFFECT: <span style='color:#58a6ff; font-weight:bold;'>{trace_report.mutation_name}</span>")
        mutation_lbl.setTextFormat(Qt.RichText)
        
        # Color dinámico de severidad
        display_severity = TraceDetailDialog._display_severity(trace_report.severity)
        sev_color = "#ff7b72" if display_severity == "VIOLATION" else "#d29922" if display_severity == "WARNING" else "#56d364"
        severity_lbl = QLabel(f"⚠️ SEVERITY: <span style='color:{sev_color}; font-weight:bold;'>{trace_report.severity}</span>")
        severity_lbl.setText(f"SEVERITY: <span style='color:{sev_color}; font-weight:bold;'>{display_severity}</span>")
        severity_lbl.setTextFormat(Qt.RichText)

        mode_lbl = QLabel("VALIDATOR: <span style='color:#58a6ff; font-weight:bold;'>DETERMINISTIC</span>")
        mode_lbl.setTextFormat(Qt.RichText)

        rec_lbl = QLabel(
            "SUMMARY: "
            f"<span style='color:#8b949e;'>{escape(self.issue_summary(trace_report, max_items=4))}</span>"
        )
        rec_lbl.setWordWrap(True)
        rec_lbl.setTextFormat(Qt.RichText)

        info_layout.addWidget(mutation_lbl)
        info_layout.addWidget(mode_lbl)
        info_layout.addWidget(severity_lbl)
        info_layout.addWidget(rec_lbl)
        layout.addWidget(info_block)

        # =====================================================
        # DETAILS (HTML AUDIT LOG)
        # =====================================================
        title_details = QLabel("AUDIT TRAIL LOG")
        title_details.setObjectName("SectionTitle")
        layout.addWidget(title_details)

        details = QTextEdit()
        details.setObjectName("LogViewer")
        details.setReadOnly(True)
        details.setMaximumHeight(360)
        details.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        details.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        details.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        html_content = ["<body style='color:#c9d1d9; font-family:monospace;'>"]

        violations = trace_report.validator_result.get("violations", [])
        warnings = trace_report.validator_result.get("warnings", [])

        # --- VIOLATIONS SECTION ---
        html_content.append("<b style='color:#ff7b72; font-size:13px;'>🚨 CRITICAL VIOLATIONS DETECTED</b>")
        html_content.append("<hr style='border: 1px solid #30363d;'>")
        if violations:
            for v in violations:
                html_content.append(f"<div style='margin-bottom: 10px; background-color: #2c1919; padding: 8px; border-left: 4px solid #ff7b72; border-radius:4px;'>")
                html_content.append(f"  <b style='color:#ff9e96;'>[RULE]:</b> {escape(str(v['rule']))}<br>")
                html_content.append(f"  <b>[EVENT]:</b> <span style='color:#ff7b72;'>{escape(str(v['event']))}</span><br>")
                html_content.append(f"  <b>[DETAILS]:</b> {escape(str(v.get('message', '')))}")
                html_content.append(f"</div>")
        else:
            html_content.append("<p style='color:#8b949e; italic;'>No critical compliance mutations broke strict rules.</p>")

        html_content.append("<br>")

        # --- WARNINGS SECTION ---
        html_content.append("<b style='color:#d29922; font-size:13px;'>⚠️ PRIVACY WARNINGS / ANOMALIES</b>")
        html_content.append("<hr style='border: 1px solid #30363d;'>")
        if warnings:
            for w in warnings:
                html_content.append(f"<div style='margin-bottom: 10px; background-color: #2c2414; padding: 8px; border-left: 4px solid #d29922; border-radius:4px;'>")
                html_content.append(f"  <b style='color:#f0e084;'>[RULE]:</b> {escape(str(w['rule']))}<br>")
                html_content.append(f"  <b>[EVENT]:</b> <span style='color:#d29922;'>{escape(str(w['event']))}</span><br>")
                html_content.append(f"  <b>[DETAILS]:</b> {escape(str(w.get('message', '')))}")
                html_content.append(f"</div>")
        else:
            html_content.append("<p style='color:#8b949e; italic;'>No secondary warnings found for this trace execution.</p>")

        html_content.append("</body>")
        details.setHtml("\n".join(html_content))
        layout.addWidget(details)

        # Bottom Bar
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        close_button = QPushButton("✕ CLOSE AUDIT")
        close_button.setFixedWidth(130)
        close_button.clicked.connect(self.close)
        actions_layout.addWidget(close_button)
        
        layout.addLayout(actions_layout)

    @staticmethod
    def _display_severity(severity):
        return "COMPLIANT" if severity == "OK" else severity

    @staticmethod
    def issue_summary(trace_report, max_items=3):
        violations = trace_report.validator_result.get("violations", [])
        warnings = trace_report.validator_result.get("warnings", [])
        total = len(violations) + len(warnings)
        if total == 0:
            return "No violations or warnings detected."

        counters = {}
        for issue in violations:
            key = issue.get("mutation") or issue.get("rule") or "violation"
            counters.setdefault(key, {"V": 0, "W": 0})
            counters[key]["V"] += 1
        for issue in warnings:
            key = issue.get("mutation") or issue.get("rule") or "warning"
            counters.setdefault(key, {"V": 0, "W": 0})
            counters[key]["W"] += 1

        parts = []
        for key, counts in sorted(counters.items())[:max_items]:
            label_parts = []
            if counts["V"]:
                label_parts.append(f"Vx{counts['V']}")
            if counts["W"]:
                label_parts.append(f"Wx{counts['W']}")
            parts.append(f"{key} ({', '.join(label_parts)})")

        suffix = "..." if len(counters) > max_items else ""
        return f"{total} findings detected: " + "; ".join(parts) + suffix


class MutationReportWindow(QWidget):

    def __init__(self, report):
        super().__init__()
        self.report = report
        self.grouped_reports = self._group_reports_by_trace(report.trace_reports)
        self.setWindowTitle("Mutation Analysis & GDPR Compliance Report")
        self.resize(1200, 750)

        self._build_ui()
        self._populate_table()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # =================================================
        # SUMMARY CARDS PANEL
        # =================================================
        summary_layout = QHBoxLayout()
        summary_layout.setSpacing(12)

        card_traces = QFrame()
        card_traces.setObjectName("SummaryCard")
        lt1 = QVBoxLayout(card_traces)
        lt1.addWidget(QLabel("<span style='color:#8b949e; font-size:10px; font-weight:bold;'>MUTATED TRACES</span>"))
        lt1.addWidget(QLabel(f"<span style='font-size:20px; font-weight:bold; color:#58a6ff;'>{len(self.grouped_reports)}</span>"))

        card_violations = QFrame()
        card_violations.setObjectName("SummaryCard")
        card_violations.setStyleSheet("border-left: 3px solid #ff7b72;")
        lt2 = QVBoxLayout(card_violations)
        lt2.addWidget(QLabel("<span style='color:#8b949e; font-size:10px; font-weight:bold;'>TOTAL VIOLATIONS</span>"))
        total_violations = sum(len(r.validator_result.get("violations", [])) for r in self.grouped_reports)
        lt2.addWidget(QLabel(f"<span style='font-size:20px; font-weight:bold; color:#ff7b72;'>{total_violations}</span>"))

        card_warnings = QFrame()
        card_warnings.setObjectName("SummaryCard")
        card_warnings.setStyleSheet("border-left: 3px solid #d29922;")
        lt3 = QVBoxLayout(card_warnings)
        lt3.addWidget(QLabel("<span style='color:#8b949e; font-size:10px; font-weight:bold;'>TOTAL WARNINGS</span>"))
        total_warnings = sum(len(r.validator_result.get("warnings", [])) for r in self.grouped_reports)
        lt3.addWidget(QLabel(f"<span style='font-size:20px; font-weight:bold; color:#d29922;'>{total_warnings}</span>"))

        summary_layout.addWidget(card_traces)
        summary_layout.addWidget(card_violations)
        summary_layout.addWidget(card_warnings)
        layout.addLayout(summary_layout)

        # =================================================
        # FILTERS BAR
        # =================================================
        filters_container = QFrame()
        filters_container.setObjectName("ToolBlock")
        filters_layout = QHBoxLayout(filters_container)
        filters_layout.setContentsMargins(10, 6, 10, 6)
        filters_layout.setSpacing(10)

        self.severity_filter = QComboBox()
        self.severity_filter.addItems(["ALL", "VIOLATION", "WARNING", "COMPLIANT"])

        self.mutation_filter = QComboBox()
        mutations = sorted({
            mutation_name
            for grouped_report in self.grouped_reports
            for mutation_name in grouped_report.mutation_names
        })
        self.mutation_filter.addItem("ALL")
        self.mutation_filter.addItems(mutations)

        self.severity_filter.currentTextChanged.connect(self._populate_table)
        self.mutation_filter.currentTextChanged.connect(self._populate_table)

        filters_layout.addWidget(QLabel("Filter Severity:"))
        filters_layout.addWidget(self.severity_filter)
        filters_layout.addWidget(QLabel("Filter Mutation Rule:"))
        filters_layout.addWidget(self.mutation_filter)
        filters_layout.addWidget(QLabel("<span style='color:#8b949e; font-size:11px; margin-left:10px;'>💡 Double-click a row to open full audit trail</span>"))
        filters_layout.addStretch()

        layout.addWidget(filters_container)

        # =================================================
        # DATA TABLE
        # =================================================
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Trace Target ID",
            "Applied Mutation Engine",
            "Audit Status",
            "Findings Summary",
            "Violations Count",
            "Warnings Count"
        ])
        
        # Ajustes de comportamiento de tabla pro
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("QTableWidget { alternate-background-color: #1c2128; }")
        
        self.table.cellDoubleClicked.connect(self._open_trace_detail)
        layout.addWidget(self.table)

    def _populate_table(self):
        severity_filter = self.severity_filter.currentText()
        mutation_filter = self.mutation_filter.currentText()

        filtered = []
        for report in self.grouped_reports:
            display_severity = TraceDetailDialog._display_severity(report.severity)
            if severity_filter != "ALL" and display_severity != severity_filter:
                continue
            if mutation_filter != "ALL" and mutation_filter not in report.mutation_names:
                continue
            filtered.append(report)

        self.filtered_reports = filtered
        self.table.setRowCount(len(filtered))

        for row, report in enumerate(filtered):
            violations = len(report.validator_result["violations"])
            warnings = len(report.validator_result["warnings"])
            display_severity = TraceDetailDialog._display_severity(report.severity)

            # Trace ID (Centrado)
            item_id = QTableWidgetItem(str(report.trace_id))
            item_id.setTextAlignment(Qt.AlignCenter)
            
            # Mutation Name
            item_mut = QTableWidgetItem(report.mutation_name)
            item_mut.setToolTip("\n".join(report.mutation_names))

            # Status Badge Dinámico
            item_sev = QTableWidgetItem(f" ● {report.severity}")
            item_sev.setText(f" ● {display_severity}")
            if display_severity == "VIOLATION":
                item_sev.setForeground(Qt.GlobalColor.red)
            elif display_severity == "WARNING":
                item_sev.setForeground(Qt.GlobalColor.yellow)
            else:
                item_sev.setForeground(Qt.GlobalColor.green)
            font_bold = QFont()
            font_bold.setBold(True)
            item_sev.setFont(font_bold)

            # Violaciones (Centrado)
            item_summary = QTableWidgetItem(TraceDetailDialog.issue_summary(report, max_items=2))
            item_summary.setToolTip(TraceDetailDialog.issue_summary(report, max_items=20))

            item_v = QTableWidgetItem(str(violations))
            item_v.setTextAlignment(Qt.AlignCenter)
            if violations > 0:
                item_v.setForeground(Qt.GlobalColor.red)

            # Warnings (Centrado)
            item_w = QTableWidgetItem(str(warnings))
            item_w.setTextAlignment(Qt.AlignCenter)
            if warnings > 0:
                item_w.setForeground(Qt.GlobalColor.yellow)

            self.table.setItem(row, 0, item_id)
            self.table.setItem(row, 1, item_mut)
            self.table.setItem(row, 2, item_sev)
            self.table.setItem(row, 3, item_summary)
            self.table.setItem(row, 4, item_v)
            self.table.setItem(row, 5, item_w)

        self.table.resizeColumnsToContents()

    @staticmethod
    def _severity_rank(severity):
        normalized = TraceDetailDialog._display_severity(severity)
        return {
            "COMPLIANT": 0,
            "WARNING": 1,
            "VIOLATION": 2,
        }.get(normalized, 0)

    @staticmethod
    def _dedupe_issues(issues):
        deduped = []
        seen = set()

        for issue in issues:
            key = (
                issue.get("rule"),
                issue.get("event"),
                issue.get("message"),
                issue.get("mutation"),
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(issue)

        return deduped

    def _group_reports_by_trace(self, trace_reports):
        grouped = {}

        for trace_report in trace_reports:
            grouped.setdefault(trace_report.trace_id, []).append(trace_report)

        aggregated = []
        for trace_id, reports in grouped.items():
            mutation_names = [report.mutation_name for report in reports]
            violations = []
            warnings = []
            recommendation_parts = []

            for report in reports:
                for issue in report.validator_result.get("violations", []):
                    merged_issue = dict(issue)
                    merged_issue["mutation"] = report.mutation_name
                    merged_issue["message"] = (
                        f"[{report.mutation_name}] {merged_issue.get('message', '')}"
                    )
                    violations.append(merged_issue)

                for issue in report.validator_result.get("warnings", []):
                    merged_issue = dict(issue)
                    merged_issue["mutation"] = report.mutation_name
                    merged_issue["message"] = (
                        f"[{report.mutation_name}] {merged_issue.get('message', '')}"
                    )
                    warnings.append(merged_issue)

                recommendation_parts.append(
                    f"{report.mutation_name}: {report.recommendation}"
                )

            violations = self._dedupe_issues(violations)
            warnings = self._dedupe_issues(warnings)
            severity = max(
                (TraceDetailDialog._display_severity(report.severity) for report in reports),
                key=self._severity_rank,
                default="COMPLIANT",
            )

            mutation_label = "; ".join(mutation_names)
            if len(mutation_label) > 90:
                mutation_label = mutation_label[:87] + "..."

            aggregated.append(SimpleNamespace(
                trace_id=trace_id,
                mutation_name=mutation_label,
                mutation_names=mutation_names,
                validator_result={
                    "validation_mode": "deterministic",
                    "violations": violations,
                    "warnings": warnings,
                },
                severity=severity,
                recommendation="\n\n".join(recommendation_parts),
            ))

        return sorted(aggregated, key=lambda item: str(item.trace_id))

    def _open_trace_detail(self, row, column):
        report = self.filtered_reports[row]
        dialog = TraceDetailDialog(report)
        dialog.exec()
