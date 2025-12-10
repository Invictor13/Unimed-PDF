from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QGroupBox, QSpacerItem, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt
from .styles import BUTTON_STYLE

class LeftPanel(QWidget):
    action_triggered = pyqtSignal(str, object)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        # Allow stylesheet inheritance but provide specific layout constraints
        self.setStyleSheet("background-color: white; border-right: 1px solid #E0E0E0;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(15)

        # File Operations
        self.btn_load = self.create_button("⬆️", "Carregar PDF", "load_pdf")
        layout.addWidget(self.btn_load)

        # Actions
        self.btn_merge = self.create_button("➕", "Unificar PDFs", "merge")
        layout.addWidget(self.btn_merge)

        self.btn_split = self.create_button("✂️", "Separar PDF", "split")
        layout.addWidget(self.btn_split)

        # Compression
        group_compress = QGroupBox("Compactação")
        group_compress.setStyleSheet("QGroupBox { font-weight: bold; color: #333333; border: 1px solid #CCCCCC; border-radius: 5px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }")
        layout_compress = QVBoxLayout(group_compress)

        self.btn_compress_low = self.create_button("⬇️ Baixa", "Compactação Leve", "compress", "low")
        layout_compress.addWidget(self.btn_compress_low)

        self.btn_compress_high = self.create_button("⬇️ Alta", "Compactação Alta", "compress", "high")
        layout_compress.addWidget(self.btn_compress_high)

        layout.addWidget(group_compress)

        # Editing
        self.btn_rotate = self.create_button("🔄", "Rotacionar Seleção", "rotate_selected")
        layout.addWidget(self.btn_rotate)

        self.btn_delete = self.create_button("🗑️", "Excluir Seleção", "delete")
        layout.addWidget(self.btn_delete)

        self.btn_ocr = self.create_button("🔍 OCR", "Reconhecimento de Texto", "ocr")
        layout.addWidget(self.btn_ocr)

        # Selection Input
        layout.addStretch()
        layout.addWidget(QLabel("Seleção Manual (ex: 1,3-5):"))
        self.input_selection = QLineEdit()
        self.input_selection.setPlaceholderText("1, 3-5")
        self.input_selection.returnPressed.connect(self.handle_manual_selection)
        layout.addWidget(self.input_selection)

        self.btn_clear = self.create_button("🧹 Limpar", "Limpar Sessão", "clear_session")
        self.btn_clear.setStyleSheet(self.btn_clear.styleSheet() + "background-color: #666666; border-color: #666666; color: white;")
        layout.addWidget(self.btn_clear)

    def create_button(self, text, tooltip, action_name, data=None):
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # Using a base style for size, but relying on global stylesheet for effects
        # Actually, if I set stylesheet here, I overwrite the global one for this widget unless I am careful.
        # The global STYLESHEET sets generic QPushButton style.
        # But here I want specific sizing/font for these icon buttons.
        # I should merge the styles or append to what comes from global.
        # However, global stylesheet applies to class. Local setStyleSheet applies to instance.
        # Local overrides global.

        # I will inject BUTTON_STYLE content here + specific overrides
        # But BUTTON_STYLE is complex.
        # A better way is to rely on the global STYLESHEET loaded in MainWindow,
        # and here only set properties that are different (font size).
        # But `setStyleSheet` on a widget REPLACES the computed style for that widget if not careful?
        # No, `setStyleSheet` on a widget sets the style sheet for that widget.
        # If I want to use the global style, I shouldn't set a full stylesheet here that conflicts.

        # Let's try to not set a full stylesheet, but just minimal adjustments.
        # But I need "background-color: #F0F0F0" which differs from the "white/primary" in BUTTON_STYLE?
        # The user wanted "Elegance" which implies using the Green/White theme.
        # My previous LeftPanel code used gray buttons. The BUTTON_STYLE uses White/Green.
        # I should probably switch LeftPanel to use the elegant White/Green style too,
        # or a variation.
        # Let's use the BUTTON_STYLE (White with Green border) for LeftPanel too.
        # It looks cleaner.

        # So I will NOT set a custom stylesheet here, except for font size maybe.
        btn.setStyleSheet("font-size: 16px;")

        btn.clicked.connect(lambda: self.action_triggered.emit(action_name, data))
        return btn

    def handle_manual_selection(self):
        text = self.input_selection.text()
        indices = []
        try:
            parts = text.split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    indices.extend(range(start - 1, end))
                else:
                    indices.append(int(part) - 1)
            self.action_triggered.emit("select_pages", indices)
        except ValueError:
            pass # Invalid input

    def update_selection_input(self, selected_indices):
        if not selected_indices:
            self.input_selection.setText("")
            return

        sorted_indices = sorted(selected_indices)
        parts = []
        if not sorted_indices:
             return

        start = sorted_indices[0]
        end = start

        for i in sorted_indices[1:]:
            if i == end + 1:
                end = i
            else:
                if start == end:
                    parts.append(str(start + 1))
                else:
                    parts.append(f"{start + 1}-{end + 1}")
                start = i
                end = i

        if start == end:
            parts.append(str(start + 1))
        else:
            parts.append(f"{start + 1}-{end + 1}")

        self.input_selection.blockSignals(True)
        self.input_selection.setText(", ".join(parts))
        self.input_selection.blockSignals(False)
