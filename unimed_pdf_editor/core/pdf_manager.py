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
        self.fitz = fitz # Export fitz module for consumers

    def load_pdf(self, filepath):
        try:
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
        except Exception as e:
            print(f"Error loading PDF: {e}")
            return 0

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

    def get_files_in_order(self):
        """Returns a list of unique files in their current visual order.
           Returns: List of dicts {'file_id': str, 'file_name': str, 'page_count': int}
        """
        files = []
        seen_ids = set()

        # Determine order based on the first occurrence of each file_id in page_order
        # This assumes we want to present files based on where they start.
        # If pages are mixed, this will still extract unique files.
        for _, fname, fid in self.page_order:
            if fid not in seen_ids:
                seen_ids.add(fid)
                # Count pages for this file
                count = sum(1 for item in self.page_order if item[2] == fid)
                files.append({'file_id': fid, 'file_name': fname, 'page_count': count})

        return files

    def reorder_file(self, file_id, new_index):
        """Moves all pages associated with file_id to a position corresponding to new_index in the file list."""
        current_files = self.get_files_in_order()
        if not (0 <= new_index < len(current_files)):
            return

        # Identify the file being moved
        target_file = next((f for f in current_files if f['file_id'] == file_id), None)
        if not target_file:
            return

        # Remove from current list and insert at new index to get target file order
        current_files_list = [f['file_id'] for f in current_files]
        current_idx = current_files_list.index(file_id)
        current_files_list.pop(current_idx)
        current_files_list.insert(new_index, file_id)

        # Reconstruct page_order based on new file order
        new_page_order = []

        # Group current pages by file_id
        pages_by_file = {}
        for item in self.page_order:
            fid = item[2]
            if fid not in pages_by_file:
                pages_by_file[fid] = []
            pages_by_file[fid].append(item)

        # Append pages in the new file order
        for fid in current_files_list:
            if fid in pages_by_file:
                new_page_order.extend(pages_by_file[fid])

        self.page_order = new_page_order

    def get_thumbnail(self, page_index, scale=0.3):
        original_index, _, _ = self.page_order[page_index]

        if original_index in self.thumbnails and scale == 0.3:
            return self.thumbnails[original_index]

        page = self.doc.load_page(original_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))

        img_data = pix.tobytes("ppm")
        if scale == 0.3:
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
            processed_xrefs = set()
            try:
                # Iterate over all pages
                for page_num in range(len(subset_doc)):
                    page = subset_doc[page_num]
                    image_list = page.get_images()

                    for img in image_list:
                        xref = img[0]
                        # Skip if already processed or invalid
                        if xref <= 0 or xref in processed_xrefs:
                            continue

                        processed_xrefs.add(xref)

                        try:
                            # Use fitz.Pixmap(doc, xref) which is the most reliable way to get image content
                            pix = fitz.Pixmap(subset_doc, xref)

                            # Check colorspace, convert to RGB if necessary (e.g. CMYK) to allow JPEG conversion
                            if pix.n - pix.alpha > 3:
                                pix = fitz.Pixmap(fitz.csRGB, pix)

                            # Target DPI logic: approx 150 DPI
                            # Assuming standard A4 (approx 600x840 points), 150 DPI is approx 1240x1754 pixels
                            # We set a max dimension safe limit of 1500px to ensure reduction
                            max_dim = 1500

                            # Optimization strategy
                            should_downsample = pix.width > max_dim or pix.height > max_dim

                            # Always attempt to compress if it's High mode, even if dimensions are okay.
                            # We create a new pixmap to ensure we have control over the data

                            # NOTE: Fixed the issue where new_pix might be garbage collected prematurely or incorrect scale used
                            if should_downsample:
                                scale = max_dim / max(pix.width, pix.height)
                                new_width = int(pix.width * scale)
                                new_height = int(pix.height * scale)
                                new_pix = fitz.Pixmap(pix, new_width, new_height)
                            else:
                                new_pix = fitz.Pixmap(pix) # Copy

                            # Convert to JPEG stream with high compression (Quality 30)
                            stream = new_pix.tobytes("jpeg", jpg_quality=30)

                            # Update the object stream and essential dictionary keys
                            # Use compress=False because we are providing already compressed JPEG data
                            subset_doc.update_stream(xref, stream, compress=False)

                            # Update metadata to reflect new dimensions and JPEG encoding
                            # Note: Values must be strings for xref_set_key
                            subset_doc.xref_set_key(xref, "Width", str(new_pix.width))
                            subset_doc.xref_set_key(xref, "Height", str(new_pix.height))
                            subset_doc.xref_set_key(xref, "Filter", "/DCTDecode")
                            subset_doc.xref_set_key(xref, "BitsPerComponent", "8")

                            # Update ColorSpace based on new pixmap
                            if new_pix.n <= 2: # Grayscale or Mono
                                subset_doc.xref_set_key(xref, "ColorSpace", "/DeviceGray")
                            else:
                                subset_doc.xref_set_key(xref, "ColorSpace", "/DeviceRGB")

                            new_pix = None
                            pix = None
                        except Exception as e:
                            print(f"Failed to compress image xref {xref}: {e}")
                            # If anything fails for an image, skip it and continue
                            continue
            except Exception as e:
                print(f"Global compression error: {e}")
                # If global processing fails, proceed to save what we have
                pass

        # Save with optimized parameters
        subset_doc.save(output_path, garbage=garbage, deflate=deflate, clean=clean)
        subset_doc.close()
