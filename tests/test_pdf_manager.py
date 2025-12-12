
import unittest
import os
import shutil
from reportlab.pdfgen import canvas
from unimed_pdf_editor.core.pdf_manager import PDFManager
import fitz

class TestPDFManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_data"
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)

        self.pdf_path = os.path.join(self.test_dir, "test.pdf")
        self.create_test_pdf(self.pdf_path)

        self.manager = PDFManager()

    def tearDown(self):
        if self.manager.doc:
            self.manager.doc.close()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def create_test_pdf(self, path):
        c = canvas.Canvas(path)
        c.drawString(100, 750, "Page 1")
        c.showPage()
        c.drawString(100, 750, "Page 2")
        c.showPage()
        c.save()

    def test_load_pdf(self):
        count = self.manager.load_pdf(self.pdf_path)
        self.assertEqual(count, 2)
        self.assertEqual(self.manager.get_page_count(), 2)

    def test_reorder_file(self):
        # Create another PDF to simulate 2 files
        pdf2_path = os.path.join(self.test_dir, "test2.pdf")
        self.create_test_pdf(pdf2_path)

        self.manager.load_pdf(self.pdf_path)
        self.manager.load_pdf(pdf2_path)

        # Initial order: File1 (2 pages), File2 (2 pages)
        # Total 4 pages
        self.assertEqual(self.manager.get_page_count(), 4)

        files = self.manager.get_files_in_order()
        self.assertEqual(len(files), 2)
        file1_id = files[0]['file_id']
        file2_id = files[1]['file_id']

        # Move File 2 to index 0
        self.manager.reorder_file(file2_id, 0)

        files = self.manager.get_files_in_order()
        self.assertEqual(files[0]['file_id'], file2_id)
        self.assertEqual(files[1]['file_id'], file1_id)

        # Check page order
        # Should be File2 pages then File1 pages
        page_info0 = self.manager.get_page_info(0)
        page_info2 = self.manager.get_page_info(2)

        self.assertEqual(page_info0['file_id'], file2_id)
        self.assertEqual(page_info2['file_id'], file1_id)

    def test_rotate_page(self):
        self.manager.load_pdf(self.pdf_path)
        original_rotation = self.manager.doc[0].rotation
        self.manager.rotate_page(0, 90)
        new_rotation = self.manager.doc[0].rotation
        self.assertEqual(new_rotation, (original_rotation + 90) % 360)

    def test_delete_pages(self):
        self.manager.load_pdf(self.pdf_path)
        self.manager.delete_pages([0])
        self.assertEqual(self.manager.get_page_count(), 1)
        # Remaining page should be original page 2
        # Original page 2 was index 1 (0-based) in doc, index 1 in page_order.
        # Now it is index 0 in page_order.
        # Since we physically deleted page 0, the remaining page (was 1) is now at index 0 in physical doc.
        page_info = self.manager.get_page_info(0)
        self.assertEqual(page_info['original_index'], 0)

    def test_compress_quality(self):
        # Verify checking code in compress_pdf
        # Since we can't easily check the output quality without visual inspection or deep analysis,
        # we check if the function runs without error with "high" compression which triggers the JPEG encoding.

        # Create a PDF with an image to trigger compression logic
        img_pdf_path = os.path.join(self.test_dir, "img.pdf")

        # Create a dummy image
        from PIL import Image
        img = Image.new('RGB', (100, 100), color = 'red')
        img_path = os.path.join(self.test_dir, "test_img.jpg")
        img.save(img_path)

        doc = fitz.open()
        page = doc.new_page()
        page.insert_image(page.rect, filename=img_path)
        doc.save(img_pdf_path)
        doc.close()

        self.manager.load_pdf(img_pdf_path)
        output_path = os.path.join(self.test_dir, "compressed.pdf")

        try:
            self.manager.compress_pdf(output_path, level="high")
            self.assertTrue(os.path.exists(output_path))
        except Exception as e:
            self.fail(f"Compress PDF failed: {e}")

if __name__ == '__main__':
    unittest.main()
