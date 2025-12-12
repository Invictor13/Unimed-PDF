from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QGridLayout, QVBoxLayout, QApplication, QLabel, QHBoxLayout, QFrame, QPushButton
)
from PyQt6.QtCore import pyqtSignal, Qt, QMimeData, QPoint, QTimer, QRect
from PyQt6.QtGui import QDrag, QPixmap, QImage, QPainter, QPen, QBrush, QColor
from .widgets.thumbnail import Thumbnail
import os

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
    files_dropped = pyqtSignal(list)               # New signal for file drops
    lasso_started = pyqtSignal()
    lasso_moved = pyqtSignal(QRect)
    lasso_ended = pyqtSignal()

    def __init__(self, mode='pages', parent=None):
        super().__init__(parent)
        self.mode = mode
        self.thumbnails_ref = [] # Reference to thumbnails list
        self.docs_ref = []       # Reference to doc cards list
        self.selection_active = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.lasso_rect = QRect()
        self.drop_indicator_rect = QRect()

    def mousePressEvent(self, event):
        if self.mode == 'pages' and event.button() == Qt.MouseButton.LeftButton:
            self.selection_active = True
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.lasso_rect = QRect()
            self.update()
            self.lasso_started.emit()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.selection_active:
            self.end_point = event.pos()
            self.lasso_rect = QRect(self.start_point, self.end_point).normalized()
            self.update()
            self.lasso_moved.emit(self.lasso_rect)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.selection_active:
            self.selection_active = False
            self.lasso_rect = QRect()
            self.update()
            self.lasso_ended.emit()
        else:
            super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)

        if self.selection_active and not self.lasso_rect.isNull():
            painter.setPen(QPen(QColor(0, 154, 62), 2))
            painter.setBrush(QBrush(QColor(0, 154, 62, 50)))
            painter.drawRect(self.lasso_rect)

        if not self.drop_indicator_rect.isNull():
            painter.setPen(QPen(QColor(0, 154, 62), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawLine(self.drop_indicator_rect.topLeft(), self.drop_indicator_rect.bottomLeft())

    def set_thumbnails(self, thumbnails):
        self.thumbnails_ref = thumbnails

    def set_docs(self, docs):
        self.docs_ref = docs

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            return

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

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            return

        if self.mode == 'pages':
            if event.mimeData().hasText() and not event.mimeData().hasFormat("application/x-unimed-doc-index"):
                try:
                    source_index = int(event.mimeData().text())
                except ValueError:
                    source_index = -1

                _, self.drop_indicator_rect = self._calculate_drop_target(event.position().toPoint(), source_index)
                self.update()
                event.accept()
            else:
                event.ignore()
        elif self.mode == 'docs':
             if event.mimeData().hasFormat("application/x-unimed-doc-index"):
                self.drop_indicator_rect = QRect() # Clear for docs for now
                self.update()
                event.accept()
             else:
                event.ignore()

    def dragLeaveEvent(self, event):
        self.drop_indicator_rect = QRect()
        self.update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self.drop_indicator_rect = QRect()
        self.update()

        if event.mimeData().hasUrls():
            self.handle_file_drop(event)
        elif self.mode == 'pages':
            self.handle_page_drop(event)
        elif self.mode == 'docs':
            self.handle_doc_drop(event)

    def _calculate_drop_target(self, pos, source_index=-1):
        if not self.thumbnails_ref:
            return -1, QRect()

        closest_thumb = None
        min_dist = float('inf')

        for thumb in self.thumbnails_ref:
            center = thumb.geometry().center()
            dist = (pos - center).manhattanLength()
            if dist < min_dist:
                min_dist = dist
                closest_thumb = thumb

        if closest_thumb:
            if closest_thumb.index == source_index:
                 return source_index, QRect() # No visual feedback if over self

            geo = closest_thumb.geometry()
            insert_after = pos.x() > geo.center().x()

            if insert_after:
                target_index = closest_thumb.index + 1
                indicator_rect = QRect(geo.right(), geo.top(), 2, geo.height())
            else:
                target_index = closest_thumb.index
                indicator_rect = QRect(geo.left() - 2, geo.top(), 2, geo.height())

            return target_index, indicator_rect

        return -1, QRect()

    def handle_file_drop(self, event):
        files = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = url.toLocalFile()
                if path.lower().endswith('.pdf'):
                    files.append(path)

        if files:
            self.files_dropped.emit(files)

    def handle_page_drop(self, event):
        try:
            source_index = int(event.mimeData().text())
        except ValueError:
            event.ignore()
            return

        drop_pos = event.position().toPoint()
        target_index, _ = self._calculate_drop_target(drop_pos, source_index)

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
        self.container.files_dropped.connect(self.main_window.load_pdf)
        self.container.lasso_started.connect(self.on_lasso_started)
        self.container.lasso_moved.connect(self.on_lasso_moved)
        self.container.lasso_ended.connect(self.on_lasso_ended)

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
        # Fixed layout bug: Ensure old layout is cleared and detached.
        old_layout = self.container.layout()

        # 1. Limpa os widgets internos e DESANEXA o layout antigo de forma robusta.
        if old_layout:
             self._clear_layout(old_layout)
             # FIX CIRÚRGICO FINAL: Usar o hack de transferir o layout para um QWidget temporário
             # para evitar o erro/warning de QWidget::setLayout: Cannot set layout to 0.
             QWidget().setLayout(old_layout)

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
        columns = 4
        row = 0
        col = 0

        for i in range(count):
            img_data = self.main_window.pdf_manager.get_thumbnail(i)
            thumb = Thumbnail(i, img_data)
            thumb.clicked.connect(self.on_thumbnail_clicked)
            thumb.double_clicked.connect(self.on_thumbnail_double_clicked)

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

    def on_lasso_started(self):
        modifiers = QApplication.keyboardModifiers()
        if modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            self.selection_snapshot = self.selected_indices.copy()
        else:
            self.selection_snapshot = set()
            self.selected_indices.clear()
            self.update_visual_selection()

    def on_lasso_moved(self, rect):
        self.update_lasso_selection(rect)

    def on_lasso_ended(self):
        if hasattr(self, 'selection_snapshot'):
            del self.selection_snapshot
        self.page_selected.emit(list(self.selected_indices))

    def update_lasso_selection(self, rect):
        modifiers = QApplication.keyboardModifiers()
        # Find indices in rect
        in_rect_indices = set()

        # Refined Lasso Selection Logic: Check intersection with thumbnail geometry
        for thumb in self.thumbnails:
            # Ensure we are checking against the correct coordinate system (ContainerWidget)
            thumb_rect = thumb.geometry()
            if rect.intersects(thumb_rect):
                in_rect_indices.add(thumb.index)

        # Combine with snapshot
        if modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            if not hasattr(self, 'selection_snapshot'):
                self.selection_snapshot = self.selected_indices.copy()

            # Logic: Union (Add to selection)
            self.selected_indices = self.selection_snapshot | in_rect_indices
        else:
            self.selected_indices = in_rect_indices

        self.update_visual_selection()

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
