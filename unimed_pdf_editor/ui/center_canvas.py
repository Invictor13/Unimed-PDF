from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QGridLayout, QVBoxLayout, QApplication, QLabel
)
from PyQt6.QtCore import pyqtSignal, Qt, QMimeData, QPoint
from PyQt6.QtGui import QDrag, QPixmap, QImage
from .widgets.thumbnail import Thumbnail

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

        # container_pos is drop_pos since we are in the container
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
        # We use a ScrollArea containing a widget with GridLayout
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAcceptDrops(True)

        self.container = ContainerWidget() # Use custom container
        self.container.setObjectName("CanvasContainer")
        self.container.page_order_changed.connect(self.handle_reorder)

        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.scroll_area.setWidget(self.container)

        # Main layout for this widget (CenterCanvas)
        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll_area)

        # Enable drag and drop on the container
        self.container.setAcceptDrops(True)

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
        columns = 3 # Adjust based on width? Or fixed for now.

        if count == 0:
            # Empty State with Branding
            empty_widget = QWidget()
            empty_layout = QVBoxLayout(empty_widget)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Logo (Optional, or just text)
            # If we had a logo asset, we'd use it. For now, styled text.
            logo_label = QLabel("Unimed")
            logo_label.setStyleSheet("font-size: 48px; font-weight: bold; color: #009A3E; margin-bottom: 20px;")
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(logo_label)

            msg_label = QLabel("Aguardando PDF's")
            msg_label.setStyleSheet("font-size: 24px; color: #333333; font-weight: bold;")
            msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(msg_label)

            sub_label = QLabel("Clique em 'Carregar' ou arraste arquivos aqui.")
            sub_label.setStyleSheet("font-size: 16px; color: #666666; margin-top: 10px;")
            sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(sub_label)

            # Center in grid
            self.grid_layout.addWidget(empty_widget, 0, 0, 1, columns)

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
                # Start new section
                if col > 0:
                    row += 1
                    col = 0

                # Add Header Separator
                # Create a container for the header style
                header_label = QLabel(f"  {file_name}")
                header_label.setStyleSheet("""
                    background-color: #F9F9F9;
                    color: #009A3E;
                    font-weight: bold;
                    padding: 8px;
                    border-left: 5px solid #009A3E;
                    font-size: 14px;
                    margin-top: 10px;
                """)
                self.grid_layout.addWidget(header_label, row, 0, 1, columns)
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

        # Update container's thumbnail reference
        self.container.set_thumbnails(self.thumbnails)

    def on_thumbnail_hover(self, index, pos):
        # Show floating card
        img_data = self.main_window.pdf_manager.get_thumbnail(index, scale=0.8) # Higher quality for hover
        image = QImage.fromData(img_data)
        pixmap = QPixmap.fromImage(image)
        # Limit size
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

            # Requirement: "Visualizador por Click: Um clique na miniatura deve ... Exibir a página inteira no Painel Direito"
            # It should also select.
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
        # Programmatic selection setting
        self.selected_indices = set()
        count = self.main_window.pdf_manager.get_page_count()
        for i in indices:
            if 0 <= i < count:
                self.selected_indices.add(i)

        self.update_visual_selection()
        # We probably shouldn't emit 'page_selected' back to avoid loop if this came from LeftPanel
        # But LeftPanel only listens to nothing, it emits.
        # However, if we emit, LeftPanel will receive it via MainWindow connection and update text?
        # MainWindow connects: self.center_canvas.page_selected.connect(self.handle_page_selection)
        # handle_page_selection calls left_panel.update_selection_input.
        # update_selection_input updates text.
        # Updating text MIGHT trigger textChanged?
        # If QLineEdit.setText triggers textChanged, we have a loop.
        # Usually programmatic setText DOES NOT trigger textChanged signal in Qt?
        # WAIT: setText DOES NOT trigger textChanged in Qt? It usually DOES NOT?
        # Actually in PyQt/Qt, setText DOES NOT trigger textChanged if not modified by user?
        # Correction: setText DOES trigger textChanged. It DOES.
        # We need to block signals in LeftPanel when updating text.
        pass

    # Drag and Drop Logic Implementation
    # This is complex in a GridLayout.
    # For MVP, let's skip complex visual drag-and-drop reordering inside the grid
    # and just focus on basic functionality or implement it if time permits.
    # Requirement: "Drag-and-Drop (Alternar Ordem): Deve permitir que o usuário arraste e solte miniaturas livremente"

    # We can use the drag events.
    # When drag enters a thumbnail, we can visualize where it would drop.
    pass
