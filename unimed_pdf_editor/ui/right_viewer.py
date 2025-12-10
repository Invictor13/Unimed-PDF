from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QPushButton, QHBoxLayout, QFrame, QSizePolicy
from PyQt6.QtGui import QPixmap, QImage, QIcon
from PyQt6.QtCore import Qt, pyqtSignal
from .styles import COLOR_SECONDARY, COLOR_PRIMARY

class RightViewer(QWidget):
    action_triggered = pyqtSignal(str, object)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.current_page_index = None
        self.init_ui()

    def init_ui(self):
        # Background color update
        self.setStyleSheet(f"background-color: {COLOR_SECONDARY};") # or white

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Removed Top Actions Bar (except navigation if needed, but thumbnails handle nav)
        # Assuming nav buttons are not strictly required if thumbnails are present,
        # or we can put nav in footer?
        # Requirement: "Remover os botões de ação atuais do topo (exceto navegação)."
        # Let's keep a simple header or overlay for navigation if needed, but
        # usually scrolling or clicking thumbnails is enough.
        # Let's verify if "navegação" means "Next/Prev" buttons.
        # If so, I will add them to the footer or a small header.
        # I'll put a small header for navigation info (Page X of Y).

        self.header_nav = QFrame()
        self.header_nav.setFixedHeight(40)
        self.header_nav.setStyleSheet("background-color: white; border-bottom: 1px solid #E0E0E0;")
        nav_layout = QHBoxLayout(self.header_nav)
        nav_layout.setContentsMargins(10, 0, 10, 0)

        self.lbl_page_info = QLabel("Nenhuma página selecionada")
        self.lbl_page_info.setStyleSheet("color: #666666; font-weight: bold;")
        nav_layout.addWidget(self.lbl_page_info)

        main_layout.addWidget(self.header_nav)

        # Image Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setStyleSheet("background-color: #F9F9F9; border: none;")

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.image_label)

        main_layout.addWidget(self.scroll_area)

        # Footer Actions
        self.footer = QFrame()
        self.footer.setFixedHeight(60)
        self.footer.setStyleSheet("background-color: white; border-top: 1px solid #E0E0E0;")
        footer_layout = QHBoxLayout(self.footer)
        footer_layout.setContentsMargins(20, 10, 20, 10)
        footer_layout.setSpacing(20)

        # Download Button
        self.btn_download = QPushButton(" Baixar Página")
        self.btn_download.setIcon(QIcon.fromTheme("document-save")) # Fallback if theme not present
        # Or better, text with unicode arrow if icon not available, but user asked for icons.
        # I will use text with emoji in label for simplicity if assets are missing.
        self.btn_download.setText("⬇️ Baixar Página")
        self.btn_download.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_download.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                color: {COLOR_PRIMARY};
                border: 2px solid {COLOR_PRIMARY};
                border-radius: 5px;
                font-weight: bold;
                padding: 5px 15px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_PRIMARY};
                color: white;
            }}
        """)
        self.btn_download.clicked.connect(lambda: self.action_triggered.emit("download_page", None))
        footer_layout.addWidget(self.btn_download)

        # Delete Button
        self.btn_delete = QPushButton("🗑️ Excluir Página")
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #CC0000;
                border: 2px solid #CC0000;
                border-radius: 5px;
                font-weight: bold;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #CC0000;
                color: white;
            }
        """)
        self.btn_delete.clicked.connect(lambda: self.action_triggered.emit("delete_page", None))
        footer_layout.addWidget(self.btn_delete)

        main_layout.addWidget(self.footer)

        # Initially hide footer if no page?
        self.footer.hide()

    def load_page(self, index):
        self.current_page_index = index
        try:
            # High res image for viewer
            img_data = self.main_window.pdf_manager.get_thumbnail(index, scale=2.0)
            image = QImage.fromData(img_data)
            pixmap = QPixmap.fromImage(image)

            self.image_label.setPixmap(pixmap)

            total = self.main_window.pdf_manager.get_page_count()
            self.lbl_page_info.setText(f"Página {index + 1} de {total}")

            self.footer.show()
        except Exception as e:
            self.image_label.setText(f"Erro ao carregar página: {e}")
            self.footer.hide()

    def clear(self):
        self.image_label.clear()
        self.lbl_page_info.setText("Nenhuma página selecionada")
        self.current_page_index = None
        self.footer.hide()
