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
        self.setFixedHeight(70)
        # Usando fundo branco para o header e verde na borda para destacar o branding
        self.setStyleSheet("background-color: white; border-bottom: 2px solid #009A3E;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 5, 20, 5)

        # Logo (Refatorado para ser o primeiro elemento)
        logo_label = QLabel()
        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
             pixmap = QPixmap(logo_path)
             if not pixmap.isNull():
                 # Tamanho maior no header
                 logo_label.setPixmap(pixmap.scaled(180, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(logo_label)

        layout.addStretch()

        title = QLabel("UNIMED - Editor de PDF")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #009A3E; border: none;")
        layout.addWidget(title)

class LoadingDialog(QProgressDialog):
    # (MANTIDO DO ORIGINAL)
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
    # (MANTIDO DO ORIGINAL)
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

        # APLICANDO ESTILOS
        self.setStyleSheet(STYLESHEET)

        self.pdf_manager = PDFManager()

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget) # Layout principal vertical (Header + Corpo)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. HEADER (TOPO)
        self.header = Header(self)
        main_layout.addWidget(self.header)

        # 2. CORPO (Lateral + Splitter)
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

        # Wrapping Canvas and Viewer with Titles
        self.splitter.addWidget(self.create_pane("Canvas de Edição", self.center_canvas))
        self.splitter.addWidget(self.create_pane("Visualização Unitária", self.right_viewer))

        self.splitter.setCollapsible(1, True)
        # 50/50 Balance
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)

        content_layout.addWidget(self.left_panel)
        content_layout.addWidget(self.splitter)

    def create_pane(self, title_text, widget):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel(title_text)
        header.setStyleSheet("""
            background-color: #F0F0F0;
            color: #333333;
            font-weight: bold;
            padding: 8px;
            border-bottom: 1px solid #CCCCCC;
            font-size: 14px;
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(header)
        layout.addWidget(widget)
        return container

        main_layout.addWidget(content_widget) # Adiciona o corpo ao layout principal

        # Connect signals
        self.left_panel.action_triggered.connect(self.handle_action)
        self.center_canvas.page_selected.connect(self.handle_page_selection)
        self.center_canvas.page_order_changed.connect(self.handle_page_reorder)
        self.center_canvas.request_viewer.connect(self.open_viewer)
        self.right_viewer.action_triggered.connect(self.handle_viewer_action)

    # (MANTENHA TODAS AS FUNÇÕES AUXILIARES E DE AÇÃO ABAIXO)
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
            self.export_single_page(data)

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
                new_total = self.pdf_manager.get_page_count()
                if new_total > 0:
                    new_idx = min(idx, new_total - 1)
                    self.open_viewer(new_idx)
                else:
                    self.right_viewer.clear()
                    self.center_canvas.clear_selection()

    def export_single_page(self, export_format):
        idx = self.right_viewer.current_page_index
        if idx is None:
            return

        filters = "PDF Files (*.pdf);;PNG Image (*.png);;JPEG Image (*.jpg *.jpeg)"
        default_ext = ".pdf" if export_format == 'pdf' else ".png"
        default_filter = f"*{default_ext}"

        output_path, selected_filter = QFileDialog.getSaveFileName(self, "Baixar Página", f"pagina_{idx+1}{default_ext}", filters, default_filter)
        if output_path:
            self.show_loading("Exportando página...")

            def task():
                # Extract single page based on filter
                if selected_filter.endswith('.png)') or selected_filter.endswith('.jpg)'):
                    # Render page as image
                    original_idx = self.pdf_manager.page_order[idx][0]
                    page = self.pdf_manager.doc.load_page(original_idx)
                    # Render with high quality (300 DPI)
                    pix = page.get_pixmap(dpi=300)
                    pix.save(output_path)
                else:
                    # Save single page PDF
                    new_doc = self.pdf_manager.fitz.open()
                    original_idx = self.pdf_manager.page_order[idx][0]
                    new_doc.insert_pdf(self.pdf_manager.doc, from_page=original_idx, to_page=original_idx)
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
            self.right_viewer.clear()
            self.center_canvas.clear_selection()

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
            confirm = QMessageBox.question(self, "Confirmar Exclução",
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
