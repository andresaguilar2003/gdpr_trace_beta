from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QFileDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
    QFrame, QStatusBar, QStackedWidget, QPushButton, QDialog
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor

from app.ui.gdpr_rulesInfo_dialog import GdprRulesInfoDialog
from app.ui.main_flow.styles import STYLE
from app.controllers.log_controller import LogController

# Importación de las nuevas pantallas modulares
from app.ui.main_flow.welcome_view import WelcomeView
from app.ui.main_flow.enrichment_view import EnrichmentView
from app.ui.main_flow.mutation_view import MutationView


# 🌟 NUEVA CLASE: Mini ventanita flotante estilo bocadillo de información (Popover)
class NodeMetricsPopover(QDialog):
    def __init__(self, node_id, metrics, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        
        # Diseño visual adaptado al estilo oscuro de la aplicación
        self.setStyleSheet("""
            QFrame#PopoverCard {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
            }
            QLabel#TitleLabel {
                color: #58a6ff;
                font-weight: bold;
                font-size: 12px;
                border-bottom: 1px solid #21262d;
                padding-bottom: 4px;
            }
            QLabel#MetricLabel {
                color: #c9d1d9;
                font-size: 11px;
            }
            QLabel#NoDataLabel {
                color: #8b949e;
                font-style: italic;
                font-size: 11px;
            }
        """)

        # Contenedor principal con efecto de tarjeta
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        card = QFrame()
        card.setObjectName("PopoverCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(6)
        
        # Título con el ID de la actividad
        title = QLabel(f"📍 {node_id}".upper())
        title.setObjectName("TitleLabel")
        card_layout.addWidget(title)
        
        # Inyección dinámica de métricas
        if metrics and isinstance(metrics, dict):
            for key, value in metrics.items():
                # Formatear claves estéticas (ej: "absolute_frequency" -> "Absolute Frequency")
                clean_key = str(key).replace("_", " ").title()
                lbl = QLabel(f"<b>{clean_key}:</b> {value}")
                lbl.setObjectName("MetricLabel")
                card_layout.addWidget(lbl)
        else:
            no_data = QLabel("No hay métricas de rendimiento avanzadas disponibles para este nodo.")
            no_data.setObjectName("NoDataLabel")
            no_data.setWordWrap(True)
            card_layout.addWidget(no_data)
            
        layout.addWidget(card)
        
    def leaveEvent(self, event):
        """Cierra el bocadillo automáticamente si el usuario saca el ratón de la ventana"""
        self.close()

    def mousePressEvent(self, event):
        """Permite cerrar el bocadillo haciendo clic directo sobre él"""
        self.close()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("SYSTEM_CORE::GDPR_ENRICHER_V1.0")
        self.resize(1350, 900)

        self.controller = LogController()
        self.current_log_path = None
        self.current_model = None
        self.gdpr_model_name = None

        self.setStyleSheet(STYLE)
        self._build_ui()

    def _build_ui(self):
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ---------------- HEADER COMÚN ----------------
        header = QFrame()
        header.setObjectName("HeaderFrame")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)

        title_label = QLabel("GDPR PROCESS TRACE ANALYZER")
        self.system_status = QLabel("● SYSTEM ONLINE")
        
        # 🔄 Rediseño del Botón Reset (Estilo integrado, limpio y no invasivo)
        self.reset_button = QPushButton("🔄 Reset App")
        self.reset_button.setVisible(False)
        self.reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8b949e;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: bold;
                text-transform: uppercase;
            }
            QPushButton:hover {
                background-color: #21262d;
                color: #f85149;
                border-color: #f85149;
            }
        """)
        self.reset_button.clicked.connect(self._reset_to_welcome)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.reset_button)
        header_layout.addSpacing(15)
        header_layout.addWidget(self.system_status)
        main_layout.addWidget(header)

        # ---------------- CONTENEDOR DE PANTALLAS (Stacked Widget) ----------------
        self.stacked_widget = QStackedWidget()

        # Inicialización de vistas pasando los Callbacks correspondientes
        self.welcome_view = WelcomeView(on_load_clicked=self.load_log)
        
        # 🛠️ CORRECCIÓN: Se añade 'on_node_clicked=self._fetch_node_metrics'
        self.enrichment_view = EnrichmentView(
            on_enrich=self.enrich_traces,
            on_export=self.export_dataset,
            on_info=self.show_gdpr_info_dialog,
            on_next=self._go_to_mutations_screen,
            on_node_clicked=self._fetch_node_metrics  # 🌟 Sincronización del click del mapa
        )
        self.mutation_view = MutationView(
            on_open_mutations=self.open_mutations_window,
            on_export_mutated=self.export_mutated_dataset,
            on_back=self._go_to_enrichment_screen
        )

        # Añadir pantallas al Stack
        self.stacked_widget.addWidget(self.welcome_view)    # Index 0
        self.stacked_widget.addWidget(self.enrichment_view) # Index 1
        self.stacked_widget.addWidget(self.mutation_view)   # Index 2

        main_layout.addWidget(self.stacked_widget, stretch=1)

        # ---------------- STATUS BAR COMÚN ----------------
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready.")

        self.setCentralWidget(main_container)

    # ---------------- NAVEGACIÓN ENTRE PANTALLAS ----------------

    def _reset_to_welcome(self):
        self.current_log_path = None
        self.current_model = None
        self.gdpr_model_name = None
        
        self.reset_button.setVisible(False)
        self.enrichment_view.next_button.setEnabled(False)
        if hasattr(self.enrichment_view, '_update_next_button_style'):
            self.enrichment_view._update_next_button_style()
            
        if hasattr(self.enrichment_view, 'reset_tabs'):
            self.enrichment_view.reset_tabs()
            
        self.mutation_view.clear_report_view()
        self.enrichment_view.file_label.setText("LOG: -")
        
        self.stacked_widget.setCurrentIndex(0)
        self.statusBar().showMessage("System reset. Awaiting new event log.")


    def _go_to_enrichment_screen(self):
        self.stacked_widget.setCurrentIndex(1)
        self.statusBar().showMessage("Viewing Enrichment phase.")

    def _go_to_mutations_screen(self):
        total_traces = self.controller.get_total_gdpr_traces()
        self.mutation_view.setup_mutation_config(self.current_model, total_traces)
        self.stacked_widget.setCurrentIndex(2)
        self.statusBar().showMessage("Viewing Mutation Engine testing phase.")

    # ---------------- LÓGICA DE BACKEND ASOCIADA (MainWindow) ----------------

    def load_log(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Event Log", "", "XES files (*.xes *.xes.gz)"
        )
        if not file_path:
            return

        try:
            self._set_processing_state(True)
            self.current_log_path = file_path

            graph, metrics = self.controller.process_log(file_path)
            filename = Path(file_path).name
            self.current_model = f"🧩 ORIGINAL · {filename}"

            self.enrichment_view.file_label.setText(f"LOG: {filename}")
            self.enrichment_view.set_original_graph(graph)
            self.enrichment_view.update_metrics(metrics)
            self.enrichment_view.update_activity_typing([])

            self.enrichment_view.next_button.setEnabled(False)
            if hasattr(self.enrichment_view, '_update_next_button_style'):
                self.enrichment_view._update_next_button_style()

            self.reset_button.setVisible(True)
            self.stacked_widget.setCurrentIndex(1)

            self.statusBar().showMessage(f"Loaded log: {filename}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.statusBar().showMessage(f"Error loading log: {str(e)}")
        finally:
            self._set_processing_state(False)

    def enrich_traces(self):
        if not self.current_log_path:
            return

        try:
            self._set_processing_state(True)
            graph = self.controller.create_gdpr_compliant_log(self.current_log_path)

            filename = Path(self.current_log_path).name
            self.current_model = f"🔐 GDPR · {filename}"
            self.gdpr_model_name = self.current_model

            self.enrichment_view.set_gdpr_graph(graph)
            self.enrichment_view.update_activity_typing(
                self.controller.get_last_activity_typing(),
                self.controller.get_last_enrichment_context_summary()
            )
            self.enrichment_view.next_button.setEnabled(True)
            if hasattr(self.enrichment_view, '_update_next_button_style'):
                self.enrichment_view._update_next_button_style()

            self.statusBar().showMessage("GDPR-compliant traces generated.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.statusBar().showMessage(f"Enrichment error: {str(e)}")
        finally:
            self._set_processing_state(False)

    def open_mutations_window(self):
        if not self.current_model or "GDPR" not in self.current_model:
            self.statusBar().showMessage("Mutations only available for GDPR models")
            return
            
        configs = self.mutation_view.get_selected_configs()
        if not configs:
            self.statusBar().showMessage("No mutations or ranges selected to inject.")
            return
            
        validation_mode = self.mutation_view.get_validation_mode()
        self.apply_mutations(configs, validation_mode)

    def apply_mutations(self, mutation_configs, validation_mode):
        try:
            self._set_processing_state(True)
            graph, report = self.controller.apply_mutations(
                mutation_configs,
                validation_mode=validation_mode
            )

            self.current_model = f"🧪 MUTATED · {self.current_model}"
            self.mutation_view.display_report(report)

            self.statusBar().showMessage(
                f"Mutations applied · {report.total_violations} violations · {report.total_warnings} warnings"
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.statusBar().showMessage(f"Mutation error: {str(e)}")
        finally:
            self._set_processing_state(False)

    def _set_processing_state(self, processing):
        self.welcome_view.set_loading_state(processing)
        self.enrichment_view.enrich_button.setEnabled(not processing)
        self.mutation_view.mutation_button.setEnabled(not processing)

        if processing:
            self.system_status.setText("[ PROCESSING ]")
        else:
            self.system_status.setText("[ SYSTEM ONLINE ]")

    def show_gdpr_info_dialog(self):
        dialog = GdprRulesInfoDialog(self)
        dialog.exec()

    def export_dataset(self):
        if not hasattr(self, "gdpr_model_name"):
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Enriched Log", "", "XES files (*.xes)")
        if file_path:
            try:
                self.controller.export_gdpr_log(file_path)
                self.statusBar().showMessage(f"Dataset exported to: {file_path}")
            except Exception as e:
                self.statusBar().showMessage(f"Export error: {str(e)}")

    def export_mutated_dataset(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Non-Compliant Log", "", "XES files (*.xes)")
        if file_path:
            try:
                self.controller.export_mutated_log(file_path)
                self.statusBar().showMessage(f"Non-compliant dataset exported: {file_path}")
            except Exception as e:
                self.statusBar().showMessage(f"Export error: {str(e)}")

    # 🌟 MÉTODO PUENTE MODIFICADO PARA DESPLEGAR EL POPUP EN EL CURSOR
    def _fetch_node_metrics(self, node_id):
        """Consulta métricas al controlador y las devuelve a la vista"""
        if hasattr(self.controller, "get_node_performance_metrics"):
            return self.controller.get_node_performance_metrics(node_id)
        return None
