from PyQt6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QWidget, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QPoint
from PyQt6.QtGui import QPixmap, QImage, QDrag

class Thumbnail(QWidget):
    clicked = pyqtSignal(int, bool, bool) # index, shift_pressed, ctrl_pressed (ctrl not used but good practice)
    double_clicked = pyqtSignal(int)
    hover_entered = pyqtSignal(int, QPoint)
    hover_left = pyqtSignal(int)

    def __init__(self, index, image_data):
        super().__init__()
        self.index = index
        self.selected = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.image_label = QLabel()
        self.image_label.setObjectName("ThumbnailLabel")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(150, 200) # Fixed thumbnail size

        # Load image
        image = QImage.fromData(image_data)
        pixmap = QPixmap.fromImage(image)
        # Scale to fit label
        pixmap = pixmap.scaled(140, 190, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(pixmap)

        layout.addWidget(self.image_label)

        # Bottom Layout for Number and Drag Handle
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        self.number_label = QLabel(str(index + 1))
        self.number_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.drag_handle = QLabel("⠿")
        self.drag_handle.setStyleSheet("color: #999999; font-size: 16px; cursor: size_all;")
        self.drag_handle.setVisible(False) # Show on hover

        bottom_layout.addStretch()
        bottom_layout.addWidget(self.number_label)
        bottom_layout.addWidget(self.drag_handle)
        bottom_layout.addStretch()

        layout.addLayout(bottom_layout)

        self.setProperty("selected", False)

    def set_selected(self, selected):
        self.selected = selected
        self.image_label.setProperty("selected", "true" if selected else "false")
        self.image_label.style().unpolish(self.image_label)
        self.image_label.style().polish(self.image_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()

        shift = event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ctrl = event.modifiers() & Qt.KeyboardModifier.ControlModifier
        self.clicked.emit(self.index, bool(shift), bool(ctrl))

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if not hasattr(self, 'drag_start_position'):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(self.index))
        drag.setMimeData(mime_data)

        # Snapshot for drag
        pixmap = self.image_label.pixmap()
        if pixmap:
            drag.setPixmap(pixmap.scaled(50, 70, Qt.AspectRatioMode.KeepAspectRatio))
            drag.setHotSpot(event.pos())

        drag.exec(Qt.DropAction.MoveAction)

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.index)

    def enterEvent(self, event):
        self.drag_handle.setVisible(True)
        # Emit global pos for the tooltip to position itself
        # We use a slight offset to avoid covering the cursor immediately
        # Using QPoint(self.width(), 0) places it to the right
        self.hover_entered.emit(self.index, self.mapToGlobal(QPoint(self.width(), 0)))

    def leaveEvent(self, event):
        self.drag_handle.setVisible(False)
        self.hover_left.emit(self.index)
