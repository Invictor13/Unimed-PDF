import tkinter as tk
from tkinter import Toplevel
from PIL import Image, ImageTk
import os
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class ScreenshotEditor(Toplevel):
    def __init__(self, parent, screenshot_image_path):
        super().__init__(parent)
        self.geometry("800x600")
        self.title("Screenshot Editor")

        # Focus Aggressive Protocol
        self.lift()
        self.attributes('-topmost', True)
        self.after(200, lambda: self.attributes('-topmost', False))
        self.focus_force()

        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(fill="both", expand=True)

        # Load screenshot (mock for now)
        try:
            self.image = Image.open(screenshot_image_path)
            self.tk_image = ImageTk.PhotoImage(self.image)
            self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")
        except Exception as e:
            print(f"Error loading screenshot: {e}")

        self.current_tool = None
        self.logo_image_ref = [] # Keep references to prevent GC
        self.history = []

        # Toolbar
        toolbar = tk.Frame(self)
        toolbar.pack(side="top", fill="x")

        btn_logo = tk.Button(toolbar, text="Logo Stamp", command=lambda: self.set_tool("Logo"))
        btn_logo.pack(side="left")

        self.canvas.bind("<Button-1>", self.on_down)

    def set_tool(self, tool_name):
        self.current_tool = tool_name

    def on_down(self, event):
        if self.current_tool == "Logo":
            self.add_logo(event.x, event.y)

    def add_logo(self, x, y):
        try:
            logo_path = resource_path("assets/logo.png")
            if not os.path.exists(logo_path):
                print(f"Logo not found at {logo_path}")
                return

            pil_img = Image.open(logo_path)
            # Resize to reasonable size
            pil_img.thumbnail((150, 150))

            tk_img = ImageTk.PhotoImage(pil_img)

            # Store reference
            self.logo_image_ref.append(tk_img)

            item_id = self.canvas.create_image(x, y, image=tk_img, anchor="center")
            self.history.append(item_id)

        except Exception as e:
            print(f"Error adding logo: {e}")
