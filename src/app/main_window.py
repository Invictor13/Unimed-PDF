import tkinter as tk
import random

class Bubble:
    def __init__(self, canvas, width, height):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.life = random.randint(50, 200)  # Life cycle of the bubble
        self.max_life = self.life
        self.x = random.randint(0, width)
        self.y = random.randint(0, height)
        self.size = random.randint(2, 6)
        self.color_base = random.choice(["#333333", "#444444", "#555555"])
        # We simulate opacity by changing color brightness if possible, or just life
        self.item = self.canvas.create_oval(
            self.x, self.y, self.x + self.size, self.y + self.size,
            fill=self.color_base, outline=""
        )

    def update(self):
        self.life -= 1

        # Simulate fading by changing color (Tkinter doesn't support alpha on shapes easily)
        # Or just "blink" - Vaga-lume style.
        # Let's make it disappear and reappear elsewhere if life ends

        if self.life <= 0:
            self.reset()
        else:
            # Slight floating movement
            self.x += random.choice([-0.5, 0.5])
            self.y += random.choice([-0.5, 0.5])
            self.canvas.coords(self.item, self.x, self.y, self.x + self.size, self.y + self.size)

            # Simulate "glowing" or fading - rough approximation
            # For simplicity in Tkinter without complex hex math, we just reset on death.
            # But the user asked for "appearing and disappearing".
            # The life cycle handles the duration.

            # If we wanted to simulate fade in/out, we'd need to map life to hex colors.
            # Given constraints, just moving and resetting is "firefly-like" enough if small and many.

    def reset(self):
        self.canvas.delete(self.item)
        self.life = random.randint(50, 200)
        self.x = random.randint(0, self.width)
        self.y = random.randint(0, self.height)
        self.size = random.randint(2, 6)
        self.item = self.canvas.create_oval(
            self.x, self.y, self.x + self.size, self.y + self.size,
            fill=self.color_base, outline=""
        )

class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sentinela v2.1")
        self.geometry("800x600")

        # Background dark color #121212
        self.canvas_bg = "#121212"
        self.configure(bg=self.canvas_bg)

        self.canvas = tk.Canvas(self, bg=self.canvas_bg, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.bubbles = [Bubble(self.canvas, 800, 600) for _ in range(50)]

        self.animate()

    def animate(self):
        for bubble in self.bubbles:
            bubble.update()
        self.after(50, self.animate)

if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()
