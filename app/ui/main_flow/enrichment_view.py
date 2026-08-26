from PySide6.QtWidgets import QTabWidget, QTreeWidget, QTreeWidgetItem, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton, QDialog, QTextEdit
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor
from app.ui.maps.process_map import ProcessMap
from PySide6.QtWidgets import QStyle


class NodeMetricsPopover(QDialog):
    """Bocadillo flotante contextual premium para mostrar métricas y datos GDPR de un nodo."""
    def __init__(self, node_id, node_data, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        
        self.setStyleSheet("""
            QFrame#PopoverCard {
                background-color: #161b22;
                border: 2px solid #30363d;
                border-radius: 8px;
            }
            QLabel {
                background: transparent;
                font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
            }
            QLabel#TitleLabel {
                color: #58a6ff;
                font-weight: 800;
                font-size: 13px;
                border-bottom: 1px solid #30363d;
                padding-bottom: 6px;
                text-transform: uppercase;
            }
            QLabel#MetricLabel {
                color: #c9d1d9;
                font-size: 11px;
            }
            QLabel#WarningLabel {
                color: #ffaa00;
                font-weight: bold;
                font-size: 11px;
                margin-top: 4px;
            }
            QLabel#PerformanceTitle {
                color: #8b949e;
                font-weight: bold;
                font-size: 10px;
                margin-top: 6px;
                border-top: 1px dashed #21262d;
                padding-top: 6px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        card = QFrame()
        card.setObjectName("PopoverCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(6)
        
        title = QLabel(f"📍 {node_id}")
        title.setObjectName("TitleLabel")
        card_layout.addWidget(title)
        
        frequency = node_data.get("frequency", node_data.get("frecuencia", "N/A"))
        freq_label = QLabel(f"<b>Frecuencia absoluta:</b> {frequency}")
        freq_label.setObjectName("MetricLabel")
        card_layout.addWidget(freq_label)
        
        is_gdpr_critical = "verify" in node_id or "consent" in node_id or "privacy" in node_id
        if is_gdpr_critical:
            warn_lbl = QLabel("⚠️ Requiere Auditoría GDPR")
            warn_lbl.setObjectName("WarningLabel")
            card_layout.addWidget(warn_lbl)
            
        perf_metrics = node_data.get("performance")
        if perf_metrics and isinstance(perf_metrics, dict):
            perf_title = QLabel("MÉTRICAS DE RENDIMIENTO")
            perf_title.setObjectName("PerformanceTitle")
            card_layout.addWidget(perf_title)
            
            for key, value in perf_metrics.items():
                clean_key = str(key).replace("_", " ").title()
                if isinstance(value, float):
                    value = f"{value:.2f}"
                lbl = QLabel(f"<b>{clean_key}:</b> {value}")
                lbl.setObjectName("MetricLabel")
                card_layout.addWidget(lbl)
                
        layout.addWidget(card)
        
    def leaveEvent(self, event):
        self.close()

    def mousePressEvent(self, event):
        self.close()


class EnrichmentSuccessDialog(QDialog):
    """Diálogo personalizado y vistoso para notificar el éxito del enriquecimiento."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pipeline Execution Status")
        self.setFixedSize(500, 320)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
            }
            QLabel {
                background: transparent;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(18)
        
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        icon_label = QLabel("✨")
        icon_label.setFixedWidth(40)
        icon_label.setStyleSheet("font-size: 34px; qproperty-alignment: 'AlignLeft | AlignVCenter';")
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        title_label = QLabel("ENRICHMENT COMPLETE")
        title_label.setStyleSheet("font-size: 16px; font-weight: 800; color: #00ffaa; letter-spacing: 0.5px;")
        
        subtitle_label = QLabel("Programmatic privacy control checkpoints successfully injected via OCL Core.")
        subtitle_label.setStyleSheet("font-size: 12px; color: #8b949e;")
        subtitle_label.setWordWrap(True)
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle_label)
        
        header_layout.addWidget(icon_label)
        header_layout.addLayout(text_layout)
        layout.addLayout(header_layout)
        
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #21262d; max-height: 1px; border: none;")
        layout.addWidget(divider)
        
        info_desc = QLabel("The target model has been updated with legal workflow constraints.")
        info_desc.setStyleSheet("font-size: 12px; color: #c9d1d9; line-height: 1.4;")
        info_desc.setWordWrap(True)
        layout.addWidget(info_desc)
        
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)
        
        self.btn_next = QPushButton("Proceed to Mutations\nChoose validation mode and inject faults")
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setStyleSheet("""
            QPushButton {
                background-color: #161b22;
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 14px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #1f242c;
                border-color: #2ea44f;
                color: #2ea44f;
            }
        """)
        
        self.btn_export = QPushButton("💾 Export Enriched Log\nSave current XES dataset structure")
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #161b22;
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 14px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #1f242c;
                border-color: #388bfd;
                color: #388bfd;
            }
        """)
        
        actions_layout.addWidget(self.btn_next, stretch=1)
        actions_layout.addWidget(self.btn_export, stretch=1)
        layout.addLayout(actions_layout)
        
        self.btn_close = QPushButton("Dismiss")
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8b949e;
                font-size: 11px;
                border: none;
                padding: 4px;
            }
            QPushButton:hover {
                color: #c9d1d9;
                text-decoration: underline;
            }
        """)
        layout.addWidget(self.btn_close, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.btn_next.clicked.connect(lambda: self.done(1))
        self.btn_export.clicked.connect(lambda: self.done(2))
        self.btn_close.clicked.connect(self.reject)


class EnrichmentInfoDialog(QDialog):
    def __init__(self, typing_rows, context_summary, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Información del enriquecimiento")
        self.resize(760, 620)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #0d1117;
                color: #c9d1d9;
            }
            QLabel#DialogTitle {
                color: #58a6ff;
                font-size: 16px;
                font-weight: 800;
            }
            QTextEdit {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 12px;
                font-size: 12px;
            }
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #30363d;
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Información del enriquecimiento")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)

        body = QTextEdit()
        body.setReadOnly(True)
        body.setHtml(self._build_html(typing_rows, context_summary))
        layout.addWidget(body)

        actions = QHBoxLayout()
        actions.addStretch()
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.close)
        actions.addWidget(close_btn)
        layout.addLayout(actions)

    @staticmethod
    def _build_html(typing_rows, context_summary):
        activity_items = []
        for row in typing_rows or []:
            activity = row.get("activity", "Actividad desconocida")
            activity_type = row.get("activity_type", "OTHER")
            user_right_type = row.get("user_right_type")
            suffix = f" / {user_right_type}" if user_right_type else ""
            activity_items.append(
                f"<tr><td>{activity}</td><td><b>{activity_type}{suffix}</b></td></tr>"
            )

        if not activity_items:
            activity_items.append(
                "<tr><td colspan='2'>No hay tipado de eventos disponible.</td></tr>"
            )

        return f"""
        <h2 style='color:#58a6ff;'>Contexto inferido</h2>
        <p style='line-height:1.45;'>{context_summary or 'No hay contexto inferido disponible.'}</p>
        <h2 style='color:#58a6ff;'>Tipado de eventos</h2>
        <table cellspacing='0' cellpadding='6' width='100%' style='border-collapse:collapse;'>
            <tr style='background-color:#161b22; color:#8b949e;'>
                <th align='left'>Actividad</th>
                <th align='left'>ActivityType asignado</th>
            </tr>
            {''.join(activity_items)}
        </table>
        """


