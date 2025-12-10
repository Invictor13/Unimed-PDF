from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QGridLayout, QVBoxLayout, QApplication, QLabel, QHBoxLayout, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt, QMimeData, QPoint
from PyQt6.QtGui import QDrag, QPixmap, QImage
from .widgets.thumbnail import Thumbnail
import os

class FloatingCard(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("border: 1px solid #009A3E; background-color: white; padding: 5px;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hide()

class ContainerWidget(QWidget):
    page_order_changed = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.thumbnails_ref = [] # Reference to thumbnails list in CenterCanvas

    def set_thumbnails(self, thumbnails):
        self.thumbnails_ref = thumbnails

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        try:
            source_index = int(event.mimeData().text())
        except ValueError:
            event.ignore()
            return

        drop_pos = event.position().toPoint()
        container_pos = drop_pos

        target_index = -1
        min_dist = float('inf')

        for thumb in self.thumbnails_ref:
            center = thumb.geometry().center()
            dist = (container_pos - center).manhattanLength()
            if dist < min_dist:
                min_dist = dist
                target_index = thumb.index

        if target_index != -1 and target_index != source_index:
            self.page_order_changed.emit(source_index, target_index)

class EmptyState(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Logo
        logo_label = QLabel()
        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
             pixmap = QPixmap(logo_path)
             if not pixmap.isNull():
                 logo_label.setPixmap(pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(logo_label, 0, Qt.AlignmentFlag.AlignCenter)

        msg_label = QLabel("Aguardando PDF's")
        msg_label.setStyleSheet("font-size: 28px; color: #333333; font-weight: bold;")
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg_label)

        sub_label = QLabel("Clique em 'Carregar' ou arraste arquivos aqui.")
        sub_label.setStyleSheet("font-size: 18px; color: #666666;")
        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub_label)

class CenterCanvas(QWidget):
    page_selected = pyqtSignal(list) # list of selected indices
    page_order_changed = pyqtSignal(int, int) # from_index, to_index
    request_viewer = pyqtSignal(int)

    def __init__(self, main_window):
        super().__init__()
        self.setObjectName("CanvasWidget")
        self.main_window = main_window
        self.layout = None
        self.thumbnails = [] # List of Thumbnail widgets
        self.selected_indices = set()
        self.last_clicked_index = -1
        self.floating_card = FloatingCard()

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Toolbar
        toolbar = QWidget()
        toolbar.setStyleSheet("background-color: #F0F0F0; border-bottom: 1px solid #CCCCCC;")
        toolbar.setFixedHeight(40)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 0, 10, 0)

        # Placeholder for toggles
        # toolbar_layout.addWidget(QLabel("Visualização"))
        toolbar_layout.addStretch()

        main_layout.addWidget(toolbar)

        # Scroll Area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAcceptDrops(True)
        self.scroll_area.setStyleSheet("background-color: #F9F9F9; border: none;")

        self.container = ContainerWidget()
        self.container.setObjectName("CanvasContainer")
        self.container.setStyleSheet("background-color: #F9F9F9;")
        self.container.page_order_changed.connect(self.handle_reorder)

        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid_layout.setContentsMargins(20, 20, 20, 20)

        self.scroll_area.setWidget(self.container)
        main_layout.addWidget(self.scroll_area)

        # Empty State (Initially hidden or shown based on content)
        # We will handle this in refresh_thumbnails.
        # Actually, adding it to layout might be better, but grid layout makes it tricky if mixing.
        # Let's handle it by clearing grid and adding it.

        # Enable drag and drop on the container
        self.container.setAcceptDrops(True)

        self.refresh_thumbnails()

    def handle_reorder(self, src, dst):
        self.page_order_changed.emit(src, dst)
        self.refresh_thumbnails()

    def refresh_thumbnails(self):
        # Clear existing
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
        self.thumbnails = []
        self.selected_indices.clear()

        count = self.main_window.pdf_manager.get_page_count()
        columns = 3

        if count == 0:
            # Show Empty State
            empty_state = EmptyState()
            self.grid_layout.addWidget(empty_state, 0, 0, 1, columns)
            self.container.set_thumbnails([])
            return

        current_file_id = None
        row = 0
        col = 0

        for i in range(count):
            page_info = self.main_window.pdf_manager.get_page_info(i)
            file_id = page_info['file_id']
            file_name = page_info['file_name']

            if file_id != current_file_id:
                if col > 0:
                    row += 1
                    col = 0

                # Header Separator
                header_frame = QFrame()
                header_frame.setStyleSheet("""
                    background-color: transparent;
                    margin-top: 10px;
                """)
                header_layout = QHBoxLayout(header_frame)
                header_layout.setContentsMargins(0, 0, 0, 0)

                header_label = QLabel(f"{file_name}")
                header_label.setStyleSheet("""
                    background-color: white;
                    color: #009A3E;
                    font-weight: bold;
                    padding: 8px 15px;
                    border-left: 5px solid #009A3E;
                    border-radius: 4px;
                    font-size: 14px;
                """)
                header_layout.addWidget(header_label)
                header_layout.addStretch()

                self.grid_layout.addWidget(header_frame, row, 0, 1, columns)
                row += 1
                current_file_id = file_id

            img_data = self.main_window.pdf_manager.get_thumbnail(i)
            thumb = Thumbnail(i, img_data)
            thumb.clicked.connect(self.on_thumbnail_clicked)
            thumb.double_clicked.connect(self.on_thumbnail_double_clicked)
            thumb.hover_entered.connect(self.on_thumbnail_hover)
            thumb.hover_left.connect(self.on_thumbnail_leave)

            self.grid_layout.addWidget(thumb, row, col)
            self.thumbnails.append(thumb)

            col += 1
            if col >= columns:
                col = 0
                row += 1

        self.container.set_thumbnails(self.thumbnails)

    def on_thumbnail_hover(self, index, pos):
        img_data = self.main_window.pdf_manager.get_thumbnail(index, scale=0.8)
        image = QImage.fromData(img_data)
        pixmap = QPixmap.fromImage(image)
        if pixmap.height() > 300:
            pixmap = pixmap.scaledToHeight(300, Qt.TransformationMode.SmoothTransformation)

        self.floating_card.setPixmap(pixmap)
        self.floating_card.move(pos)
        self.floating_card.show()

    def on_thumbnail_leave(self, index):
        self.floating_card.hide()

    def on_thumbnail_clicked(self, index, shift_pressed, ctrl_pressed):
        if shift_pressed and self.last_clicked_index != -1:
            start = min(self.last_clicked_index, index)
            end = max(self.last_clicked_index, index)
            for i in range(start, end + 1):
                self.selected_indices.add(i)
        else:
            if index in self.selected_indices:
                self.selected_indices.remove(index)
            else:
                self.selected_indices.add(index)

            self.request_viewer.emit(index)
            self.last_clicked_index = index

        self.update_visual_selection()
        self.page_selected.emit(list(self.selected_indices))

    def on_thumbnail_double_clicked(self, index):
        self.request_viewer.emit(index)

    def update_visual_selection(self):
        for thumb in self.thumbnails:
            thumb.set_selected(thumb.index in self.selected_indices)

    def get_selected_indices(self):
        return sorted(list(self.selected_indices))

    def clear_selection(self):
        self.selected_indices.clear()
        self.update_visual_selection()
        self.page_selected.emit([])

    def set_selection(self, indices):
        self.selected_indices = set()
        count = self.main_window.pdf_manager.get_page_count()
        for i in indices:
            if 0 <= i < count:
                self.selected_indices.add(i)
        self.update_visual_selection()
