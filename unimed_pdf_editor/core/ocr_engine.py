import sys
import os
import pytesseract
from PIL import Image
import fitz # PyMuPDF
from pypdf import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

class OCREngine:
    def __init__(self):
        self._setup_tesseract_path()

    def _setup_tesseract_path(self):
        """
        Sets the tesseract command path, handling PyInstaller's sys._MEIPASS
        """
        if getattr(sys, 'frozen', False):
            # If running as a PyInstaller bundle
            base_path = sys._MEIPASS
            # Assuming tesseract binary is bundled at the root or a specific folder
            # Adjust 'tesseract' to the actual folder name if bundled differently
            if os.name == 'nt':
                tesseract_path = os.path.join(base_path, 'tesseract', 'tesseract.exe')
            else:
                tesseract_path = os.path.join(base_path, 'tesseract', 'tesseract')
        else:
            # Development environment - assume it's in PATH or set explicitly
            # Here we just check if it's reachable, otherwise user might need to install it
            tesseract_path = 'tesseract'

        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def make_searchable(self, input_pdf_path, output_pdf_path, progress_callback=None):
        """
        Takes a PDF, runs OCR on each page, and saves a new PDF with text layer.
        """
        try:
            doc = fitz.open(input_pdf_path)
            writer = PdfWriter()

            total_pages = len(doc)

            for page_num, page in enumerate(doc):
                if progress_callback:
                    progress_callback(page_num, total_pages)

                # Get image from page
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))

                # Run OCR
                # get PDF data from tesseract
                pdf_data = pytesseract.image_to_pdf_or_hocr(image, extension='pdf')

                # Read the OCR'd PDF page
                ocr_reader = PdfReader(io.BytesIO(pdf_data))
                ocr_page = ocr_reader.pages[0]

                writer.add_page(ocr_page)

            with open(output_pdf_path, "wb") as f:
                writer.write(f)

            return True, "OCR completed successfully."

        except Exception as e:
            return False, str(e)