class EnrichmentView(QWidget):
    def __init__(self, on_enrich, on_export, on_info, on_next, on_node_clicked=None):
        super().__init__()
        self.on_enrich_callback = on_enrich
        self.on_export_callback = on_export
        self.on_next_callback = on_next
        self.on_node_clicked_callback = on_node_clicked
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(18)

        # =====================================================
        # 1. PANEL LATERAL IZQUIERDO DE CONTROL (REDISEÑADO PREMIUM)
        # =====================================================
        panel = QFrame()
        panel.setObjectName("ToolBlock")
        panel.setFixedWidth(320)
        
        # Estilos centralizados (Actualizados para soportar el TreeWidget interactivo)
        panel.setStyleSheet("""
            .QFrame#ToolBlock {
                background-color: #12161f;
                border: 1px solid #21262d;
                border-radius: 12px;
            }
            QLabel#SectionTitle {
                color: #ffffff;
                font-size: 16px;
                font-weight: 800;
                letter-spacing: 0.8px;
                background: transparent;
            }
            QLabel#FileLabel {
                color: #58a6ff;
                font-size: 12px;
                font-family: monospace;
                font-weight: 600;
                background: transparent;
            }
            QLabel#BlockTitle {
                color: #8b949e;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
                text-transform: uppercase;
                background: transparent;
            }
            
            QPushButton#EnrichBtn {
                background-color: #1f6feb;
                color: #ffffff;
                border: 1px solid transparent;
                border-radius: 6px;
                padding: 12px;
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 0.3px;
            }
            QPushButton#EnrichBtn:hover {
                background-color: #388bfd;
            }
            QPushButton#EnrichBtn:pressed {
                background-color: #0c4089;
            }
            
            QPushButton#SecBtn {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 10px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton#SecBtn:hover {
                background-color: #30363d;
                color: #ffffff;
                border-color: #8b949e;
            }
            QPushButton#SecBtn:disabled {
                background-color: #161b22;
                color: #484f58;
                border-color: #21262d;
            }
            
            QFrame#MetricsCard {
                background-color: #0d1117;
                border: 1px solid #21262d;
                border-radius: 8px;
            }
            QLabel#MetricKey {
                color: #8b949e;
                font-size: 12px;
                font-weight: 500;
                background: transparent;
            }
            QLabel#MetricValue {
                color: #f0f6fc;
                font-size: 12px;
                font-family: monospace;
                font-weight: 700;
                background: transparent;
            }
            
            /* Estilos Premium para el Árbol de Información */
            QTreeWidget#InfoTree {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #21262d;
                border-radius: 8px;
                padding: 4px;
                font-size: 11px;
            }
            QTreeWidget#InfoTree::item {
                padding: 6px;
                border-bottom: 1px solid #161b22;
            }
            QTreeWidget#InfoTree::item:hover {
                background-color: #21262d;
                color: #ffffff;
                border-radius: 4px;
            }
            QTreeWidget#InfoTree::item:selected {
                background-color: #1f6feb;
                color: #ffffff;
                border-radius: 4px;
            }
        """)
        
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(24, 24, 24, 24)
        panel_layout.setSpacing(16)

        # Fila superior de cabecera
        header_layout = QHBoxLayout()
        title = QLabel("GDPR ENRICHMENT")
        title.setObjectName("SectionTitle")
        
        info_button = QPushButton()
        pixmap = self.style().standardPixmap(QStyle.StandardPixmap.SP_MessageBoxInformation)
        info_button.setIcon(pixmap)
        info_button.setFixedSize(28, 28)
        info_button.setCursor(Qt.CursorShape.PointingHandCursor)
        info_button.setToolTip("Ver reglas OCL y metodología de cumplimiento del RGPD")
        info_button.setStyleSheet("""
            QPushButton { 
                background-color: #21262d; 
                border: 1px solid #30363d; 
                border-radius: 6px; 
                padding: 4px;
            }
            QPushButton:hover { 
                background-color: #30363d; 
                border-color: #8b949e;
            }
        """)
        info_button.clicked.connect(on_info)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(info_button)
        panel_layout.addLayout(header_layout)

        # Información del archivo de registro cargado
        self.file_label = QLabel("LOG: -")
        self.file_label.setObjectName("FileLabel")
        self.file_label.setWordWrap(True)
        panel_layout.addWidget(self.file_label)
        
        panel_layout.addSpacing(4)

        # Botonera de flujo operativo primario
        self.enrich_button = QPushButton("🔐 GENERATE GDPR TRACES")
        self.enrich_button.setObjectName("EnrichBtn")
        self.enrich_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.enrich_button.clicked.connect(self._handle_enrich_click)

        self.export_button = QPushButton("💾 EXPORT ENRICHED LOG")
        self.export_button.setObjectName("SecBtn")
        self.export_button.setEnabled(False)
        self.export_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_button.clicked.connect(on_export)

        panel_layout.addWidget(self.enrich_button)
        panel_layout.addWidget(self.export_button)
        
        panel_layout.addSpacing(12)
        
        # Etiqueta de sección de métricas
        metrics_title = QLabel("PROCESS METRICS")
        metrics_title.setObjectName("BlockTitle")
        panel_layout.addWidget(metrics_title)
        
        metrics_card = QFrame()
        metrics_card.setObjectName("MetricsCard")
        metrics_card_layout = QVBoxLayout(metrics_card)
        metrics_card_layout.setContentsMargins(16, 16, 16, 16)
        metrics_card_layout.setSpacing(12)
        
        self.metrics_cases = self._add_metric_row(metrics_card_layout, "Cases", "-")
        self.metrics_events = self._add_metric_row(metrics_card_layout, "Events", "-")
        self.metrics_activities = self._add_metric_row(metrics_card_layout, "Activities", "-")
        self.metrics_variants = self._add_metric_row(metrics_card_layout, "Variants", "-")
        self.metrics_avg_trace = self._add_metric_row(metrics_card_layout, "Avg Length", "-")
        
        panel_layout.addWidget(metrics_card)

        self._last_typing_rows = []
        self._last_context_summary = "Ejecuta el enriquecimiento para ver el contexto inferido."

        # =====================================================
        # CAMBIO: TÍTULO Y WIDGET INTERACTIVO DE ENRIQUECIMIENTO
        # =====================================================
        typing_title = QLabel("INFORMACIÓN DEL ENRIQUECIMIENTO")
        typing_title.setObjectName("BlockTitle")
        panel_layout.addWidget(typing_title)

        # Reemplazamos QTextEdit por un QTreeWidget interactivo y elegante
        self.enrichment_tree = QTreeWidget()
        self.enrichment_tree.setObjectName("InfoTree")
        self.enrichment_tree.setHeaderHidden(True)  # Ocultamos la cabecera para que parezca una lista limpia
        self.enrichment_tree.setFixedHeight(180)
        
        # Nodo inicial indicativo
        initial_item = QTreeWidgetItem([None, "Ejecuta el enriquecimiento para ver los detalles."])
        self.enrichment_tree.addTopLevelItem(initial_item)
        
        panel_layout.addWidget(self.enrichment_tree)
        self.enrichment_tree.setVisible(False)

        self.enrichment_info_button = QPushButton("INFO DEL ENRIQUECIMIENTO")
        self.enrichment_info_button.setObjectName("SecBtn")
        self.enrichment_info_button.setEnabled(False)
        self.enrichment_info_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.enrichment_info_button.clicked.connect(self._show_enrichment_info)

        self.enrichment_info_status = QLabel("Ejecuta el enriquecimiento para ver el tipado y el contexto inferido.")
        self.enrichment_info_status.setWordWrap(True)
        self.enrichment_info_status.setStyleSheet("color: #8b949e; font-size: 11px;")

        panel_layout.addWidget(self.enrichment_info_button)
        panel_layout.addWidget(self.enrichment_info_status)
        panel_layout.addStretch()
        
        # Agregar el panel al layout principal
        main_layout.addWidget(panel)


        # Botón inferior de transiciones del flujo
        self.next_button = QPushButton("PROCEED TO MUTATIONS")
        self.next_button.setEnabled(False)
        self._update_next_button_style()
        self.next_button.clicked.connect(on_next)
        panel_layout.addWidget(self.next_button)

        # =====================================================
        # 2. PANEL DERECHO: CONTENEDOR MULTI-TAB DE MAPAS
        # =====================================================
        self.map_container = QWidget()
        map_container_layout = QVBoxLayout(self.map_container)
        map_container_layout.setContentsMargins(0, 0, 0, 0)
        map_container_layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::panel {
                border: 1px solid #30363d;
                background-color: #0d1117;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #161b22;
                color: #8b949e;
                border: 1px solid #30363d;
                border-bottom: none;
                padding: 10px 18px;
                font-weight: bold;
                font-size: 11px;
                font-family: monospace;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #12161f;
                color: #58a6ff;
                border-bottom: 2px solid #58a6ff;
            }
            QTabBar::tab:hover:not(:selected) {
                background: #21262d;
                color: #c9d1d9;
            }
        """)

        self.process_map_original = ProcessMap()
        self.process_map_gdpr = ProcessMap()
        
        self.process_map_original.node_click_callback = self._on_node_clicked_handler
        self.process_map_gdpr.node_click_callback = self._on_node_clicked_handler

        self.tab_original = self._create_map_viewport(self.process_map_original, "ORIGINAL SPECIFICATION")
        self.tab_gdpr = self._create_map_viewport(self.process_map_gdpr, "ENRICHED COMPLIANCE MODEL")

        self.tab_widget.addTab(self.tab_original, "🧩 ORIGINAL LOG MAP")
        self.tab_widget.addTab(self.tab_gdpr, "🔐 GDPR ENRICHED MAP")
        self.tab_widget.setTabEnabled(1, False)

        map_container_layout.addWidget(self.tab_widget)

        # Overlay de carga
        self.loading_overlay = QFrame(self.map_container)
        self.loading_overlay.setObjectName("LoadingOverlay")
        self.loading_overlay.setVisible(False)
        self.loading_overlay.setStyleSheet("""
            QFrame#LoadingOverlay {
                background-color: rgba(13, 17, 23, 0.9);
                border: 1px solid #30363d;
                border-radius: 8px;
            }
            QLabel {
                color: #58a6ff;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        overlay_layout = QVBoxLayout(self.loading_overlay)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.setSpacing(15)

        spinner_label = QLabel("⏳")
        spinner_label.setStyleSheet("font-size: 50px;")
        spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        loading_text = QLabel("ENRICHING LOG DATASET CONTEXTS...\nEvaluating compliance frameworks via OCL Core.")
        loading_text.setStyleSheet("font-size: 13px; color: #c9d1d9; font-family: monospace;")
        loading_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        overlay_layout.addWidget(spinner_label)
        overlay_layout.addWidget(loading_text)

        main_layout.addWidget(panel)
        main_layout.addWidget(self.map_container, stretch=1)

    def update_activity_typing(self, typing_rows, context_summary=None):
        self._last_typing_rows = typing_rows or []
        self._last_context_summary = context_summary or "No hay contexto inferido disponible."
        has_info = bool(self._last_typing_rows) or bool(context_summary)

        self.enrichment_info_button.setEnabled(has_info)

        if has_info:
            self.enrichment_info_status.setText(
                f"{len(self._last_typing_rows)} actividades tipadas. Pulsa el botón para ver el contexto inferido."
            )
        else:
            self.enrichment_info_status.setText(
                "Ejecuta el enriquecimiento para ver el tipado y el contexto inferido."
            )
        return

    def _update_activity_typing_tree(self, typing_rows):
        """Actualiza el árbol interactivo con el tipado y los contextos."""
        self.enrichment_tree.clear()

        if not typing_rows:
            self.enrichment_tree.addTopLevelItem(QTreeWidgetItem(["No hay información disponible."]))
            return

        for row in typing_rows:
            activity = row.get("activity", "Actividad Desconocida")
            activity_type = row.get("activity_type", "OTHER")
            user_right_type = row.get("user_right_type")
            
            # Formateamos el texto del Tipo Principal
            tipo_str = f"🏷️ Tipo: {activity_type}"
            if user_right_type:
                tipo_str += f" / {user_right_type}"

            # 1. Creamos el Nodo Padre (La Actividad)
            parent_item = QTreeWidgetItem([activity])
            parent_item.setToolTip(0, f"Clic para expandir detalles de: {activity}")
            
            # 2. Creamos los Nodos Hijos (Los detalles legibles)
            type_item = QTreeWidgetItem([tipo_str])
            parent_item.addChild(type_item)
            
            # Agregamos los detalles del contexto de forma condicional y legible
            # Nota: Asegúrate de que tu backend pase estas claves o cámbialas por tus nombres reales.
            contexto_origen = row.get("context_source", "No especificado")
            regla_aplicada = row.get("matched_rule", "Ninguna")
            
            context_item = QTreeWidgetItem([f"🔍 Origen: {contexto_origen}"])
            rule_item = QTreeWidgetItem([f"📜 Regla: {regla_aplicada}"])
            
            parent_item.addChild(context_item)
            parent_item.addChild(rule_item)

            # Insertamos la actividad al árbol principal
            self.enrichment_tree.addTopLevelItem(parent_item)


    def _show_enrichment_info(self):
        dialog = EnrichmentInfoDialog(
            self._last_typing_rows,
            self._last_context_summary,
            self,
        )
        dialog.exec()

    def _add_metric_row(self, layout, key, value):
        # Método auxiliar placeholder por si acaso no venía en tu fragmento
        row = QHBoxLayout()
        k_lbl = QLabel(key)
        k_lbl.setObjectName("MetricKey")
        v_lbl = QLabel(value)
        v_lbl.setObjectName("MetricValue")
        row.addWidget(k_lbl)
        row.addStretch()
        row.addWidget(v_lbl)
        layout.addLayout(row)
        return v_lbl

    def _handle_enrich_click(self):
        if self.on_enrich_callback:
            self.on_enrich_callback()

    def _on_node_clicked_handler(self, node_id, node_data):
        extended_data = node_data.copy()
        if self.on_node_clicked_callback:
            perf_metrics = self.on_node_clicked_callback(node_id)
            if perf_metrics:
                extended_data["performance"] = perf_metrics
                
        popover = NodeMetricsPopover(node_id, extended_data, self)
        cursor_pos = QCursor.pos()
        popover.move(cursor_pos + QPoint(15, 10))
        popover.show()

    def _create_map_viewport(self, map_widget, layer_title):
        viewport = QWidget()
        viewport_layout = QVBoxLayout(viewport)
        viewport_layout.setContentsMargins(0, 0, 0, 0)
        viewport_layout.setSpacing(0)

        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border-bottom: 1px solid #30363d;
                padding: 6px;
            }
            QLabel {
                color: #8b949e;
                font-size: 10px;
                font-family: monospace;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton {
                background-color: #21262d;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: #30363d;
                border-color: #8b949e;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #0d1117;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 2, 10, 2)

        layer_label = QLabel(f"📍 VIEWPORT :: {layer_title}")
        toolbar_layout.addWidget(layer_label)
        toolbar_layout.addStretch()

        btn_zoom_in = QPushButton("➕")
        btn_zoom_in.setToolTip("Zoom In")
        btn_zoom_in.clicked.connect(lambda: self._execute_map_zoom(map_widget, 1.2))

        btn_zoom_out = QPushButton("➖")
        btn_zoom_out.setToolTip("Zoom Out")
        btn_zoom_out.clicked.connect(lambda: self._execute_map_zoom(map_widget, 0.8))

        btn_reset = QPushButton("🔄")
        btn_reset.setToolTip("Reset Viewport")
        btn_reset.clicked.connect(lambda: self._execute_map_zoom(map_widget, 1.0, reset=True))

        toolbar_layout.addWidget(btn_zoom_out)
        toolbar_layout.addWidget(btn_zoom_in)
        toolbar_layout.addWidget(btn_reset)

        map_widget.setStyleSheet("background-color: white; border: none;")

        viewport_layout.addWidget(toolbar)
        viewport_layout.addWidget(map_widget, stretch=1)
        return viewport

    def _execute_map_zoom(self, map_widget, factor, reset=False):
        target_view = map_widget.view if hasattr(map_widget, 'view') else map_widget
        if hasattr(target_view, 'scene') and target_view.scene():
            if reset:
                target_view.fitInView(target_view.scene().sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            else:
                target_view.scale(factor, factor)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.loading_overlay.resize(self.map_container.size())

    def set_loading_state(self, is_loading):
        self.loading_overlay.resize(self.map_container.size())
        self.loading_overlay.setVisible(is_loading)
        self.enrich_button.setEnabled(not is_loading)
        if not is_loading:
            self._update_next_button_style()

    def _handle_enrich_click(self):
        self.set_loading_state(True)
        self.repaint()
        
        self.on_enrich_callback()
        
        self.set_loading_state(False)
        self.next_button.setEnabled(True)
        self._update_next_button_style()
        
        self.tab_widget.setTabEnabled(1, True)
        self.tab_widget.setCurrentIndex(1)
        
        self._show_success_dialog()

    def reset_tabs(self):
        # Adaptado para limpiar el nuevo Tree Widget
        self.tab_widget.setTabEnabled(1, False)
        self.tab_widget.setCurrentIndex(0)
        self.enrichment_tree.clear()
        self.enrichment_tree.addTopLevelItem(QTreeWidgetItem(["Ejecuta el enriquecimiento para ver los detalles."]))


    def _show_success_dialog(self):
        dialog = EnrichmentSuccessDialog(self)
        result = dialog.exec()
        if result == 1:
            self.on_next_callback()
        elif result == 2:
            self.on_export_callback()

    def _update_next_button_style(self):
        if self.next_button.isEnabled():
            self.next_button.setStyleSheet("""
                QPushButton {
                    background-color: #2ea44f;
                    color: #ffffff;
                    font-weight: bold;
                    font-size: 13px;
                    border: 1px solid #34d058;
                    border-radius: 6px;
                    padding: 14px;
                }
                QPushButton:hover {
                    background-color: #22863a;
                    border-color: #2ea44f;
                }
            """)
            self.next_button.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.next_button.setStyleSheet("""
                QPushButton {
                    background-color: #161b22;
                    color: #484f58;
                    font-weight: bold;
                    font-size: 13px;
                    border: 1px solid #21262d;
                    border-radius: 6px;
                    padding: 14px;
                }
            """)
            self.next_button.setCursor(Qt.CursorShape.ForbiddenCursor)

    def update_metrics(self, metrics):
        self.metrics_cases.setText(str(metrics['cases']))
        self.metrics_events.setText(str(metrics['events']))
        self.metrics_activities.setText(str(metrics['activities']))
        self.metrics_variants.setText(str(metrics['variants']))
        self.metrics_avg_trace.setText(str(metrics['avg_trace_length']))

    def set_original_graph(self, graph):
        if hasattr(self.process_map_original, 'set_graph'):
            self.process_map_original.set_graph(graph)
        elif hasattr(self.process_map_original, 'update_graph'):
            self.process_map_original.update_graph(graph)
            
        target_view = self.process_map_original.view if hasattr(self.process_map_original, 'view') else self.process_map_original
        if hasattr(target_view, 'scene') and target_view.scene():
            target_view.fitInView(target_view.scene().sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def set_gdpr_graph(self, graph):
        if hasattr(self.process_map_gdpr, 'set_graph'):
            self.process_map_gdpr.set_graph(graph)
        elif hasattr(self.process_map_gdpr, 'update_graph'):
            self.process_map_gdpr.update_graph(graph)
            
        target_view = self.process_map_gdpr.view if hasattr(self.process_map_gdpr, 'view') else self.process_map_gdpr
        if hasattr(target_view, 'scene') and target_view.scene():
            target_view.fitInView(target_view.scene().sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            
