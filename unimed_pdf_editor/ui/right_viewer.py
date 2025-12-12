
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QPushButton, QHBoxLayout, QFrame
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, pyqtSignal
from .styles import COLOR_PRIMARY, COLOR_TEXT

class RightViewer(QWidget):
    action_triggered = pyqtSignal(str, object)

    def __init__(self, main_window):
        # Refactored for Task 4
        super().__init__()
        self.main_window = main_window
        self.current_page_index = None
        self.zoom_level = 1.0  # Initial zoom level (scale)
        self.setObjectName("RightViewer") # Used for white background in styles.py
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Título da Frame (Topo - MANTIDO NA CLASSE MAIN_WINDOW)
        # O título será injetado pelo create_pane_with_title

        # 1. Image Area (Scroll Area)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setStyleSheet("background-color: white; border: none;")

        # Empty State Label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.image_label)

        main_layout.addWidget(self.scroll_area)

        # 2. Footer Actions (Rodapé)
        self.footer = QFrame()
        self.footer.setFixedHeight(60)
        # Garantindo fundo claro e borda visível
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

        # Zoom Controls
        footer_layout.addSpacing(10)
        btn_zoom_out = self.create_nav_button("-", "Diminuir Zoom", self.zoom_out)
        btn_zoom_in = self.create_nav_button("+", "Aumentar Zoom", self.zoom_in)

        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setFixedWidth(50)
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_zoom.setStyleSheet("color: #333333; font-weight: bold;")

        footer_layout.addWidget(btn_zoom_out)
        footer_layout.addWidget(self.lbl_zoom)
        footer_layout.addWidget(btn_zoom_in)

        footer_layout.addStretch()

        # Rotation Button (NOVO)
        # Integrated rotation functionality
        self.btn_rotate = self.create_action_button("🔄 Rotacionar", "Rotacionar Página Atual (90°)", lambda: self.action_triggered.emit("rotate_page", None))
        footer_layout.addWidget(self.btn_rotate)

        # Download Button (Individual PDF)
        self.btn_download_pdf = self.create_action_button("⬇️ PDF", "Baixar Página como PDF", lambda: self.action_triggered.emit("download_page", "pdf"))
        footer_layout.addWidget(self.btn_download_pdf)

        # Download Button (Individual Image)
        self.btn_download_img = self.create_action_button("🖼️ PNG", "Baixar Página como Imagem PNG", lambda: self.action_triggered.emit("download_page", "png"))
        footer_layout.addWidget(self.btn_download_img)

        # Delete Button (Individual)
        self.btn_delete = self.create_action_button("🗑️ Excluir", "Excluir Página Atual", lambda: self.action_triggered.emit("delete_page", None))
        self.btn_delete.setObjectName("DeleteButton") # Usa o estilo de alerta global
        footer_layout.addWidget(self.btn_delete)

        main_layout.addWidget(self.footer)

        # Inicialização do estado
        self.clear()
        self.update_zoom_label()

    def create_nav_button(self, icon_text, tooltip, slot):
        btn = QPushButton(icon_text)
        btn.setFixedSize(40, 30)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # CORRIGIDO: Cor do texto (ícone) para Verde Unimed (#009A3E)
        # Uso de estilo explícito para garantir contraste contra o fundo cinza
        btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 16px;
                padding: 0px;
                background-color: #E0E0E0;
                color: {COLOR_PRIMARY};
                border: 1px solid #CCCCCC;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: #D0D0D0;
            }}
        """)
        btn.clicked.connect(slot)
        return btn

    def create_action_button(self, text, tooltip, slot):
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(slot)
        # TASK 1.1: Forçar cor do texto para PRETO para contraste no rodapé cinza.
        btn.setStyleSheet(f"color: {COLOR_TEXT};")
        return btn

    def load_page(self, index):
        self.current_page_index = index
        try:
            # High res image for viewer (usando a função otimizada e zoom dinâmico)
            img_data = self.main_window.pdf_manager.get_page_image(index, scale=self.zoom_level)
            image = QImage.fromData(img_data)
            pixmap = QPixmap.fromImage(image)

            # Escala dinâmica
            # Se a imagem for maior que a área visível, o QScrollArea cuida do scroll.
            # Não forçamos mais o scaledToWidth para respeitar o zoom, a menos que seja muito grande inicialmente?
            # Com zoom manual, o usuário controla o tamanho.

            # No entanto, se o zoom é padrão (2.0), pode ser muito grande.
            # Vamos respeitar o zoom definido.

            self.image_label.setPixmap(pixmap)
            self.image_label.adjustSize()

            total = self.main_window.pdf_manager.get_page_count()
            self.lbl_page_info.setText(f"Página {index + 1} de {total}")

            self.footer.show()
        except Exception as e:
            self.image_label.setText(f"Erro ao carregar página: {e}")
            self.image_label.setStyleSheet("font-size: 14px; color: red; font-weight: normal;")
            self.footer.hide()

    def clear(self):
        # Implementação do Empty State
        self.image_label.clear()
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

    def zoom_in(self):
        if self.zoom_level < 5.0:
            self.zoom_level += 0.5
            self.update_zoom_label()
            if self.current_page_index is not None:
                self.load_page(self.current_page_index)

    def zoom_out(self):
        if self.zoom_level > 0.5:
            self.zoom_level -= 0.5
            self.update_zoom_label()
            if self.current_page_index is not None:
                self.load_page(self.current_page_index)

    def update_zoom_label(self):
        # 2.0 scale is roughly "Standard" but let's map 2.0 to 100% relative to our quality baseline,
        # or just show raw scale factor?
        # Usually user expects 100%.
        # If scale=1.0 is 72 DPI, scale=2.0 is 144 DPI (Retina/High Quality).
        # Let's say 2.0 is 100% visual quality.
        percentage = int(self.zoom_level * 100)
        self.lbl_zoom.setText(f"{percentage}%")
