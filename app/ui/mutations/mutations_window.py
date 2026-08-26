from functools import partial  # 🛠️ IMPORTANTE: Para asociar argumentos de forma segura en Qt
from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QComboBox,
    QHBoxLayout,
)

from app.mutations.registry.mutation_registry import MUTATION_REGISTRY
from app.mutations.base.mutation_category import MutationCategory
from app.ui.mutations.mutation_config_widget import MutationConfigWidget
from app.ui.main_flow.styles import STYLE


class MutationsWindow(QWidget):
    mutations_applied = Signal(list)

    def __init__(self, model_name, total_traces=100):
        super().__init__()
        self.total_traces = total_traces
        self.widgets = []
        
        # 💡 Única fuente de verdad limpia
        self.mutation_state = {}
        for name in MUTATION_REGISTRY.keys():
            self.mutation_state[name] = {
                "selected": False,
                "range": (0, total_traces - 1)
            }
            
        self.setWindowTitle("Mutation Engine")
        self.resize(1000, 850)
        
        self.setStyleSheet(STYLE)
        self._build_ui(model_name)

    # =====================================================
    # UI BUILDER
    # =====================================================

    def _build_ui(self, model_name):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # TITLE
        title = QLabel(f"MUTATIONS · {model_name}")
        title.setObjectName("BlockTitle")
        main_layout.addWidget(title)

        mode_label = QLabel("Manual mutation selection")
        mode_label.setStyleSheet(
            "color: #9fb3c8; font-weight: bold; padding: 8px; "
            "background-color: #12161f; border: 1px solid #30363d; border-radius: 6px;"
        )
        main_layout.addWidget(mode_label)

        # MANUAL PANEL
        self.manual_panel = QFrame()
        self.manual_panel.setObjectName("MainContainerPanel")
        manual_layout = QVBoxLayout(self.manual_panel)
        manual_layout.setContentsMargins(0, 0, 0, 0)
        manual_layout.setSpacing(12)

        category_row = QHBoxLayout()
        cat_label = QLabel("Category")
        cat_label.setStyleSheet("font-weight: bold; color: #9fb3c8;")
        category_row.addWidget(cat_label)

        self.category_combo = QComboBox()
        self.category_combo.addItems([c.name for c in MutationCategory])
        self.category_combo.currentTextChanged.connect(self._reload_mutations)
        category_row.addWidget(self.category_combo)
        category_row.addStretch()
        manual_layout.addLayout(category_row)

        # Zona Scroll Manual
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QFrame()
        self.container.setObjectName("ScrollContent")
        
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(12, 12, 12, 12)
        self.container_layout.setSpacing(10)
        
        self.scroll.setWidget(self.container)
        manual_layout.addWidget(self.scroll)
        main_layout.addWidget(self.manual_panel)

        # APPLY FOOTER
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #1f2933; max-height: 1px; border: none;")
        main_layout.addWidget(line)

        self.apply_button = QPushButton("⚡ APPLY MUTATIONS")
        self.apply_button.setObjectName("PrimaryButton")
        self.apply_button.clicked.connect(self._apply_mutations)
        main_layout.addWidget(self.apply_button)

        self._reload_mutations()

    # =====================================================
    # LOGIC & EVENTS
    # =====================================================

    def _clear_layout(self, layout):
        """Helper seguro para vaciar layouts eliminando widgets y espaciadores por igual."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                # Quitamos las conexiones activas antes de destruir para evitar llamadas zombie
                try:
                    widget.checkbox.stateChanged.disconnect()
                    widget.range_slider.valueChanged.disconnect()
                except Exception:
                    pass
                widget.setParent(None)
                widget.deleteLater()
            elif item.spacerItem():
                del item

    def _on_checkbox_changed(self, mutation_name, state):
        """Callback en tiempo real. Modificamos orden de parámetros para encajar con partial."""
        is_checked = (state == 2 or state is True)
        self.mutation_state[mutation_name]["selected"] = is_checked

    def _on_slider_changed(self, mutation_name, value):
        """Callback en tiempo real. Modificamos orden de parámetros para encajar con partial."""
        self.mutation_state[mutation_name]["range"] = value

    def _reload_mutations(self):
        # 1. Limpiamos la visualización de forma segura
        self._clear_layout(self.container_layout)
        self.widgets.clear()
        
        category = self.category_combo.currentText()

        # 2. Reconstruimos los widgets pertenecientes a la categoría activa
        for name, data in MUTATION_REGISTRY.items():
            if data["category"].name != category:
                continue

            widget = MutationConfigWidget(name, self.total_traces)
            saved = self.mutation_state[name]
            
            # 3. Restauramos los datos del diccionario maestro bloqueando eventos reactivos
            widget.checkbox.blockSignals(True)
            widget.checkbox.setChecked(saved["selected"])
            widget.checkbox.blockSignals(False)
            
            # Forzamos un refresco diferido limpio para que el QRangeSlider no colapse
            def restore_slider(w=widget, rng=saved["range"]):
                w.range_slider.blockSignals(True)
                w.range_slider.setValue(rng)
                if hasattr(w, '_update_label'):
                    w._update_label()
                w.range_slider.blockSignals(False)
                
            QTimer.singleShot(5, restore_slider)
            
            # 4. 🛠️ CAMBIO CLAVE: Usamos 'partial' en lugar de lambdas para congelar la variable 'name'
            widget.checkbox.stateChanged.connect(
                partial(self._on_checkbox_changed, name)
            )
            widget.range_slider.valueChanged.connect(
                partial(self._on_slider_changed, name)
            )
            
            self.widgets.append(widget)
            self.container_layout.addWidget(widget)

        self.container_layout.addStretch()

    def _apply_mutations(self):
        configs = []
        for mutation_name, state in self.mutation_state.items():
            if not state["selected"]:
                continue
            
            start, end = state["range"]
            configs.append({
                "mutation": mutation_name,
                "start": start,
                "end": end
            })

        self.mutations_applied.emit(configs)
        self.close()
