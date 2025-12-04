import sys
import os
import uuid
import fitz  # PyMuPDF
from PIL import Image
import io
from pypdf import PdfReader, PdfWriter

class PDFManager:
    def __init__(self):
        self.doc = None  # Current PyMuPDF document
        self.filepath = None
        self.page_order = [] # List of tuples: (original_doc_page_index, file_name, file_id)
        self.thumbnails = {} # Cache for thumbnails

    def load_pdf(self, filepath):
        new_doc = fitz.open(filepath)
        file_name = os.path.basename(filepath)
        file_id = str(uuid.uuid4())

        if self.doc is None:
            self.doc = new_doc
            self.filepath = filepath
            current_count = 0
        else:
            current_count = len(self.doc)
            self.doc.insert_pdf(new_doc)
            # new_doc is merged into self.doc

        new_pages_count = len(new_doc)

        # Add new page indices with file tracking info
        for i in range(new_pages_count):
            # The page index in the merged doc is current_count + i
            self.page_order.append((current_count + i, file_name, file_id))

        return len(self.page_order)

    def rotate_page(self, page_index, angle=90):
        if 0 <= page_index < len(self.page_order):
            original_index, _, _ = self.page_order[page_index]
            page = self.doc.load_page(original_index)
            page.set_rotation(page.rotation + angle)

            if original_index in self.thumbnails:
                del self.thumbnails[original_index]

    def get_page_count(self):
        return len(self.page_order)

    def get_page_info(self, page_index):
        if 0 <= page_index < len(self.page_order):
            idx, fname, fid = self.page_order[page_index]
            return {'original_index': idx, 'file_name': fname, 'file_id': fid}
        return None

    def get_thumbnail(self, page_index, scale=0.3):
        original_index, _, _ = self.page_order[page_index]

        if original_index in self.thumbnails:
            return self.thumbnails[original_index]

        page = self.doc.load_page(original_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))

        img_data = pix.tobytes("ppm")
        self.thumbnails[original_index] = img_data
        return img_data

    def get_page_image(self, page_index, scale=2.0):
        original_index, _, _ = self.page_order[page_index]
        page = self.doc.load_page(original_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        return pix.tobytes("ppm")

    def move_page(self, from_index, to_index):
        if 0 <= from_index < len(self.page_order) and 0 <= to_index < len(self.page_order):
            item = self.page_order.pop(from_index)
            self.page_order.insert(to_index, item)

    def delete_pages(self, indices):
        sorted_indices = sorted(indices, reverse=True)
        for idx in sorted_indices:
            if 0 <= idx < len(self.page_order):
                del self.page_order[idx]

    def save_pdf(self, output_path):
        output_doc = fitz.open()
        for item in self.page_order:
            original_idx = item[0]
            output_doc.insert_pdf(self.doc, from_page=original_idx, to_page=original_idx)

        output_doc.save(output_path)
        output_doc.close()

    def split_pdf(self, selected_indices, output_path):
        output_doc = fitz.open()
        for idx in selected_indices:
            if 0 <= idx < len(self.page_order):
                original_idx = self.page_order[idx][0]
                output_doc.insert_pdf(self.doc, from_page=original_idx, to_page=original_idx)

        output_doc.save(output_path)
        output_doc.close()

    def clear_session(self):
        """Clears the current session data."""
        self.doc = None
        self.filepath = None
        self.page_order = []
        self.thumbnails = {}

    def compress_pdf(self, output_path, level="medium"):
        deflate = True
        garbage = 0
        clean = False

        # Determine compression parameters
        if level == "low":
            garbage = 1
        elif level == "medium":
            garbage = 2
            deflate = True
        elif level == "high":
            garbage = 4  # Aggressive garbage collection
            deflate = True
            clean = True

        # Create a temporary subset document with the current page order
        subset_doc = fitz.open()
        for item in self.page_order:
            original_idx = item[0]
            subset_doc.insert_pdf(self.doc, from_page=original_idx, to_page=original_idx)

        # For high compression, attempt to downsample images
        if level == "high":
            try:
                # Iterate over all pages
                for page_num in range(len(subset_doc)):
                    page = subset_doc[page_num]
                    image_list = page.get_images()

                    for img in image_list:
                        xref = img[0]
                        # Skip if already processed or invalid
                        if xref <= 0:
                            continue

                        try:
                            pix = fitz.Pixmap(subset_doc, xref)
                            # Downsample if width or height > 1500
                            if pix.width > 1500 or pix.height > 1500:
                                # Check colorspace, convert to RGB if necessary (e.g. CMYK)
                                if pix.n - pix.alpha > 3:
                                    pix = fitz.Pixmap(fitz.csRGB, pix)

                                # Downsample logic: resize
                                new_pix = fitz.Pixmap(pix, pix.width // 2, pix.height // 2)

                                # Convert to JPEG stream with lower quality for compression
                                stream = new_pix.tobytes("jpeg", jpg_quality=50)

                                # Update the object stream
                                subset_doc.update_stream(xref, stream)
                                new_pix = None
                                pix = None
                        except Exception:
                            # If anything fails for an image, skip it and continue
                            continue
            except Exception:
                # If global processing fails, proceed to save what we have
                pass

        # Save with optimized parameters
        subset_doc.save(output_path, garbage=garbage, deflate=deflate, clean=clean)
        subset_doc.close()
