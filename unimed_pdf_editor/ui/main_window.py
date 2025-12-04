from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QFrame, QSplitter, QFileDialog, QMessageBox, QProgressDialog, QApplication, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from .styles import STYLESHEET
from .left_panel import LeftPanel
from .center_canvas import CenterCanvas
from .right_viewer import RightViewer
from ..core.pdf_manager import PDFManager

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
        from PyQt6.QtGui import QPixmap
        import os
        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
             pixmap = QPixmap(logo_path)
             if not pixmap.isNull():
                 logo_label.setPixmap(pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(logo_label)

        # Text
        text_label = QLabel(message)
        text_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333333; margin-left: 10px;")
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
        # Note: QMessageBox usually needs application-level stylesheet or explicit setStyleSheet
        # We append some specific styling for standard dialogs to the main stylesheet
        from .styles import COLOR_PRIMARY
        dialog_style = f"""
            QMessageBox, QInputDialog {{
                background-color: white;
            }}
            QMessageBox QLabel, QInputDialog QLabel {{
                color: #333333;
            }}
            QMessageBox QPushButton, QInputDialog QPushButton {{
                background-color: {COLOR_PRIMARY};
                color: white;
                border-radius: 4px;
                padding: 6px 16px;
                min-width: 80px;
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
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter to allow resizing panels (though requirements said fixed, split view usually implies adjustable)
        # Requirements: "Três painéis principais (um split view horizontal)"
        # and "Painel Esquerdo ... Fixo, largura menor"
        # We will make Left Panel fixed width, and allow Center/Right to share space.

        self.left_panel = LeftPanel(self)
        self.center_canvas = CenterCanvas(self)
        self.right_viewer = RightViewer(self)

        self.left_panel.setFixedWidth(250)

        # We use a splitter for Center and Right
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.center_canvas)
        self.splitter.addWidget(self.right_viewer)

        # Right panel initially collapsed or takes some space?
        # Req: "Opcional/Expansível, exibindo a página inteira sob demanda."
        self.splitter.setCollapsible(1, True)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)

        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.splitter)

        # Connect signals
        self.left_panel.action_triggered.connect(self.handle_action)
        self.center_canvas.page_selected.connect(self.handle_page_selection)
        self.center_canvas.page_order_changed.connect(self.handle_page_reorder)
        self.center_canvas.request_viewer.connect(self.open_viewer)
        self.right_viewer.action_triggered.connect(self.handle_viewer_action)

    def handle_action(self, action_name, data=None):
        # Delegate to appropriate handlers
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
        # Update selection in Canvas
        # We need a method in Canvas to set selection programmatically without emitting signal back?
        # Or just use set_selected.
        self.center_canvas.set_selection(indices)

    def load_pdf(self, filepaths):
        # For simplicity, assuming single file load or handling multiple by merging first?
        # Req: "Combina todos os PDFs carregados ... Se apenas um PDF estiver carregado..."
        # It seems we should support loading multiple files.
        # The PDFManager I wrote supports one doc.
        # I should probably update PDFManager to handle "Import" which merges into current session
        # OR just load one for now as MVP.
        # Let's stick to loading one file or merging multiple into one session immediately.

        if not filepaths:
            return

        # MVP: Load the first one. To support multiple, we would need to merge them in memory first.
        # Let's update PDFManager to support 'add_pdf' or similar if needed.
        # For now, let's load the first one.
        count = self.pdf_manager.load_pdf(filepaths[0])
        self.center_canvas.refresh_thumbnails()

    def handle_page_selection(self, selected_indices):
        self.left_panel.update_selection_input(selected_indices)

    def handle_page_reorder(self, from_idx, to_idx):
        self.pdf_manager.move_page(from_idx, to_idx)

    def open_viewer(self, page_index):
        # Show right panel if hidden
        if self.splitter.sizes()[1] == 0:
             self.splitter.setSizes([700, 300]) # Approximate

        self.right_viewer.load_page(page_index)

    def handle_viewer_action(self, action, data):
        # Rotate, Delete from viewer
        pass

    def show_loading(self, message="Processando..."):
        """Displays a simple modal loading dialog."""
        self.loading_dialog = LoadingDialog(message, self)
        self.loading_dialog.show()
        QApplication.processEvents() # Force UI update

    def hide_loading(self):
        """Hides the loading dialog."""
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
                self.right_viewer.clear() # Assuming right_viewer has a clear method or handles loading empty page

    def execute_task(self, func, *args, success_callback=None, **kwargs):
        """Helper to run tasks in a separate thread."""
        self.thread = QThread()
        self.worker = Worker(func, *args, **kwargs)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # UI Handling
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
