from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton,
    QComboBox, QScrollArea, QSplitter,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from types import SimpleNamespace

from app.mutations.registry.mutation_registry import MUTATION_REGISTRY
from app.ui.mutations.mutation_config_widget import MutationConfigWidget
from app.ui.mutations.mutation_report_window import TraceDetailDialog  # Diálogo de auditoría detallada
from app.ui.main_flow.styles import STYLE


class MutationView(QWidget):
    def __init__(self, on_open_mutations, on_export_mutated, on_back):
        super().__init__()
        
        self.total_traces = 100
        self.widgets = []
        self.current_report = None
        self.filtered_reports = []
        self.grouped_reports = []
        self.on_open_mutations = on_open_mutations  # Callback original de inyección
        
        self.setStyleSheet(STYLE)
        
        # LAYOUT DE RAÍZ VERTICAL (Permite una barra de navegación superior)
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(15, 15, 15, 15)
        root_layout.setSpacing(12)

        # =================================================================
        # BARRA SUPERIOR DE NAVEGACIÓN
        # =================================================================
        nav_bar = QHBoxLayout()
        back_button = QPushButton("⬅ BACK TO ENRICHMENT")
        back_button.setMinimumWidth(200)  # Evita que se colapse el texto
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px 14px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #30363d;
                border-color: #8b949e;
            }
        """)
        back_button.clicked.connect(on_back)
        nav_bar.addWidget(back_button)
        nav_bar.addStretch()
        root_layout.addLayout(nav_bar)
        
        # SPLITTER PRINCIPAL (Ahora sí es 100% interactivo y redimensionable)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #30363d;
                width: 4px;
            }
            QSplitter::handle:hover {
                background-color: #58a6ff;
            }
        """)
        
        # =================================================================
        # PANEL IZQUIERDO: CONFIGURADOR DE MUTACIONES
        # =================================================================
        config_panel = QFrame()
        config_panel.setObjectName("ToolBlock")
        config_panel.setMinimumWidth(300) # Ancho mínimo de seguridad, quitamos setFixedWidth
        
        config_layout = QVBoxLayout(config_panel)
        config_layout.setContentsMargins(12, 12, 12, 12)
        config_layout.setSpacing(10)
        
        self.title_label = QLabel("MUTATION ENGINE")
        self.title_label.setObjectName("SectionTitle")
        config_layout.addWidget(self.title_label)

        mode_note = QLabel("Manual mutation selection")
        mode_note.setStyleSheet(
            "color: #8b949e; font-weight: bold; font-size: 10px; "
            "padding: 7px; background-color: #161b22; border: 1px solid #30363d; "
            "border-radius: 6px;"
        )
        config_layout.addWidget(mode_note)
        
        # --- SUB-PANEL MANUAL ---
        self.manual_panel = QWidget()
        manual_layout = QVBoxLayout(self.manual_panel)
        manual_layout.setContentsMargins(0, 0, 0, 0)
        manual_layout.setSpacing(8)
        
        cat_row = QHBoxLayout()
        cat_lbl = QLabel("Category:")
        cat_lbl.setStyleSheet("color: #8b949e; font-weight: bold;")
        self.category_combo = QComboBox()
        self.category_combo.addItems(self._available_category_names())
        self.category_combo.currentTextChanged.connect(self._reload_mutations)
        cat_row.addWidget(cat_lbl)
        cat_row.addWidget(self.category_combo)
        manual_layout.addLayout(cat_row)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.container = QFrame()
        self.container.setObjectName("ScrollContent")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(2, 2, 2, 2)
        self.container_layout.setSpacing(6)
        self.scroll.setWidget(self.container)
        manual_layout.addWidget(self.scroll)
        
        config_layout.addWidget(self.manual_panel)
        
        # Footer del panel izquierdo
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #30363d; max-height: 1px; border: none; margin: 5px 0;")
        config_layout.addWidget(line)
        
        # BOTÓN PRINCIPAL DE ACCIÓN: INYECTAR MUTACIONES (Optimizado visualmente)
        self.mutation_button = QPushButton("🧪 INJECT GDPR VIOLATIONS")
        self.mutation_button.setStyleSheet("""
            QPushButton {
                background-color: #d1440c;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #f26522;
                border-radius: 6px;
                padding: 10px 15px;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #e0531c;
                border-color: #f47942;
            }
            QPushButton:pressed {
                background-color: #a7360a;
            }
        """)
        self.mutation_button.clicked.connect(self._on_inject_clicked)
        config_layout.addWidget(self.mutation_button)
        
        # =================================================================
        # PANEL DERECHO: REPORTE E INTERFAZ DE AUDITORÍA INTEGRADA
        # =================================================================
        self.report_panel = QFrame()
        self.report_panel.setObjectName("MainContainerPanel")
        self.report_panel.setMinimumWidth(500)
        self.report_panel.setStyleSheet("background-color: #0d1117; border: 1px solid #30363d; border-radius: 8px;")
        
        self.report_layout = QVBoxLayout(self.report_panel)
        self.report_layout.setContentsMargins(20, 20, 20, 20)
        self.report_layout.setSpacing(12)
        
        # Estado inicial vacío (Placeholder)
        self.placeholder_layout = QVBoxLayout()
        self.placeholder_layout.setAlignment(Qt.AlignCenter)
        
        self.icon_placeholder = QLabel("🧪")
        self.icon_placeholder.setStyleSheet("font-size: 50px; margin-bottom: 10px;")
        self.icon_placeholder.setAlignment(Qt.AlignCenter)
        
        self.txt_placeholder = QLabel("Awaiting Fault Injection Configuration...\nSelect anomalies on the left panel and click 'Inject'.")
        self.txt_placeholder.setStyleSheet("color: #8b949e; font-size: 14px; text-align: center; line-height: 1.5;")
        self.txt_placeholder.setAlignment(Qt.AlignCenter)
        
        self.placeholder_layout.addWidget(self.icon_placeholder)
        self.placeholder_layout.addWidget(self.txt_placeholder)
        self.report_layout.addLayout(self.placeholder_layout)
        
        # Añadir elementos al splitter y setear pesos de estiramiento iniciales (35% - 65%)
        splitter.addWidget(config_panel)
        splitter.addWidget(self.report_panel)
        splitter.setStretchFactor(0, 35)
        splitter.setStretchFactor(1, 65)
        
        root_layout.addWidget(splitter)

    # =================================================================
    # MANEJO DE ACCIONES Y VALIDACIONES
    # =================================================================
    
    def _on_inject_clicked(self):
        """Intercepta el clic de inyección para validar la entrada manual."""
        has_selection = any(w.is_selected() for w in self.widgets)
        if not has_selection:
            QMessageBox.warning(
                self,
                "No Mutations Selected",
                "Please select at least one mutation rule checkbox from the list before attempting injection."
            )
            return

        self.on_open_mutations()

    def _available_category_names(self):
        categories = []
        for data in MUTATION_REGISTRY.values():
            category_name = data["category"].name
            if category_name not in categories:
                categories.append(category_name)
        return categories

    def setup_mutation_config(self, model_name, total_traces):
        self.total_traces = total_traces
        self.title_label.setText(f"MUTATIONS · {model_name.split('·')[-1].strip()}")
        self._reload_mutations()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
            elif item.spacerItem():
                del item

    def _reload_mutations(self):
        self._clear_layout(self.container_layout)
        self.widgets.clear()
        category = self.category_combo.currentText()

        for name, data in MUTATION_REGISTRY.items():
            if data["category"].name != category:
                continue

            widget = MutationConfigWidget(name, self.total_traces)
            widget.setStyleSheet(STYLE) 
            self.widgets.append(widget)
            self.container_layout.addWidget(widget)

        self.container_layout.addStretch()

    def get_selected_configs(self):
        configs = []
        for widget in self.widgets:
            if not widget.is_selected():
                continue
            start, end = widget.get_range()
            configs.append({
                "mutation": widget.get_mutation_name(),
                "start": start,
                "end": end
            })
        return configs

    def get_validation_mode(self):
        return "deterministic"

    # =================================================================
    # INTERFAZ DEL REPORTE INTEGRADO Y COMPLETO
    # =================================================================
    
    def display_report(self, report):
        """Procesa y renderiza el dashboard de cumplimiento con tabla y filtros dinámicos."""
        self.clear_report_view()
        self.current_report = report
        self.grouped_reports = self._group_reports_by_trace(report.trace_reports)
        
        # Ocultar placeholder
        self.icon_placeholder.hide()
        self.txt_placeholder.hide()
        
        # --- ENCABEZADO DEL REPORTE ---
        header_container = QHBoxLayout()
        rep_title = QLabel("GDPR COMPLIANCE & MUTATION AUDIT REPORT")
        rep_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #58a6ff; letter-spacing: 0.5px;")

        header_container.addWidget(rep_title)
        header_container.addStretch()
        self.report_layout.addLayout(header_container)
        
        # Dashboard de KPIs resumidos
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)
        
        total_violations = sum(
            len(r.validator_result.get("violations", []))
            for r in self.grouped_reports
        )
        total_warnings = sum(
            len(r.validator_result.get("warnings", []))
            for r in self.grouped_reports
        )

        cards_data = [
            ("MUTATED TRACES", str(len(self.grouped_reports)), "#58a6ff", "#161b22"),
            ("CRITICAL VIOLATIONS", str(total_violations), "#ff7b72", "#211515"),
            ("SECURITY WARNINGS", str(total_warnings), "#d29922", "#1e1a10")
        ]
        
        for title, val, color, bg in cards_data:
            card = QFrame()
            card.setStyleSheet(f"background-color: {bg}; border: 1px solid {color}; border-radius: 6px; padding: 10px;")
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(8, 8, 8, 8)
            
            lbl_t = QLabel(f"<span style='color:#8b949e; font-size:10px; font-weight:bold;'>{title}</span>")
            lbl_v = QLabel(f"<span style='font-size:22px; font-weight:bold; color:{color};'>{val}</span>")
            
            c_lay.addWidget(lbl_t)
            c_lay.addWidget(lbl_v)
            stats_layout.addWidget(card)
            
        self.report_layout.addLayout(stats_layout)
        
        # Barra de Filtros Integrada
        filters_container = QFrame()
        filters_container.setStyleSheet("background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 4px;")
        filters_layout = QHBoxLayout(filters_container)
        filters_layout.setContentsMargins(8, 4, 8, 4)
        filters_layout.setSpacing(8)
        
        self.severity_filter = QComboBox()
        self.severity_filter.addItems(["ALL", "VIOLATION", "WARNING", "COMPLIANT"])
        self.severity_filter.currentTextChanged.connect(self._populate_table)
        
        self.mutation_filter = QComboBox()
        mutations = sorted({
            mutation_name
            for grouped_report in self.grouped_reports
            for mutation_name in grouped_report.mutation_names
        })
        self.mutation_filter.addItem("ALL")
        self.mutation_filter.addItems(mutations)
        self.mutation_filter.currentTextChanged.connect(self._populate_table)
        
        filters_layout.addWidget(QLabel("Severity:"))
        filters_layout.addWidget(self.severity_filter)
        filters_layout.addWidget(QLabel("Mutation Rule:"))
        filters_layout.addWidget(self.mutation_filter)
        filters_layout.addWidget(QLabel("<span style='color:#8b949e; font-size:11px; margin-left:10px;'>💡 Double-click row to open trail logs</span>"))
        filters_layout.addStretch()
        
        self.report_layout.addWidget(filters_container)
        
        # Tabla Principal del Reporte
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Trace Target ID",
            "Applied Mutation Engine",
            "Validator",
            "Audit Status",
            "Findings Summary",
            "Violations",
            "Warnings"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("QTableWidget { alternate-background-color: #1c2128; }")
        self.table.cellDoubleClicked.connect(self._open_trace_detail)
        
        self.report_layout.addWidget(self.table)
        
        # Llenar la tabla con los datos por primera vez
        self._populate_table()

    def _populate_table(self):
        if not self.current_report:
            return
            
        severity_filter = self.severity_filter.currentText()
        mutation_filter = self.mutation_filter.currentText()

        filtered = []
        for r in self.grouped_reports:
            report_severity = self._display_severity(r.severity)
            if severity_filter != "ALL" and report_severity != severity_filter:
                continue
            if mutation_filter != "ALL" and mutation_filter not in r.mutation_names:
                continue
            filtered.append(r)

        self.filtered_reports = filtered
        self.table.setRowCount(len(filtered))

        for row, r in enumerate(filtered):
            v_count = len(r.validator_result.get("violations", []))
            w_count = len(r.validator_result.get("warnings", []))
            validation_mode = "deterministic"
            display_severity = self._display_severity(r.severity)

            # Trace ID
            item_id = QTableWidgetItem(str(r.trace_id))
            item_id.setTextAlignment(Qt.AlignCenter)
            
            item_mut = QTableWidgetItem(r.mutation_name)
            item_mut.setToolTip("\n".join(r.mutation_names))

            item_mode = QTableWidgetItem(validation_mode.upper())
            item_mode.setTextAlignment(Qt.AlignCenter)

            item_summary = QTableWidgetItem(TraceDetailDialog.issue_summary(r, max_items=2))
            item_summary.setToolTip(TraceDetailDialog.issue_summary(r, max_items=20))
            
            # Status Badge
            item_sev = QTableWidgetItem(f" ● {r.severity}")
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

            # Violaciones
            item_v = QTableWidgetItem(str(v_count))
            item_v.setTextAlignment(Qt.AlignCenter)
            if v_count > 0:
                item_v.setForeground(Qt.GlobalColor.red)

            # Warnings
            item_w = QTableWidgetItem(str(w_count))
            item_w.setTextAlignment(Qt.AlignCenter)
            if w_count > 0:
                item_w.setForeground(Qt.GlobalColor.yellow)

            self.table.setItem(row, 0, item_id)
            self.table.setItem(row, 1, item_mut)
            self.table.setItem(row, 2, item_mode)
            self.table.setItem(row, 3, item_sev)
            self.table.setItem(row, 4, item_summary)
            self.table.setItem(row, 5, item_v)
            self.table.setItem(row, 6, item_w)

        self.table.resizeColumnsToContents()

    @staticmethod
    def _display_severity(severity):
        return "COMPLIANT" if severity == "OK" else severity

    @staticmethod
    def _severity_rank(severity):
        normalized = MutationView._display_severity(severity)
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
                (self._display_severity(report.severity) for report in reports),
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

    def clear_report_view(self):
        """Limpia todo el layout del panel derecho eliminando widgets dinámicos y recupera el placeholder."""
        self.current_report = None
        self.filtered_reports.clear()
        self.grouped_reports.clear()
        
        for i in reversed(range(self.report_layout.count())):
            item = self.report_layout.itemAt(i)
            if item.layout() == self.placeholder_layout:
                continue
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
                
        self.icon_placeholder.show()
        self.txt_placeholder.show()
