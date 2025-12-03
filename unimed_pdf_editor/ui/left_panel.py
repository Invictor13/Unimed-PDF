from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QFileDialog, QFrame, QMessageBox, QInputDialog
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import pyqtSignal, Qt
import os

class LeftPanel(QFrame):
    action_triggered = pyqtSignal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LeftPanel")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title / Branding
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Load logo
        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
             pixmap = QPixmap(logo_path)
             if not pixmap.isNull():
                 # Scale if necessary, but assuming logo is sized appropriate or we limit it
                 logo_label.setPixmap(pixmap.scaled(200, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        # Fallback if no logo? Or just empty.
        layout.addWidget(logo_label)
        layout.addSpacing(20)

        # File Operations
        btn_load = QPushButton("Carregar PDF(s)")
        btn_load.clicked.connect(self.on_load_clicked)
        layout.addWidget(btn_load)

        # Range Input
        layout.addWidget(QLabel("Seleção (ex: 1-5, 8)"))
        self.range_input = QLineEdit()
        self.range_input.setPlaceholderText("Selecione páginas...")
        self.range_input.textChanged.connect(self.on_range_input_changed)
        layout.addWidget(self.range_input)

        # Action Buttons
        btn_merge = QPushButton("Unificar PDFs")
        btn_merge.clicked.connect(lambda: self.action_triggered.emit("merge", None))
        layout.addWidget(btn_merge)

        btn_split = QPushButton("Separar PDF")
        btn_split.clicked.connect(lambda: self.action_triggered.emit("split", None))
        layout.addWidget(btn_split)

        btn_compress = QPushButton("Compactar PDF")
        btn_compress.clicked.connect(self.on_compress_clicked)
        layout.addWidget(btn_compress)

        btn_ocr = QPushButton("Tornar Pesquisável (OCR)")
        btn_ocr.clicked.connect(lambda: self.action_triggered.emit("ocr", None))
        layout.addWidget(btn_ocr)

        layout.addStretch()

        btn_delete = QPushButton("Excluir Páginas")
        btn_delete.setObjectName("DeleteButton")
        btn_delete.clicked.connect(lambda: self.action_triggered.emit("delete", None))
        layout.addWidget(btn_delete)

    def on_load_clicked(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Selecionar PDFs", "", "PDF Files (*.pdf)")
        if files:
            self.action_triggered.emit("load_pdf", files)

    def on_compress_clicked(self):
        levels = ["Baixa", "Média", "Alta"]
        item, ok = QInputDialog.getItem(self, "Compactar PDF", "Selecione o nível:", levels, 1, False)
        if ok and item:
            level_map = {"Baixa": "low", "Média": "medium", "Alta": "high"}
            self.action_triggered.emit("compress", level_map[item])

    def update_selection_input(self, indices):
        # Convert 0-based indices to 1-based string representation
        self.range_input.blockSignals(True)
        try:
            if not indices:
                self.range_input.setText("")
                return

            indices = sorted([i + 1 for i in indices])
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

            self.range_input.setText(", ".join(ranges))
        finally:
            self.range_input.blockSignals(False)


    def on_range_input_changed(self, text):
        # Parse range like "1-5, 8"
        indices = set()
        parts = text.split(',')
        for part in parts:
            part = part.strip()
            if not part:
                continue

            if '-' in part:
                # Range
                subparts = part.split('-')
                if len(subparts) == 2:
                    try:
                        start = int(subparts[0])
                        end = int(subparts[1])
                        # Handle reverse range or just min-max
                        r_start = min(start, end)
                        r_end = max(start, end)
                        for i in range(r_start, r_end + 1):
                            indices.add(i - 1) # Convert 1-based to 0-based
                    except ValueError:
                        pass
            else:
                # Single number
                try:
                    val = int(part)
                    indices.add(val - 1)
                except ValueError:
                    pass

        # Emit signal to update canvas selection
        # We need a new signal or reuse existing mechanism.
        # LeftPanel doesn't have direct access to Canvas.
        # We should emit a signal that MainWindow catches.
        self.action_triggered.emit("select_pages", list(indices))
