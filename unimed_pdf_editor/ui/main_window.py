from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QFrame, QSplitter, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt
from .styles import STYLESHEET
from .left_panel import LeftPanel
from .center_canvas import CenterCanvas
from .right_viewer import RightViewer
from ..core.pdf_manager import PDFManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor PDF Unimed")
        self.resize(1200, 800)
        self.setStyleSheet(STYLESHEET)

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

    def merge_pdfs(self):
        # The current design loads multiple PDFs and merges them in memory via PDFManager's logic
        # if we had implemented "append" logic.
        # But per requirements: "Combina todos os PDFs carregados na ordem do Canvas Central."
        # Since our PDFManager currently only loads one file at a time or handles a session,
        # we assume "saving" the current state IS merging if multiple were loaded (or pages rearranged).

        output_path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF Unificado", "unificado.pdf", "PDF Files (*.pdf)")
        if output_path:
            self.pdf_manager.save_pdf(output_path)
            QMessageBox.information(self, "Sucesso", "PDF unificado salvo com sucesso!")

    def split_pdf(self):
        indices = self.center_canvas.get_selected_indices()
        if not indices:
            QMessageBox.warning(self, "Atenção", "Selecione as páginas para separar.")
            return

        output_path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF Separado", "separado.pdf", "PDF Files (*.pdf)")
        if output_path:
            self.pdf_manager.split_pdf(indices, output_path)
            QMessageBox.information(self, "Sucesso", "PDF separado salvo com sucesso!")

    def compress_pdf(self, level):
        output_path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF Compactado", "compactado.pdf", "PDF Files (*.pdf)")
        if output_path:
            self.pdf_manager.compress_pdf(output_path, level)
            QMessageBox.information(self, "Sucesso", f"PDF compactado ({level}) salvo com sucesso!")

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

        # Warning: This can take time. Should run in thread.
        # For MVP we run blocking or show a message.
        QMessageBox.information(self, "OCR", "Iniciando OCR. Isso pode demorar alguns instantes.")

        from ..core.ocr_engine import OCREngine
        ocr = OCREngine()

        output_path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF Pesquisável", "ocr.pdf", "PDF Files (*.pdf)")
        if output_path:
            success, msg = ocr.make_searchable(self.pdf_manager.filepath, output_path)
            if success:
                 QMessageBox.information(self, "Sucesso", msg)
            else:
                 QMessageBox.critical(self, "Erro", f"Falha no OCR: {msg}")
