from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QSplitter, QFileDialog, QMessageBox, QProgressDialog, QApplication, QLabel, QInputDialog
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QIcon
from .styles import STYLESHEET
from .left_panel import LeftPanel
from .center_canvas import CenterCanvas
from .right_viewer import RightViewer
from ..core.pdf_manager import PDFManager
import os

class Header(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.setStyleSheet("background-color: white; border-bottom: 2px solid #009A3E;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)

        # Logo
        logo_label = QLabel()
        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
             pixmap = QPixmap(logo_path)
             if not pixmap.isNull():
                 logo_label.setPixmap(pixmap.scaled(150, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(logo_label)

        layout.addStretch()

        title = QLabel("Editor PDF Unimed")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #009A3E; border: none;")
        layout.addWidget(title)

        # Could add version or user info here
        # layout.addStretch()

class LoadingDialog(QProgressDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setCancelButton(None)
        self.setMinimumDuration(0)
        self.setRange(0, 0) # Indeterminate

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Logo
        logo_label = QLabel()
        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
             pixmap = QPixmap(logo_path)
             if not pixmap.isNull():
                 logo_label.setPixmap(pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(logo_label)

        # Text
        text_label = QLabel(message)
        text_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333333; margin-left: 10px; border: none;")
        layout.addWidget(text_label)

        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 2px solid #009A3E;
                border-radius: 10px;
            }
        """)

class Worker(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor PDF Unimed")
        self.resize(1200, 800)

        # Apply global stylesheet adjustments for Dialogs
        from .styles import COLOR_PRIMARY
        dialog_style = f"""
            QMessageBox, QInputDialog {{
                background-color: white;
            }}
            QMessageBox QLabel, QInputDialog QLabel {{
                color: #333333;
                background-color: transparent;
            }}
            QMessageBox QPushButton, QInputDialog QPushButton {{
                background-color: {COLOR_PRIMARY};
                color: white;
                border-radius: 4px;
                padding: 6px 16px;
                min-width: 80px;
                border: none;
            }}
            QMessageBox QPushButton:hover, QInputDialog QPushButton:hover {{
                background-color: #007A30;
            }}
        """
        self.setStyleSheet(STYLESHEET + dialog_style)

        self.pdf_manager = PDFManager()

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: white;")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        self.header = Header(self)
        main_layout.addWidget(self.header)

        # Content Area (Left Panel + Splitter)
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Left Panel (Fixed Width)
        self.left_panel = LeftPanel(self)
        self.left_panel.setFixedWidth(250)

        # Center and Right (Splitter)
        self.center_canvas = CenterCanvas(self)
        self.right_viewer = RightViewer(self)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.center_canvas)
        self.splitter.addWidget(self.right_viewer)

        self.splitter.setCollapsible(1, True)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)

        content_layout.addWidget(self.left_panel)
        content_layout.addWidget(self.splitter)

        main_layout.addWidget(content_widget)

        # Connect signals
        self.left_panel.action_triggered.connect(self.handle_action)
        self.center_canvas.page_selected.connect(self.handle_page_selection)
        self.center_canvas.page_order_changed.connect(self.handle_page_reorder)
        self.center_canvas.request_viewer.connect(self.open_viewer)
        self.right_viewer.action_triggered.connect(self.handle_viewer_action)

    def handle_action(self, action_name, data=None):
        if action_name == "load_pdf":
            self.load_pdf(data)
        elif action_name == "merge":
            self.merge_pdfs()
        elif action_name == "split":
            self.split_pdf()
        elif action_name == "compress":
            self.compress_pdf(data)
        elif action_name == "delete":
            self.delete_selected_pages()
        elif action_name == "ocr":
            self.run_ocr()
        elif action_name == "select_pages":
            self.select_pages_from_input(data)
        elif action_name == "clear_session":
            self.clear_session()
        elif action_name == "rotate_selected":
            self.rotate_selected_pages()

    def select_pages_from_input(self, indices):
        self.center_canvas.set_selection(indices)

    def load_pdf(self, filepaths):
        if not filepaths:
            return

        # Handle multiple files by merging them into one list if necessary
        # But PDFManager.load_pdf takes a single file usually.
        # For now, let's load the first one or iterate.
        # Ideally, we should merge them into the session.
        # Assuming single file load for now based on current manager capabilities or
        # if the manager supports appending, we call append.
        # But based on typical implementation, we might clear and load new.
        # If multiple files are dropped, we can propose merge.

        # For now, just load the first one.
        count = self.pdf_manager.load_pdf(filepaths[0])
        self.center_canvas.refresh_thumbnails()

    def handle_page_selection(self, selected_indices):
        self.left_panel.update_selection_input(selected_indices)

    def handle_page_reorder(self, from_idx, to_idx):
        self.pdf_manager.move_page(from_idx, to_idx)

    def open_viewer(self, page_index):
        if self.splitter.sizes()[1] == 0:
             self.splitter.setSizes([700, 300])

        self.right_viewer.load_page(page_index)

    def handle_viewer_action(self, action, data):
        if action == "delete_page":
            self.delete_single_page_from_viewer()
        elif action == "download_page":
            self.export_single_page()

    def delete_single_page_from_viewer(self):
        idx = self.right_viewer.current_page_index
        if idx is not None:
             confirm = QMessageBox.question(self, "Confirmar Exclusão",
                                         f"Tem certeza que deseja excluir a página {idx + 1}?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
             if confirm == QMessageBox.StandardButton.Yes:
                self.pdf_manager.delete_pages([idx])
                self.center_canvas.refresh_thumbnails()
                # Determine next page to show
                new_total = len(self.pdf_manager.doc) if self.pdf_manager.doc else 0
                if new_total > 0:
                    new_idx = min(idx, new_total - 1)
                    self.open_viewer(new_idx)
                else:
                    self.right_viewer.clear()

    def export_single_page(self):
        idx = self.right_viewer.current_page_index
        if idx is None:
            return

        output_path, _ = QFileDialog.getSaveFileName(self, "Baixar Página", f"pagina_{idx+1}.pdf", "PDF Files (*.pdf);;Images (*.png *.jpg)")
        if output_path:
            self.show_loading("Exportando página...")

            def task():
                # Extract single page
                # If image format, render and save. If PDF, extract page.
                if output_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    # Render page
                    page = self.pdf_manager.doc[idx]
                    pix = page.get_pixmap(dpi=300)
                    pix.save(output_path)
                else:
                    # Save single page PDF
                    new_doc = self.pdf_manager.fitz.open()
                    new_doc.insert_pdf(self.pdf_manager.doc, from_page=idx, to_page=idx)
                    new_doc.save(output_path)
                    new_doc.close()

            def success(_):
                 QMessageBox.information(self, "Sucesso", "Página exportada com sucesso!")

            self.execute_task(task, success_callback=success)

    def show_loading(self, message="Processando..."):
        self.loading_dialog = LoadingDialog(message, self)
        self.loading_dialog.show()
        QApplication.processEvents()

    def hide_loading(self):
        if hasattr(self, 'loading_dialog') and self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None

    def clear_session(self):
        confirm = QMessageBox.question(self, "Confirmar",
                                       "Tem certeza que deseja limpar a sessão? Todas as alterações não salvas serão perdidas.",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.pdf_manager.clear_session()
            self.center_canvas.refresh_thumbnails()
            if hasattr(self.right_viewer, 'clear'):
                self.right_viewer.clear()

    def execute_task(self, func, *args, success_callback=None, **kwargs):
        self.thread = QThread()
        self.worker = Worker(func, *args, **kwargs)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.worker.finished.connect(self.hide_loading)
        if success_callback:
            self.worker.finished.connect(success_callback)

        self.worker.error.connect(lambda err: QMessageBox.critical(self, "Erro", f"Ocorreu um erro: {err}"))
        self.worker.error.connect(self.hide_loading)

        self.thread.start()

    def rotate_selected_pages(self):
        indices = self.center_canvas.get_selected_indices()
        if not indices:
             QMessageBox.warning(self, "Atenção", "Selecione as páginas para rotacionar.")
             return

        self.show_loading("Rotacionando páginas...")

        def task():
            for idx in indices:
                self.pdf_manager.rotate_page(idx, 90)

        self.execute_task(task, success_callback=lambda _: self.center_canvas.refresh_thumbnails())

    def merge_pdfs(self):
        output_path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF Unificado", "unificado.pdf", "PDF Files (*.pdf)")
        if output_path:
            self.show_loading("Unificando PDF...")

            def success(_):
                QMessageBox.information(self, "Sucesso", "PDF unificado salvo com sucesso!")

            self.execute_task(self.pdf_manager.save_pdf, output_path, success_callback=success)

    def split_pdf(self):
        indices = self.center_canvas.get_selected_indices()
        if not indices:
            QMessageBox.warning(self, "Atenção", "Selecione as páginas para separar.")
            return

        output_path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF Separado", "separado.pdf", "PDF Files (*.pdf)")
        if output_path:
            self.show_loading("Separando PDF...")

            def success(_):
                QMessageBox.information(self, "Sucesso", "PDF separado salvo com sucesso!")

            self.execute_task(self.pdf_manager.split_pdf, indices, output_path, success_callback=success)

    def compress_pdf(self, level):
        output_path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF Compactado", "compactado.pdf", "PDF Files (*.pdf)")
        if output_path:
            self.show_loading(f"Compactando PDF (Nível: {level})...")

            def success(_):
                QMessageBox.information(self, "Sucesso", f"PDF compactado ({level}) salvo com sucesso!")

            self.execute_task(self.pdf_manager.compress_pdf, output_path, level, success_callback=success)

    def delete_selected_pages(self):
        indices = self.center_canvas.get_selected_indices()
        if indices:
            confirm = QMessageBox.question(self, "Confirmar Exclusão",
                                         f"Tem certeza que deseja excluir {len(indices)} página(s)?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if confirm == QMessageBox.StandardButton.Yes:
                self.pdf_manager.delete_pages(indices)
                self.center_canvas.refresh_thumbnails()
                self.center_canvas.clear_selection()

    def run_ocr(self):
        if not self.pdf_manager.filepath:
            return

        from ..core.ocr_engine import OCREngine
        ocr = OCREngine()

        output_path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF Pesquisável", "ocr.pdf", "PDF Files (*.pdf)")
        if output_path:
            self.show_loading("Executando OCR...")

            def task():
                return ocr.make_searchable(self.pdf_manager.filepath, output_path)

            def success(result):
                success, msg = result
                if success:
                     QMessageBox.information(self, "Sucesso", msg)
                else:
                     QMessageBox.critical(self, "Erro", f"Falha no OCR: {msg}")

            self.execute_task(task, success_callback=success)
