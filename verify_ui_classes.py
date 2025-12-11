
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow

# Mock Styles if needed, but we can import them if the environment allows
# We assume the file structure is intact.

try:
    from unimed_pdf_editor.ui.left_panel import LeftPanel
    from unimed_pdf_editor.ui.right_viewer import RightViewer
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected Error during import: {e}")
    sys.exit(1)

def verify_classes():
    app = QApplication(sys.argv)

    # Mock MainWindow
    class MockMainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.pdf_manager = None # RightViewer accesses this, but not in init_ui

    main_window = MockMainWindow()

    try:
        print("Instantiating LeftPanel...")
        left_panel = LeftPanel(main_window)
        print("LeftPanel instantiated successfully.")
    except Exception as e:
        print(f"Failed to instantiate LeftPanel: {e}")
        sys.exit(1)

    try:
        print("Instantiating RightViewer...")
        right_viewer = RightViewer(main_window)
        print("RightViewer instantiated successfully.")
    except Exception as e:
        print(f"Failed to instantiate RightViewer: {e}")
        sys.exit(1)

    print("Verification complete: Classes are syntactically correct and can be instantiated.")
    sys.exit(0)

if __name__ == "__main__":
    verify_classes()
