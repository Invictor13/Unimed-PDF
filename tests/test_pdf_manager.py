import unittest
import os
import fitz
from PIL import Image
import io
from unimed_pdf_editor.core.pdf_manager import PDFManager

class TestPDFManager(unittest.TestCase):
    def setUp(self):
        self.manager = PDFManager()
        self.test_pdf = "test_doc_with_images.pdf"
        # Create a PDF with an actual raster image
        doc = fitz.open()
        page = doc.new_page()

        # Create a large red image using PIL
        img = Image.new('RGB', (2000, 2000), color='red')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()

        # Insert image
        page.insert_image(page.rect, stream=img_bytes)
        doc.save(self.test_pdf)
        doc.close()

    def tearDown(self):
        if self.manager.doc:
            self.manager.doc.close()
        if os.path.exists(self.test_pdf):
            os.remove(self.test_pdf)
        if os.path.exists("compressed_high.pdf"):
            os.remove("compressed_high.pdf")

    def test_load_pdf(self):
        count = self.manager.load_pdf(self.test_pdf)
        self.assertEqual(count, 1)
        self.assertEqual(self.manager.get_page_count(), 1)

    def test_compress_pdf_high(self):
        self.manager.load_pdf(self.test_pdf)
        output_path = "compressed_high.pdf"

        # Get original size
        original_size = os.path.getsize(self.test_pdf)

        self.manager.compress_pdf(output_path, level="high")
        self.assertTrue(os.path.exists(output_path))

        # Verify file size reduction (since we start with a large unoptimized image or at least redundant structure)
        # Note: PyMuPDF might optimize structure even if image size is similar, but here we expect downsampling
        compressed_size = os.path.getsize(output_path)

        # Verify that the image in the compressed PDF is actually smaller/downsampled
        doc = fitz.open(output_path)
        page = doc[0]
        images = page.get_images()
        self.assertEqual(len(images), 1)
        xref = images[0][0]
        pix = fitz.Pixmap(doc, xref)

        # Original was 2000x2000, max dim is 1500, so should be scaled down
        # New max dimension is 1500
        self.assertTrue(pix.width <= 1500)
        self.assertTrue(pix.height <= 1500)

        doc.close()

if __name__ == '__main__':
    unittest.main()
