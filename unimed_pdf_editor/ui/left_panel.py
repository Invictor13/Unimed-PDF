from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QGroupBox, QFileDialog, QFrame, QMessageBox, QInputDialog
)
from PyQt6.QtCore import pyqtSignal, Qt
from .styles import BUTTON_STYLE, COLOR_TEXT_LIGHT, COLOR_PRIMARY # Importar cores

class LeftPanel(QFrame):
    action_triggered = pyqtSignal(str, object)

    def __init__(self, main_window):
        super().__init__(main_window)
        self.setObjectName("LeftPanel") # Used for dark background in styles.py
        self.init_ui()

    def create_button(self, icon, tooltip, action_name, data=None, connect_default=True):
        btn = QPushButton(icon)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # SOLUÇÃO DE CONTRASTE: Mantém font-size: 20px; confiando no estilo global para a cor (branca).
        btn.setStyleSheet("font-size: 20px;")

        if connect_default:
            btn.clicked.connect(lambda: self.action_triggered.emit(action_name, data))
        return btn

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 10, 15, 10)

        # Corrigindo o texto do GroupBox no Dark Theme
        group_style = f"QGroupBox {{ color: {COLOR_TEXT_LIGHT}; border: 1px solid #444444; margin-top: 10px; }} QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 3px; }}"

        # File Operations
        # Corrigido para usar connect_default=False para controle de conexão local
        self.btn_load = self.create_button("⬆️", "Carregar PDFs", "load_pdf", connect_default=False)
        self.btn_load.clicked.connect(self.on_load_clicked)
        layout.addWidget(self.btn_load)

        # Actions
        self.btn_merge = self.create_button("➕", "Unificar PDFs", "merge")
        layout.addWidget(self.btn_merge)

        self.btn_split = self.create_button("✂️", "Separar Páginas Selecionadas", "split")
        layout.addWidget(self.btn_split)

        self.btn_ocr = self.create_button("🔍", "Executar OCR (Texto Pesquisável)", "ocr")
        layout.addWidget(self.btn_ocr)

        # Compression Group
        group_compress = QGroupBox("Compactação")
        group_compress.setStyleSheet(group_style)
        layout_compress = QVBoxLayout(group_compress)

        # Ícones de compactação corrigidos
        self.btn_compress_low = self.create_button("⬇️", "Compactação Baixa (Estrutura)", "compress", "low")
        layout_compress.addWidget(self.btn_compress_low)

        self.btn_compress_high = self.create_button("📉", "Compactação Alta (Otimizar Imagens)", "compress", "high")
        layout_compress.addWidget(self.btn_compress_high)
        layout.addWidget(group_compress)

        # Selection Input
        layout.addStretch()
        label_selecao = QLabel("Seleção Manual:")
        label_selecao.setStyleSheet(f"color: {COLOR_TEXT_LIGHT}; margin-top: 15px;")
        layout.addWidget(label_selecao)

        self.input_selection = QLineEdit()
        self.input_selection.setPlaceholderText("Ex: 1, 3-5")
        self.input_selection.textChanged.connect(self.on_range_input_changed)
        layout.addWidget(self.input_selection)

        # QoL and Deletion
        self.btn_rotate = self.create_button("🔄", "Rotacionar Páginas Selecionadas (90°)", "rotate_selected")
        layout.addWidget(self.btn_rotate)

        self.btn_clear = self.create_button("🧹", "Limpar Sessão", "clear_session")
        # Estilo neutro corrigido (Dark Gray)
        self.btn_clear.setStyleSheet(f"QPushButton {{ background-color: #444444; color: white; }} QPushButton:hover {{ background-color: #333333; }}")
        layout.addWidget(self.btn_clear)

        self.btn_delete = self.create_button("❌", "Excluir Seleção", "delete")
        self.btn_delete.setObjectName("DeleteButton")
        layout.addWidget(self.btn_delete)

    # (Mantenha as funções lógicas de manipulação de seleção)
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
        from PyQt6.QtCore import QCoreApplication

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
