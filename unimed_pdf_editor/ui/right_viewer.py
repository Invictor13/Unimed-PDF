from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QHBoxLayout, QFrame
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QImage

class RightViewer(QFrame):
    action_triggered = pyqtSignal(str, object)

    def __init__(self, main_window):
        super().__init__()
        self.setObjectName("RightPanel")
        self.main_window = main_window
        self.current_page_index = -1
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Toolbar
        toolbar = QHBoxLayout()
        btn_prev = QPushButton("<")
        btn_prev.setFixedWidth(40)
        btn_prev.clicked.connect(self.prev_page)

        btn_next = QPushButton(">")
        btn_next.setFixedWidth(40)
        btn_next.clicked.connect(self.next_page)

        self.lbl_page_num = QLabel("Página -")

        toolbar.addWidget(btn_prev)
        toolbar.addWidget(self.lbl_page_num)
        toolbar.addWidget(btn_next)
        toolbar.addStretch()

        btn_rotate = QPushButton("⟳")
        btn_rotate.setFixedWidth(40)
        btn_rotate.setToolTip("Rotacionar 90°")
        btn_rotate.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                background-color: #009A3E;
                color: white;
            }
            QPushButton:hover {
                background-color: #007A30;
            }
        """)
        btn_rotate.clicked.connect(self.rotate_page)
        toolbar.addWidget(btn_rotate)

        btn_delete = QPushButton("🗑")
        btn_delete.setFixedWidth(40)
        btn_delete.setToolTip("Excluir Página")
        btn_delete.setObjectName("DeleteButton")
        # Note: DeleteButton is styled in main STYLESHEET in styles.py
        # But we ensure font size for icon
        btn_delete.setStyleSheet("font-size: 16px;")
        btn_delete.clicked.connect(self.delete_page)
        toolbar.addWidget(btn_delete)

        layout.addLayout(toolbar)

        # Viewer Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.viewer_content = QLabel()
        self.viewer_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.viewer_content)

        layout.addWidget(self.scroll_area)

    def load_page(self, page_index):
        if page_index < 0:
            return

        self.current_page_index = page_index
        count = self.main_window.pdf_manager.get_page_count()
        if page_index >= count:
            return

        self.lbl_page_num.setText(f"Página {page_index + 1} / {count}")

        # Get image from manager
        img_bytes = self.main_window.pdf_manager.get_page_image(page_index)

        image = QImage.fromData(img_bytes)
        pixmap = QPixmap.fromImage(image)

        # Scale if too big for view?
        # For now let scroll area handle it, but maybe fit width
        w = self.scroll_area.width() - 20
        if pixmap.width() > w:
            pixmap = pixmap.scaledToWidth(w, Qt.TransformationMode.SmoothTransformation)

        self.viewer_content.setPixmap(pixmap)

    def prev_page(self):
        if self.current_page_index > 0:
            self.load_page(self.current_page_index - 1)

    def next_page(self):
        count = self.main_window.pdf_manager.get_page_count()
        if self.current_page_index < count - 1:
            self.load_page(self.current_page_index + 1)

    def rotate_page(self):
        if self.current_page_index >= 0:
             self.main_window.pdf_manager.rotate_page(self.current_page_index)
             self.load_page(self.current_page_index)
             self.main_window.center_canvas.refresh_thumbnails()

    def delete_page(self):
        if self.current_page_index >= 0:
            from PyQt6.QtWidgets import QMessageBox
            confirm = QMessageBox.question(self, "Confirmar Exclusão",
                                         f"Tem certeza que deseja excluir a página atual?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.Yes:
                self.main_window.pdf_manager.delete_pages([self.current_page_index])
                self.main_window.center_canvas.refresh_thumbnails()
                self.main_window.center_canvas.clear_selection()

                # Navigate to next or prev or clear
                count = self.main_window.pdf_manager.get_page_count()
                if count > 0:
                    new_index = min(self.current_page_index, count - 1)
                    self.load_page(new_index)
                else:
                    self.current_page_index = -1
                    self.viewer_content.clear()
                    self.lbl_page_num.setText("Página -")
