from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QPushButton, QHBoxLayout, QFrame
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, pyqtSignal
from .styles import COLOR_PRIMARY

class RightViewer(QWidget):
    action_triggered = pyqtSignal(str, object)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.current_page_index = None
        self.setObjectName("RightViewer") # Used for white background in styles.py
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Image Area (Scroll Area) - No top toolbar actions
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setStyleSheet("background-color: white; border: none;")

        self.image_label = QLabel("Clique em uma página para prévia")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("font-size: 18px; color: #999999; font-weight: bold;")
        self.scroll_area.setWidget(self.image_label)

        main_layout.addWidget(self.scroll_area)

        # 2. Footer Actions (Rodapé)
        self.footer = QFrame()
        self.footer.setFixedHeight(60)
        self.footer.setStyleSheet("background-color: #F0F0F0; border-top: 1px solid #CCCCCC;")
        footer_layout = QHBoxLayout(self.footer)
        footer_layout.setContentsMargins(20, 10, 20, 10)
        footer_layout.setSpacing(15)

        # Page Info
        self.lbl_page_info = QLabel("Nenhuma página selecionada")
        self.lbl_page_info.setStyleSheet("font-weight: bold; color: #333333;")
        footer_layout.addWidget(self.lbl_page_info)

        # Navigation Buttons (Setas para navegação rápida)
        btn_prev = self.create_nav_button("◀️", "Página Anterior", self.prev_page)
        btn_next = self.create_nav_button("▶️", "Próxima Página", self.next_page)

        footer_layout.addWidget(btn_prev)
        footer_layout.addWidget(btn_next)

        footer_layout.addStretch()

        # Download Button (Individual PDF)
        self.btn_download_pdf = self.create_action_button("⬇️ PDF", "Baixar Página como PDF", lambda: self.action_triggered.emit("download_page", "pdf"))
        self.btn_download_pdf.setStyleSheet(self.btn_download_pdf.styleSheet().replace("min-width: 100px", "min-width: 80px"))
        footer_layout.addWidget(self.btn_download_pdf)

        # Download Button (Individual Image)
        self.btn_download_img = self.create_action_button("🖼️ PNG", "Baixar Página como Imagem PNG", lambda: self.action_triggered.emit("download_page", "png"))
        self.btn_download_img.setStyleSheet(self.btn_download_img.styleSheet().replace("min-width: 100px", "min-width: 80px"))
        footer_layout.addWidget(self.btn_download_img)

        # Delete Button (Individual)
        self.btn_delete = self.create_action_button("🗑️ Excluir", "Excluir Página Atual", lambda: self.action_triggered.emit("delete_page", None))
        self.btn_delete.setObjectName("DeleteButton") # Usa o estilo de alerta global
        self.btn_delete.setStyleSheet(self.btn_delete.styleSheet().replace("min-width: 100px", "min-width: 80px"))
        footer_layout.addWidget(self.btn_delete)

        main_layout.addWidget(self.footer)

        # Initially hide footer
        self.footer.hide()

    def create_nav_button(self, icon_text, tooltip, slot):
        # Botões de navegação menores e mais discretos
        btn = QPushButton(icon_text)
        btn.setFixedSize(40, 30)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # CORRIGIDO: Cor do texto (ícone) para Verde Unimed
        btn.setStyleSheet(f"font-size: 16px; padding: 0px; box-shadow: none; margin: 0px; background-color: #E0E0E0; color: {COLOR_PRIMARY}; border: 1px solid #CCCCCC;")
        btn.clicked.connect(slot)
        return btn

    def create_action_button(self, text, tooltip, slot):
        # Usando o estilo global de QPushButton
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(slot)
        return btn

    def load_page(self, index):
        self.current_page_index = index
        try:
            # High res image for viewer (usando a função otimizada)
            img_data = self.main_window.pdf_manager.get_page_image(index, scale=2.0)
            image = QImage.fromData(img_data)
            pixmap = QPixmap.fromImage(image)

            # Escala dinâmica
            w = self.scroll_area.width() - 40
            if pixmap.width() > w:
                pixmap = pixmap.scaledToWidth(w, Qt.TransformationMode.SmoothTransformation)

            self.image_label.setPixmap(pixmap)
            self.image_label.adjustSize()

            total = self.main_window.pdf_manager.get_page_count()
            self.lbl_page_info.setText(f"Página {index + 1} de {total}")

            self.footer.show()
        except Exception as e:
            self.image_label.setText(f"Erro ao carregar página: {e}")
            self.image_label.setStyleSheet("font-size: 14px; color: red;")
            self.footer.hide()

    def clear(self):
        # RE-APLICA MENSAGEM DE EMPTY STATE
        self.image_label.setText("Clique em uma página para prévia")
        self.image_label.setStyleSheet("font-size: 18px; color: #999999; font-weight: bold;")

        self.lbl_page_info.setText("Nenhuma página selecionada")
        self.current_page_index = None
        self.footer.hide()

    def prev_page(self):
        if self.current_page_index is not None and self.current_page_index > 0:
            self.load_page(self.current_page_index - 1)

    def next_page(self):
        total = self.main_window.pdf_manager.get_page_count()
        if self.current_page_index is not None and self.current_page_index < total - 1:
            self.load_page(self.current_page_index + 1)
