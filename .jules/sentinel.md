## 2024-05-23 - [Privacy Leak in OCR Workflow]
**Vulnerability:** The `run_ocr` function passed the original file path (`self.pdf_manager.filepath`) to the OCR engine, ignoring any modifications made in the current session (such as deleting pages containing sensitive information).
**Learning:** In document processing applications, "source of truth" ambiguity (file on disk vs. in-memory state) can lead to data leaks. Users expect "What You See Is What You Get".
**Prevention:** Always ensure that downstream processes (like OCR or Export) operate on the *current* state of the data. Use temporary files or in-memory streams to pass the modified state to external processors if they don't support the internal data structure directly.
