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
    }}

    QPushButton:hover {{
        background-color: #007A30;
    }}

    QPushButton:pressed {{
        background-color: #005F25;
    }}

    QPushButton#DeleteButton {{
        background-color: {COLOR_ALERT};
    }}

    QPushButton#DeleteButton:hover {{
        background-color: #AA0000;
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

    /* Thumbnails */
    QLabel#ThumbnailLabel {{
        border: 1px solid #DDDDDD;
        background-color: white;
    }}

    QLabel#ThumbnailLabel[selected="true"] {{
        border: 3px solid {COLOR_PRIMARY};
    }}

    /* Right Viewer */
    QFrame#RightPanel {{
        background-color: #FFFFFF;
        border-left: 1px solid #E0E0E0;
    }}

"""
