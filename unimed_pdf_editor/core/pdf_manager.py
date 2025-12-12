import sys
import os
import uuid
import fitz  # PyMuPDF
from PIL import Image
import io
import copy

class PDFManager:
    def __init__(self):
        self.doc = None  # Current PyMuPDF document (Physical Source)
        self.filepath = None
        # Page Order: list of (original_doc_page_index, file_name, file_id, rotation)
        self.page_order = []
        self.thumbnails = {} # Cache: key=(original_index, rotation) -> value=img_data
        self.fitz = fitz

        # Undo/Redo Stacks
        self.history_stack = []
        self.redo_stack = []
        self._is_undoing = False # Flag to prevent pushing to stack during undo/redo

    def _save_state(self):
        """Saves current state to history stack."""
        if self._is_undoing:
            return
        # Deep copy of page_order is enough as it defines the state
        self.history_stack.append(copy.deepcopy(self.page_order))
        self.redo_stack.clear() # Clear redo on new action

        # Limit stack size to prevent memory issues (e.g., 50 actions)
        if len(self.history_stack) > 50:
            self.history_stack.pop(0)

    def undo(self):
        if not self.history_stack:
            return False

        self._is_undoing = True
        try:
            # Save current state to redo stack
            self.redo_stack.append(copy.deepcopy(self.page_order))
            # Pop previous state
            self.page_order = self.history_stack.pop()
            return True
        finally:
            self._is_undoing = False

    def redo(self):
        if not self.redo_stack:
            return False

        self._is_undoing = True
        try:
            self.history_stack.append(copy.deepcopy(self.page_order))
            self.page_order = self.redo_stack.pop()
            return True
        finally:
            self._is_undoing = False

    def load_pdf(self, input_data):
        self._save_state()
        filepaths = input_data if isinstance(input_data, list) else [input_data]
        total_loaded = 0

        for filepath in filepaths:
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

                new_pages_count = len(new_doc)

                # Add new page indices with 0 rotation default
                for i in range(new_pages_count):
                    self.page_order.append((current_count + i, file_name, file_id, 0))

                total_loaded += 1

            except Exception as e:
                print(f"Error loading PDF {filepath}: {e}")

        return len(self.page_order)

    def rotate_page(self, page_index, angle=90):
        if 0 <= page_index < len(self.page_order):
            self._save_state()
            idx, fname, fid, rot = self.page_order[page_index]
            new_rot = (rot + angle) % 360
            self.page_order[page_index] = (idx, fname, fid, new_rot)

    def get_page_count(self):
        return len(self.page_order)

    def get_page_info(self, page_index):
        if 0 <= page_index < len(self.page_order):
            idx, fname, fid, rot = self.page_order[page_index]
            return {'original_index': idx, 'file_name': fname, 'file_id': fid, 'rotation': rot}
        return None

    def get_files_in_order(self):
        files = []
        seen_ids = set()
        for _, fname, fid, _ in self.page_order:
            if fid not in seen_ids:
                seen_ids.add(fid)
                count = sum(1 for item in self.page_order if item[2] == fid)
                files.append({'file_id': fid, 'file_name': fname, 'page_count': count})
        return files

    def reorder_file(self, file_id, new_index):
        self._save_state()
        current_files = self.get_files_in_order()
        if not (0 <= new_index < len(current_files)):
            return

        target_file = next((f for f in current_files if f['file_id'] == file_id), None)
        if not target_file:
            return

        current_files_list = [f['file_id'] for f in current_files]
        current_idx = current_files_list.index(file_id)
        current_files_list.pop(current_idx)
        current_files_list.insert(new_index, file_id)

        new_page_order = []
        pages_by_file = {}
        for item in self.page_order:
            fid = item[2]
            if fid not in pages_by_file:
                pages_by_file[fid] = []
            pages_by_file[fid].append(item)

        for fid in current_files_list:
            if fid in pages_by_file:
                new_page_order.extend(pages_by_file[fid])

        self.page_order = new_page_order

    def get_thumbnail(self, page_index, scale=0.3):
        if not (0 <= page_index < len(self.page_order)):
             return None

        original_index, _, _, rotation = self.page_order[page_index]

        # Cache key includes rotation
        cache_key = (original_index, rotation)

        if cache_key in self.thumbnails and scale == 0.3:
            return self.thumbnails[cache_key]

        page = self.doc.load_page(original_index)

        # Apply rotation
        page.set_rotation(rotation)

        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)

        img_data = {
            "width": pix.width,
            "height": pix.height,
            "stride": pix.stride,
            "samples": bytes(pix.samples),
            "format": "RGB888"
        }

        if scale == 0.3:
            self.thumbnails[cache_key] = img_data
        return img_data

    def get_page_image(self, page_index, scale=2.0):
        original_index, _, _, rotation = self.page_order[page_index]
        page = self.doc.load_page(original_index)
        page.set_rotation(rotation)
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        return pix.tobytes("ppm")

    def move_page(self, from_index, to_index):
        if 0 <= from_index < len(self.page_order) and 0 <= to_index < len(self.page_order):
            self._save_state()
            item = self.page_order.pop(from_index)
            self.page_order.insert(to_index, item)

    def delete_pages(self, indices):
        """Soft delete: Remove from page_order only."""
        if not indices:
            return

        self._save_state()

        # Sort desc to delete safely
        indices = sorted(indices, reverse=True)
        for idx in indices:
            if 0 <= idx < len(self.page_order):
                del self.page_order[idx]

    def save_pdf(self, output_path):
        output_doc = fitz.open()
        for item in self.page_order:
            original_idx, _, _, rotation = item

            # We must load the page, rotate it, and then insert?
            # insert_pdf copies the page. If we want to save rotation, we should ensure the source is rotated
            # OR we use insert_pdf with rotation logic.
            # fitz.Document.insert_pdf does NOT have a rotation param per page easily (it merges docs).
            # Easier: Create a temp single-page doc, rotate it, then insert.
            # OR: simply set rotation on self.doc page before inserting (but that modifies self.doc state? Yes).
            # But we are allowed to modify self.doc state as long as we reset it? No, that's risky.

            # Better: self.doc.insert_pdf copies the page stream.
            # Rotation is a page attribute.

            output_doc.insert_pdf(self.doc, from_page=original_idx, to_page=original_idx, rotate=rotation)

        output_doc.save(output_path)
        output_doc.close()

    def split_pdf(self, selected_indices, output_path):
        output_doc = fitz.open()
        for idx in selected_indices:
            if 0 <= idx < len(self.page_order):
                original_idx, _, _, rotation = self.page_order[idx]
                output_doc.insert_pdf(self.doc, from_page=original_idx, to_page=original_idx, rotate=rotation)

        output_doc.save(output_path)
        output_doc.close()

    def clear_session(self):
        self.doc = None
        self.filepath = None
        self.page_order = []
        self.thumbnails = {}
        self.history_stack = []
        self.redo_stack = []

    def compress_pdf(self, output_path, level="medium"):
        deflate = True
        garbage = 0
        clean = False

        if level == "low":
            garbage = 1
        elif level == "medium":
            garbage = 2
            deflate = True
        elif level == "high":
            garbage = 4
            deflate = True
            clean = True

        subset_doc = fitz.open()
        for item in self.page_order:
            original_idx, _, _, rotation = item
            subset_doc.insert_pdf(self.doc, from_page=original_idx, to_page=original_idx, rotate=rotation)

        if level == "high":
            processed_xrefs = set()
            try:
                for page_num in range(len(subset_doc)):
                    page = subset_doc[page_num]
                    image_list = page.get_images()

                    for img in image_list:
                        xref = img[0]
                        if xref <= 0 or xref in processed_xrefs:
                            continue
                        processed_xrefs.add(xref)

                        try:
                            pix = fitz.Pixmap(subset_doc, xref)
                            if pix.n - pix.alpha > 3:
                                pix = fitz.Pixmap(fitz.csRGB, pix)
                            if pix.alpha:
                                pix = fitz.Pixmap(pix, 0)

                            max_dim = 1500
                            should_downsample = pix.width > max_dim or pix.height > max_dim

                            if should_downsample:
                                scale = max_dim / max(pix.width, pix.height)
                                new_width = int(pix.width * scale)
                                new_height = int(pix.height * scale)
                                new_pix = fitz.Pixmap(pix, new_width, new_height)
                            else:
                                new_pix = fitz.Pixmap(pix)

                            stream = new_pix.tobytes("jpeg", jpg_quality=50)

                            subset_doc.update_stream(xref, stream, compress=False)
                            subset_doc.xref_set_key(xref, "Width", str(new_pix.width))
                            subset_doc.xref_set_key(xref, "Height", str(new_pix.height))
                            subset_doc.xref_set_key(xref, "Filter", "/DCTDecode")
                            subset_doc.xref_set_key(xref, "BitsPerComponent", "8")
                            if new_pix.n <= 2:
                                subset_doc.xref_set_key(xref, "ColorSpace", "/DeviceGray")
                            else:
                                subset_doc.xref_set_key(xref, "ColorSpace", "/DeviceRGB")
                        except Exception as e:
                            print(f"Failed to compress image xref {xref}: {e}")
                            continue
            except Exception as e:
                pass

        subset_doc.save(output_path, garbage=garbage, deflate=deflate, clean=clean)
        subset_doc.close()
