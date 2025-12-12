from PyQt6.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QWidget, QApplication, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QPoint, QRect, QSize
from PyQt6.QtGui import QPixmap, QImage, QDrag, QPainter, QColor, QPen, QBrush, QFont, QPainterPath

class Thumbnail(QWidget):
    clicked = pyqtSignal(int, bool, bool) # index, shift_pressed, ctrl_pressed
    double_clicked = pyqtSignal(int)

    def __init__(self, index, image_data):
        super().__init__()
        self.index = index
        self._selected = False
        self._hovered = False
        self.image_pixmap = None

        # Fixed logic size for the widget, but painting will handle "Card" feel
        self.setFixedSize(220, 280)

        # Process Image Data
        if image_data:
            if isinstance(image_data, dict) and 'samples' in image_data:
                image = QImage(
                    image_data['samples'],
                    image_data['width'],
                    image_data['height'],
                    image_data['stride'],
                    QImage.Format.Format_RGB888
                )
            else:
                image = QImage.fromData(image_data)

            # Create a high-quality scaled pixmap for the card
            # Card image area is approx 200x240
            self.image_pixmap = QPixmap.fromImage(image).scaled(
                200, 240,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

        self.setMouseTracking(True)

    def set_selected(self, selected):
        if self._selected != selected:
            self._selected = selected
            self.update() # Trigger repaint

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. Background / Shadow Area
        # If hovered, lift slightly (shift rect up by 2px)
        offset = -2 if (self._hovered and not self._selected) else 0

        # Main Card Rect
        rect = self.rect().adjusted(10, 10 + offset, -10, -10 + offset)

        # Draw Shadow
        shadow_path = QPainterPath()
        shadow_path.addRoundedRect(rect.adjusted(2, 2, 2, 2), 8, 8)
        painter.fillPath(shadow_path, QColor(0, 0, 0, 30))

        # Draw Card Background (White)
        path = QPainterPath()
        path.addRoundedRect(rect, 8, 8)
        painter.fillPath(path, Qt.GlobalColor.white)

        # Draw Selection Border (Neon Effect)
        if self._selected:
            pen = QPen(QColor("#009A3E"), 3)
            painter.setPen(pen)
            painter.drawPath(path)

            # Inner Glow / Dimming logic
            # Actually, user asked for dimming the IMAGE. We do that below.
        else:
            # Subtle border
            painter.setPen(QPen(QColor("#DDDDDD"), 1))
            painter.drawPath(path)

        # 2. Draw Image
        if self.image_pixmap:
            # Center image in the rect, but shifted up slightly to leave room for page number
            img_rect = QRect(0, 0, self.image_pixmap.width(), self.image_pixmap.height())
            img_rect.moveCenter(rect.center())
            img_rect.moveTop(rect.top() + 10) # Padding top

            painter.drawPixmap(img_rect, self.image_pixmap)

            # Dimming if selected
            if self._selected:
                painter.setBrush(QColor(0, 0, 0, 25)) # 10% dimming roughly
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(img_rect)

        # 3. Page Number
        number_rect = QRect(rect.left(), rect.bottom() - 30, rect.width(), 30)
        painter.setPen(QColor("#333333"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(number_rect, Qt.AlignmentFlag.AlignCenter, str(self.index + 1))

        # 4. Checkmark (Google Gallery Style)
        if self._selected:
            check_size = 24
            check_rect = QRect(rect.right() - check_size - 5, rect.top() + 5, check_size, check_size)

            painter.setBrush(QColor("#009A3E"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(check_rect)

            # Draw Check Icon (White)
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
            # Simple tick shape
            p1 = QPoint(check_rect.left() + 6, check_rect.center().y())
            p2 = QPoint(check_rect.center().x() - 1, check_rect.bottom() - 6)
            p3 = QPoint(check_rect.right() - 6, check_rect.top() + 7)
            painter.drawLine(p1, p2)
            painter.drawLine(p2, p3)

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

        # Snapshot for drag (Render the widget)
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        self.render(pixmap)

        drag.setPixmap(pixmap.scaled(100, 130, Qt.AspectRatioMode.KeepAspectRatio))
        drag.setHotSpot(event.pos()) # Center drag? Or keep relative? Relative is fine.

        drag.exec(Qt.DropAction.MoveAction)

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.index)
