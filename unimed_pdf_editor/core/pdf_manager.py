import sys
import os
import fitz  # PyMuPDF
from PIL import Image
import io
from pypdf import PdfReader, PdfWriter

class PDFManager:
    def __init__(self):
        self.doc = None  # Current PyMuPDF document
        self.filepath = None
        self.page_order = [] # List of page indices in the original doc
        self.thumbnails = {} # Cache for thumbnails

    def load_pdf(self, filepath):
        # If we already have a doc, we close it? Or we append?
        # The architecture was simple. To support multiple PDFs seamlessly for editing:
        # We can either maintain a list of (filepath, page_index) tuples in page_order
        # OR we can merge incoming PDFs into a temporary in-memory PDF (or temp file).
        # Using PyMuPDF's insert_pdf is efficient.

        new_doc = fitz.open(filepath)

        if self.doc is None:
            self.doc = new_doc
            self.filepath = filepath # Primary filepath (maybe use for save default)
        else:
            self.doc.insert_pdf(new_doc)
            # new_doc is merged into self.doc

        # Re-sync page order
        # This is a bit simplistic: if we load a 2nd PDF, we just append its pages to the current list
        current_count = len(self.page_order)
        new_pages_count = len(self.doc) - current_count

        # Add new page indices
        # page_order stores indices of self.doc
        # Since we modified self.doc in place by appending, the new pages are at the end
        for i in range(new_pages_count):
            self.page_order.append(current_count + i)

        # Clear specific thumbnail cache?
        # No, thumbnails for existing indices are valid. New indices don't have cache yet.
        return len(self.doc)

    def rotate_page(self, page_index, angle=90):
        """
        Rotates the page at page_index by angle (clockwise).
        page_index: index in the current page_order
        """
        if 0 <= page_index < len(self.page_order):
            original_index = self.page_order[page_index]
            page = self.doc.load_page(original_index)
            page.set_rotation(page.rotation + angle)

            # Invalidate thumbnail for this page
            if original_index in self.thumbnails:
                del self.thumbnails[original_index]

    def get_page_count(self):
        return len(self.page_order)

    def get_thumbnail(self, page_index, scale=0.3):
        """
        Returns a QImage/Pixmap compatible byte array or PIL Image for the thumbnail.
        page_index: index in the CURRENT page_order
        """
        original_index = self.page_order[page_index]

        # Check cache
        if original_index in self.thumbnails:
            return self.thumbnails[original_index]

        page = self.doc.load_page(original_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))

        # Convert to bytes for PyQt
        img_data = pix.tobytes("ppm")
        self.thumbnails[original_index] = img_data
        return img_data

    def get_page_image(self, page_index, scale=2.0):
        """
        Returns a high-res image for the viewer.
        """
        original_index = self.page_order[page_index]
        page = self.doc.load_page(original_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        return pix.tobytes("ppm")

    def move_page(self, from_index, to_index):
        if 0 <= from_index < len(self.page_order) and 0 <= to_index < len(self.page_order):
            page_id = self.page_order.pop(from_index)
            self.page_order.insert(to_index, page_id)

    def delete_pages(self, indices):
        # Sort indices in descending order to avoid shifting issues during deletion
        # from the list
        sorted_indices = sorted(indices, reverse=True)
        for idx in sorted_indices:
            if 0 <= idx < len(self.page_order):
                del self.page_order[idx]

    def save_pdf(self, output_path):
        """
        Saves the current state of the PDF using PyMuPDF to handle potentially merged documents and rotations.
        """
        # Since self.doc contains all pages (merged or not) and rotations are applied on self.doc pages
        # We just need to save a new PDF with the correct order.

        output_doc = fitz.open()
        output_doc.insert_pdf(self.doc, from_page=-1, to_page=-1) # Dummy init? No.

        # Actually, insert_pdf allows picking pages.
        # But we need to map page_order (list of indices) to the sequence in self.doc

        # A more efficient way if we have many pages:
        # Create a new doc, copy pages in order.

        # However, PyMuPDF insert_pdf takes a range. We have a random list.
        # So we iterate.
        output_doc = fitz.open()
        for original_idx in self.page_order:
            output_doc.insert_pdf(self.doc, from_page=original_idx, to_page=original_idx)

        output_doc.save(output_path)
        output_doc.close()

    def split_pdf(self, selected_indices, output_path):
        """
        Creates a new PDF with only the selected pages.
        """
        output_doc = fitz.open()
        for idx in selected_indices:
            if 0 <= idx < len(self.page_order):
                original_idx = self.page_order[idx]
                output_doc.insert_pdf(self.doc, from_page=original_idx, to_page=original_idx)

        output_doc.save(output_path)
        output_doc.close()

    def compress_pdf(self, output_path, level="medium"):
        """
        Compresses the PDF.
        Level: 'low', 'medium', 'high'
        """
        # Note: pypdf has limited compression capabilities (mostly lossless).
        # For image compression, we might need to iterate images and compress them using Pillow,
        # then replace them in the PDF. However, pypdf supports `compress_content_streams`.
        # For this task, we will use basic compression provided by pypdf and/or PyMuPDF.

        # Using PyMuPDF for "garbage collection" and stream compression is often better.

        deflate = True
        garbage = 0
        clean = False

        if level == "low":
            garbage = 1
        elif level == "medium":
            garbage = 2
            deflate = True
        elif level == "high":
            garbage = 3
            deflate = True
            clean = True

        # Create a new document with the current order
        new_doc = fitz.open()
        new_doc.insert_pdf(self.doc, from_page= -1, to_page= -1) # Copy metadata? No, we need specific pages.

        # Actually we need to respect page_order
        # It's more efficient to just save the current self.doc with garbage collection options
        # BUT self.doc is read-only regarding structure if we want to keep it simple,
        # or we create a subset doc.

        subset_doc = fitz.open()
        for original_idx in self.page_order:
            subset_doc.insert_pdf(self.doc, from_page=original_idx, to_page=original_idx)

        subset_doc.save(output_path, garbage=garbage, deflate=deflate, clean=clean)
        subset_doc.close()
