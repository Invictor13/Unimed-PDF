# Unimed Branding Colors
COLOR_PRIMARY = "#009A3E"  # Verde Unimed
COLOR_SECONDARY = "#F9F9F9" # Cinza Claro
COLOR_ALERT = "#CC0000"     # Vermelho Sutil
COLOR_TEXT = "#333333"      # Cinza Escuro

STYLESHEET = f"""
    QMainWindow {{
        background-color: {COLOR_SECONDARY};
    }}

    QWidget {{
        font-family: 'Segoe UI', Arial, sans-serif;
        color: {COLOR_TEXT};
        font-size: 14px;
    }}

    /* Left Panel */
    QFrame#LeftPanel {{
        background-color: #FFFFFF;
        border-right: 1px solid #E0E0E0;
    }}

    QPushButton {{
        background-color: {COLOR_PRIMARY};
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 4px;
        font-weight: bold;
        border-bottom: 3px solid #007A30;
    }}

    QPushButton:hover {{
        background-color: #007A30;
        border-bottom: 5px solid #005F25;
        margin-top: -2px;
        margin-bottom: 2px;
    }}

    QPushButton:pressed {{
        background-color: #005F25;
        border-bottom: 0px solid transparent;
        margin-top: 3px;
        margin-bottom: 0px;
    }}

    QPushButton#DeleteButton {{
        background-color: {COLOR_ALERT};
        border-bottom: 3px solid #AA0000;
    }}

    QPushButton#DeleteButton:hover {{
        background-color: #AA0000;
        border-bottom: 5px solid #880000;
        margin-top: -2px;
        margin-bottom: 2px;
    }}

    QPushButton#DeleteButton:pressed {{
        background-color: #880000;
        border-bottom: 0px solid transparent;
        margin-top: 3px;
        margin-bottom: 0px;
    }}

    QLineEdit {{
        border: 1px solid #CCCCCC;
        border-radius: 4px;
        padding: 5px;
    }}

    /* Center Canvas */
    QScrollArea {{
        border: none;
        background-color: {COLOR_SECONDARY};
    }}

    QWidget#CanvasWidget {{
        background-color: {COLOR_SECONDARY};
    }}

    QWidget#CanvasContainer {{
        background-color: {COLOR_SECONDARY};
    }}

    /* Thumbnails */
    QLabel#ThumbnailLabel {{
        border: 1px solid #DDDDDD;
        background-color: white;
        transition: all 0.2s ease;
    }}

    QLabel#ThumbnailLabel[selected="true"] {{
        border: 3px solid {COLOR_PRIMARY};
    }}

    /* Right Viewer */
    QFrame#RightPanel {{
        background-color: {COLOR_SECONDARY};
        border-left: 1px solid #E0E0E0;
    }}

    /* Dialogs */
    QMessageBox, QInputDialog {{
        background-color: white;
    }}
    QMessageBox QLabel, QInputDialog QLabel {{
        color: {COLOR_TEXT};
    }}
    QMessageBox QPushButton, QInputDialog QPushButton {{
        background-color: {COLOR_PRIMARY};
        color: white;
        border-radius: 4px;
        padding: 6px 16px;
        min-width: 80px;
    }}
    QMessageBox QPushButton:hover, QInputDialog QPushButton:hover {{
        background-color: #007A30;
    }}
"""
