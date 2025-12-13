from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QGroupBox, QFileDialog, QFrame, QMessageBox, QInputDialog
)
from PyQt6.QtCore import pyqtSignal, Qt
from .styles import BUTTON_STYLE, COLOR_TEXT_LIGHT, COLOR_PRIMARY

class LeftPanel(QFrame):
    action_triggered = pyqtSignal(str, object)

    def __init__(self, main_window):
        super().__init__(main_window)
        self.setObjectName("LeftPanel")
        self.init_ui()

    def create_button(self, text, tooltip, action_name, data=None, connect_default=True, icon_char=None):
        # Uses text and optional emoji/char as icon
        if icon_char:
            text = f"{icon_char}  {text}"

        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setAccessibleName(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        if connect_default:
            btn.clicked.connect(lambda: self.action_triggered.emit(action_name, data))
        return btn

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 20, 15, 20)

        group_style = f"QGroupBox {{ color: {COLOR_TEXT_LIGHT}; border: 1px solid #444444; margin-top: 10px; font-weight: bold; }} QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 3px; }}"

        # --- Arquivos ---
        group_files = QGroupBox("ARQUIVOS")
        group_files.setStyleSheet(group_style)
        layout_files = QVBoxLayout(group_files)
        layout_files.setSpacing(10)

        self.btn_load = self.create_button("Carregar PDFs", "Carregar arquivos", "load_pdf", connect_default=False, icon_char="📂")
        self.btn_load.clicked.connect(self.on_load_clicked)
        layout_files.addWidget(self.btn_load)

        self.btn_clear = self.create_button("Limpar Sessão", "Limpar tudo", "clear_session", icon_char="🗑️")
        # Darker gray for clear
        self.btn_clear.setStyleSheet(f"QPushButton {{ background-color: #444444; color: white; border: none; padding: 10px; border-radius: 4px; font-weight: bold; font-size: 14px; }} QPushButton:hover {{ background-color: #333333; }}")
        layout_files.addWidget(self.btn_clear)

        layout.addWidget(group_files)


        # --- Ações ---
        group_actions = QGroupBox("AÇÕES")
        group_actions.setStyleSheet(group_style)
        layout_actions = QVBoxLayout(group_actions)
        layout_actions.setSpacing(10)

        self.btn_merge = self.create_button("Unificar", "Salvar tudo em um PDF", "merge", icon_char="📑")
        layout_actions.addWidget(self.btn_merge)

        self.btn_split = self.create_button("Separar", "Salvar páginas selecionadas", "split", icon_char="✂️")
        layout_actions.addWidget(self.btn_split)

        self.btn_rotate = self.create_button("Rotacionar", "Rotacionar seleção 90°", "rotate_selected", icon_char="🔄")
        layout_actions.addWidget(self.btn_rotate)

        self.btn_delete = self.create_button("Excluir", "Remover seleção", "delete", icon_char="❌")
        self.btn_delete.setObjectName("DeleteButton")
        layout_actions.addWidget(self.btn_delete)

        layout.addWidget(group_actions)

        # --- Ferramentas ---
        group_tools = QGroupBox("FERRAMENTAS")
        group_tools.setStyleSheet(group_style)
        layout_tools = QVBoxLayout(group_tools)
        layout_tools.setSpacing(10)

        self.btn_ocr = self.create_button("OCR (Texto)", "Reconhecimento de Texto", "ocr", icon_char="🔍")
        layout_tools.addWidget(self.btn_ocr)

        # Compression Sub-Layout
        lbl_compress = QLabel("Compactação:")
        lbl_compress.setStyleSheet("color: #CCCCCC; font-size: 12px; margin-top: 5px;")
        layout_tools.addWidget(lbl_compress)

        row_compress = QWidget()
        row_layout = QVBoxLayout(row_compress) # Changing to Vertical for better button look
        row_layout.setContentsMargins(0,0,0,0)

        self.btn_compress_low = self.create_button("Baixa (Estrutura)", "Remove metadados", "compress", "low", icon_char="📉")
        self.btn_compress_low.setStyleSheet("font-size: 13px;")
        row_layout.addWidget(self.btn_compress_low)

        self.btn_compress_high = self.create_button("Alta (Imagens)", "Reduz qualidade de imagens", "compress", "high", icon_char="📉")
        self.btn_compress_high.setStyleSheet("font-size: 13px;")
        row_layout.addWidget(self.btn_compress_high)

        layout_tools.addWidget(row_compress)

        layout.addWidget(group_tools)

        # --- Seleção ---
        layout.addStretch()
        label_selecao = QLabel("Seleção por Intervalo:")
        label_selecao.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; font-weight: bold;")
        layout.addWidget(label_selecao)

        self.input_selection = QLineEdit()
        self.input_selection.setPlaceholderText("Ex: 1, 3-5")
        self.input_selection.setAccessibleName("Seleção de páginas por intervalo")
        self.input_selection.textChanged.connect(self.on_range_input_changed)
        layout.addWidget(self.input_selection)


    def on_load_clicked(self):
        from PyQt6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(self, "Selecionar PDFs", "", "PDF Files (*.pdf)")
        if files:
            self.action_triggered.emit("load_pdf", files)

    def on_range_input_changed(self, text):
        indices = set()
        parts = text.split(',')
        for part in parts:
            part = part.strip()
            if not part:
                continue

            if '-' in part:
                subparts = part.split('-')
                if len(subparts) == 2:
                    try:
                        start = int(subparts[0])
                        end = int(subparts[1])
                        r_start = min(start, end)
                        r_end = max(start, end)
                        for i in range(r_start, r_end + 1):
                            indices.add(i - 1)
                    except ValueError:
                        pass
            else:
                try:
                    val = int(part)
                    indices.add(val - 1)
                except ValueError:
                    pass

        self.action_triggered.emit("select_pages", list(indices))

    def update_selection_input(self, selected_indices):
        self.input_selection.blockSignals(True)
        try:
            if not selected_indices:
                self.input_selection.setText("")
                return

            indices = sorted([i + 1 for i in selected_indices])
            ranges = []

            start = indices[0]
            end = start

            for i in range(1, len(indices)):
                if indices[i] == end + 1:
                    end = indices[i]
                else:
                    if start == end:
                        ranges.append(str(start))
                    else:
                        ranges.append(f"{start}-{end}")
                    start = indices[i]
                    end = start

            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")

            self.input_selection.setText(", ".join(ranges))
        finally:
            self.input_selection.blockSignals(False)
