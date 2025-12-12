# Cores Institucionais Unimed
COLOR_PRIMARY = "#009A3E"   # Verde Unimed
COLOR_ALERT = "#CC0000"     # Vermelho Excluir
COLOR_DARK = "#1E1E1E"      # Fundo Escuro para Estrutura (Painel Esquerdo, Cabeçalho)
COLOR_BACKGROUND = "#F9F9F9" # Fundo Claro para Conteúdo (Canvas)
COLOR_TEXT = "#333333"      # Texto escuro para conteúdo
COLOR_TEXT_LIGHT = "white"  # Texto claro para fundo escuro

# Estilo de Botão (Flat Elegante e Estável)
BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLOR_PRIMARY};
        color: white; /* GARANTIA DE CONTRASTE ABSOLUTO */
        border: none;
        padding: 10px 10px;
        border-radius: 4px;
        font-weight: bold;
        min-height: 30px;
        font-size: 16px;
    }}
    QPushButton:hover {{
        background-color: #007A30;
        color: white;
    }}
    QPushButton:pressed {{
        background-color: #005F25;
        color: white;
    }}
    QPushButton#DeleteButton {{
        background-color: {COLOR_ALERT};
        color: white;
    }}
    QPushButton#DeleteButton:hover {{
        background-color: #AA0000;
        color: white;
    }}
    QPushButton#DeleteButton:pressed {{
        background-color: #880000;
        color: white;
    }}
"""

# Estilos Gerais (MANTIDOS)
STYLESHEET = f"""
    QMainWindow {{
        background-color: {COLOR_DARK};
    }}
    QWidget {{
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 14px;
        color: {COLOR_TEXT};
    }}

    /* Cabeçalho e Painel Lateral (Dark Theme) */
    QFrame#Header, QWidget#LeftPanel {{
        background-color: {COLOR_DARK};
        color: {COLOR_TEXT_LIGHT};
    }}

    /* Input field no Dark Panel */
    QLineEdit {{
        border: 1px solid #666666;
        background-color: #333333;
        color: {COLOR_TEXT_LIGHT};
        border-radius: 4px;
        padding: 5px;
        font-size: 14px;
    }}

    /* Center Canvas (Content Area - Light Theme) */
    QScrollArea {{
        border: none;
        background-color: {COLOR_BACKGROUND};
    }}
    QWidget#CanvasContainer {{
        background-color: {COLOR_BACKGROUND};
    }}

    /* Divisor de PDFs */
    QLabel#FileHeader {{
        background-color: white;
        color: {COLOR_PRIMARY};
        font-weight: bold;
        padding: 8px 15px;
        border-left: 5px solid {COLOR_PRIMARY};
        border-radius: 4px;
        font-size: 14px;
    }}

    /* Thumbnails */
    QLabel#ThumbnailLabel {{
        border: 1px solid #DDDDDD;
        background-color: white;
    }}

    QLabel#ThumbnailLabel[selected="true"] {{
        border: 3px solid {COLOR_PRIMARY};
    }}

    /* Right Viewer (Light Theme) */
    QFrame#RightViewer {{
        background-color: white;
    }}

    /* Dialogos - Corrigindo o problema de caixa preta */
    QMessageBox, QInputDialog {{
        background-color: white;
    }}
    QMessageBox QLabel, QInputDialog QLabel {{
        color: {COLOR_TEXT};
        background-color: transparent;
    }}

    {BUTTON_STYLE}
"""
