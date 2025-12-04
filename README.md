# 📄 Editor PDF Unimed (Projeto Braço Direito)

Este é um editor de PDF moderno construído em Python (PyQt6) com foco em UX (Experiência do Usuário), seguindo a paleta de cores da Unimed.

## ✨ Características Principais

* **Interface Fluida:** Layout em três colunas (Painel de Funções, Canvas de Miniaturas, Visualizador Ampliado).
* **UX Avançada:** Seleção de páginas por **Shift-Click** e input de faixas (ex: `1-5, 8`).
* **Reordenação Fácil:** Alterna ordem das páginas via **Drag-and-Drop**.
* **Visualização Detalhada:** Zoom Contextual (Floating Card) ao passar o mouse sobre as miniaturas e Visualizador Ampliado com navegação e botões de **Rotacionar/Excluir**.
* **Funções Core:** Unificar, Separar, Compactar e Excluir Páginas.

## ⚙️ Funcionalidade de OCR

O recurso **Tornar Pesquisável (OCR)** é implementado usando **`pytesseract`**.

**Nota sobre Distribuição:**
Para garantir que o OCR funcione em uma aplicação distribuída (empacotada com PyInstaller), a classe `OCREngine` contém uma lógica especial para localizar o binário do **Tesseract** dentro do pacote `sys._MEIPASS`. Isso elimina a necessidade do usuário final instalar o Tesseract separadamente.

## 🚀 Como Executar

1.  **Instale as dependências:** `pip install -r requirements.txt`
2.  **Instale o Tesseract:** O executável do Tesseract deve estar instalado no sistema para o modo de desenvolvimento.
3.  **Execute:** `python -m unimed_pdf_editor.main`
