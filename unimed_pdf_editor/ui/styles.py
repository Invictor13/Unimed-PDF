# Cores Institucionais Unimed
COLOR_PRIMARY = "#009A3E"
COLOR_SECONDARY = "#F9F9F9"
COLOR_ALERT = "#CC0000"
COLOR_TEXT = "#333333"

# Estilo de Botão com Efeito de Profundidade (Simulado)
BUTTON_STYLE = f"""
    QPushButton {{
        background-color: white;
        color: {COLOR_PRIMARY};
        border: 2px solid {COLOR_PRIMARY};
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2px;
    }}
    QPushButton:hover {{
        background-color: {COLOR_PRIMARY};
        color: white;
        border: 2px solid {COLOR_PRIMARY};
    }}
    QPushButton:pressed {{
        margin-top: 2px;
        margin-bottom: 0px;
        background-color: #007A30;
        border-color: #007A30;
    }}
"""

# Tooltip Style
TOOLTIP_STYLE = """
    QToolTip {
        border: 1px solid #CCCCCC;
        background-color: #FFFFEE;
        color: #333333;
        padding: 5px;
        opacity: 200;
    }
"""

# Estilos Gerais
STYLESHEET = f"""
    QMainWindow {{
        background-color: white;
    }}
    QWidget {{
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 14px;
        color: {COLOR_TEXT};
    }}
    QScrollBar:vertical {{
        border: none;
        background: #F0F0F0;
        width: 10px;
        margin: 0px 0px 0px 0px;
    }}
    QScrollBar::handle:vertical {{
        background: #CCCCCC;
        min-height: 20px;
        border-radius: 5px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    {BUTTON_STYLE}
    {TOOLTIP_STYLE}
"""
