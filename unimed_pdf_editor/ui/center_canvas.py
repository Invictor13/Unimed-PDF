from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QGridLayout, QVBoxLayout, QApplication, QLabel, QHBoxLayout, QFrame, QPushButton
)
from PyQt6.QtCore import pyqtSignal, Qt, QMimeData, QPoint, QTimer
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

class DocumentCard(QFrame):
    """
    Widget representing a single document (file) in 'View Documents' mode.
    Draggable to reorder files.
    """
    def __init__(self, file_info, index, parent=None):
        super().__init__(parent)
        self.file_info = file_info
        self.index = index
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #DDDDDD;
                border-radius: 6px;
                padding: 10px;
                margin-bottom: 5px;
            }
            QFrame:hover {
                border: 1px solid #009A3E;
                background-color: #F0FFF4;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)

        # Icon
        icon_label = QLabel("📄") # Or use a proper icon
        icon_label.setStyleSheet("font-size: 24px; border: none; background: transparent;")
        layout.addWidget(icon_label)

        # Info
        info_layout = QVBoxLayout()
        name_label = QLabel(file_info['file_name'])
        name_label.setStyleSheet("font-weight: bold; font-size: 14px; border: none; background: transparent; color: #333333;")
        info_layout.addWidget(name_label)

        count_label = QLabel(f"{file_info['page_count']} Páginas")
        count_label.setStyleSheet("color: #666666; font-size: 12px; border: none; background: transparent;")
        info_layout.addWidget(count_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        # Drag Handle Icon
        drag_handle = QLabel("☰")
        drag_handle.setStyleSheet("color: #999999; font-size: 20px; border: none; background: transparent;")
        layout.addWidget(drag_handle)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(str(self.index))
            mime.setData("application/x-unimed-doc-index", str(self.index).encode())
            drag.setMimeData(mime)

            # Create visual representation for drag
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.position().toPoint())

            drag.exec(Qt.DropAction.MoveAction)

class ContainerWidget(QWidget):
    page_order_changed = pyqtSignal(int, int)      # For Page View
    doc_order_changed = pyqtSignal(str, int)       # For Doc View: file_id, new_index

    def __init__(self, mode='pages', parent=None):
        super().__init__(parent)
        self.mode = mode
        self.thumbnails_ref = [] # Reference to thumbnails list
        self.docs_ref = []       # Reference to doc cards list

    def set_thumbnails(self, thumbnails):
        self.thumbnails_ref = thumbnails

    def set_docs(self, docs):
        self.docs_ref = docs

    def dragEnterEvent(self, event):
        if self.mode == 'pages':
            if event.mimeData().hasText() and not event.mimeData().hasFormat("application/x-unimed-doc-index"):
                event.accept()
            else:
                event.ignore()
        elif self.mode == 'docs':
            if event.mimeData().hasFormat("application/x-unimed-doc-index"):
                event.accept()
            else:
                event.ignore()

    def dropEvent(self, event):
        if self.mode == 'pages':
            self.handle_page_drop(event)
        elif self.mode == 'docs':
            self.handle_doc_drop(event)

    def handle_page_drop(self, event):
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

    def handle_doc_drop(self, event):
        try:
            source_idx_str = event.mimeData().data("application/x-unimed-doc-index").data().decode()
            source_index = int(source_idx_str)
        except (ValueError, AttributeError):
            event.ignore()
            return

        drop_pos = event.position().toPoint()

        target_index = -1

        # Simple vertical list hit testing
        # We check which card we are over
        for i, doc_card in enumerate(self.docs_ref):
            geo = doc_card.geometry()
            if geo.contains(drop_pos):
                target_index = i
                break

        # If dropped below all, assume last
        if target_index == -1:
            if drop_pos.y() > self.docs_ref[-1].geometry().bottom():
                target_index = len(self.docs_ref) - 1
            else:
                 # Check if above first
                 if drop_pos.y() < self.docs_ref[0].geometry().top():
                     target_index = 0

        if target_index != -1 and target_index != source_index:
            file_id = self.docs_ref[source_index].file_info['file_id']
            self.doc_order_changed.emit(file_id, target_index)

# CLASSE DE ESTADO VAZIO SIMPLIFICADA (ESTÁVEL)
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

        sub_label = QLabel("Clique em 'Carregar' ou arraste arquivos aqui.\n(Pode arrastar as miniaturas para reordenar)")
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
        self.view_mode = 'pages' # 'pages' or 'docs'

        self.thumbnails = [] # List of Thumbnail widgets
        self.doc_cards = []  # List of DocumentCard widgets
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
        toolbar.setFixedHeight(50)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)

        # View Toggles
        self.btn_view_pages = QPushButton("Ver Páginas")
        self.btn_view_pages.setCheckable(True)
        self.btn_view_pages.setChecked(True)
        self.btn_view_pages.clicked.connect(lambda: self.set_view_mode('pages'))
        self.style_toggle_button(self.btn_view_pages)

        self.btn_view_docs = QPushButton("Ver Documentos")
        self.btn_view_docs.setCheckable(True)
        self.btn_view_docs.clicked.connect(lambda: self.set_view_mode('docs'))
        self.style_toggle_button(self.btn_view_docs)

        toolbar_layout.addWidget(self.btn_view_pages)
        toolbar_layout.addWidget(self.btn_view_docs)
        toolbar_layout.addStretch()

        main_layout.addWidget(toolbar)

        # Scroll Area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAcceptDrops(True)
        self.scroll_area.setStyleSheet("background-color: #F9F9F9; border: none;")

        self.container = ContainerWidget(mode=self.view_mode)
        self.container.setObjectName("CanvasContainer")
        self.container.setStyleSheet("background-color: #F9F9F9;")
        self.container.page_order_changed.connect(self.handle_reorder)
        self.container.doc_order_changed.connect(self.handle_doc_reorder)

        # We switch layouts based on mode
        self.grid_layout = QGridLayout(self.container) # Used for Pages
        self.v_layout = QVBoxLayout() # Used for Docs (we will set it to container when mode changes)

        # Default layout
        self.container.setLayout(self.grid_layout)

        self.scroll_area.setWidget(self.container)
        main_layout.addWidget(self.scroll_area)

        # Enable drag and drop on the container
        self.container.setAcceptDrops(True)

        self.refresh_thumbnails()

    def style_toggle_button(self, btn):
        btn.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                border: 1px solid #CCCCCC;
                padding: 5px 15px;
                border-radius: 4px;
                color: #333333;
            }
            QPushButton:checked {
                background-color: #009A3E;
                color: white;
                border: 1px solid #007A30;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
            QPushButton:checked:hover {
                background-color: #007A30;
            }
        """)

    def _clear_layout(self, layout):
        """Recursively clears a layout."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget() is not None:
                    item.widget().deleteLater()
                elif item.layout() is not None:
                    self._clear_layout(item.layout())

    def set_view_mode(self, mode):
        if self.view_mode == mode:
            return

        self.view_mode = mode
        self.btn_view_pages.setChecked(mode == 'pages')
        self.btn_view_docs.setChecked(mode == 'docs')

        self.container.mode = mode

        # --- CORREÇÃO CRÍTICA DE LAYOUT ---
        old_layout = self.container.layout()

        # 1. Limpa os widgets internos e DESANEXA o layout antigo de forma robusta.
        if old_layout:
             self._clear_layout(old_layout)
             self.container.setLayout(None) # O comando mágico para o PyQt6!

        # 2. Anexar o NOVO layout.
        if mode == 'pages':
            self.grid_layout = QGridLayout(self.container)
            self.grid_layout.setSpacing(20)
            self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            self.grid_layout.setContentsMargins(20, 20, 20, 20)
        else:
            self.v_layout = QVBoxLayout(self.container)
            self.v_layout.setSpacing(10)
            self.v_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.v_layout.setContentsMargins(20, 20, 20, 20)

        self.refresh_thumbnails()

    def handle_reorder(self, src, dst):
        self.page_order_changed.emit(src, dst)
        self.refresh_thumbnails()

    def handle_doc_reorder(self, file_id, new_index):
        # Call PDF Manager to reorder
        self.main_window.pdf_manager.reorder_file(file_id, new_index)
        self.refresh_thumbnails()

    def refresh_thumbnails(self):
        # Clear existing items
        layout = self.container.layout()
        if layout:
            self._clear_layout(layout)

        self.thumbnails = []
        self.doc_cards = []
        self.selected_indices.clear()

        count = self.main_window.pdf_manager.get_page_count()

        if count == 0:
            # Show Empty State
            empty_state = EmptyState()
            layout.addWidget(empty_state)
            if self.view_mode == 'pages':
                # Center in grid
                pass
            self.container.set_thumbnails([])
            self.container.set_docs([])
            return

        if self.view_mode == 'pages':
            self._render_pages_view(count, layout)
        else:
            self._render_docs_view(layout)

    def _render_pages_view(self, count, layout):
        columns = 3
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
                header_frame.setStyleSheet("background-color: transparent; margin-top: 10px;")
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

                layout.addWidget(header_frame, row, 0, 1, columns)
                row += 1
                current_file_id = file_id

            img_data = self.main_window.pdf_manager.get_thumbnail(i)
            thumb = Thumbnail(i, img_data)
            thumb.clicked.connect(self.on_thumbnail_clicked)
            thumb.double_clicked.connect(self.on_thumbnail_double_clicked)
            thumb.hover_entered.connect(self.on_thumbnail_hover)
            thumb.hover_left.connect(self.on_thumbnail_leave)

            layout.addWidget(thumb, row, col)
            self.thumbnails.append(thumb)

            col += 1
            if col >= columns:
                col = 0
                row += 1

        self.container.set_thumbnails(self.thumbnails)

    def _render_docs_view(self, layout):
        files = self.main_window.pdf_manager.get_files_in_order()

        for i, file_info in enumerate(files):
            card = DocumentCard(file_info, i)
            layout.addWidget(card)
            self.doc_cards.append(card)

        layout.addStretch() # Push items to top
        self.container.set_docs(self.doc_cards)

    def on_thumbnail_hover(self, index, pos):
        if self.view_mode != 'pages': return

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
