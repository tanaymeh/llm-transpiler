import tkinter as tk

class MouseColorChanger(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("500x500+250+125")
        self.bind("<Button-1>", self.change_color_left)  # Left mouse button
        self.bind("<Button-2>", self.change_color_middle)  # Middle mouse button
        self.bind("<Button-3>", self.change_color_right)  # Right mouse button
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def change_color_left(self, event):
        self.configure(bg='red')

    def change_color_middle(self, event):
        self.configure(bg='green')

    def change_color_right(self, event):
        self.configure(bg='blue')

    def on_closing(self):
        self.destroy()

if __name__ == "__main__":
    app = MouseColorChanger()
    app.mainloop()