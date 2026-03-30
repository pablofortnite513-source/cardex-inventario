"""
CECIF - Kardex Reactivos
Sistema de Gestión de Inventario
Prototipo funcional v1.0
"""

import tkinter as tk
from ui.login import LoginWindow


def main():
    root = tk.Tk()
    root.title("CECIF - Kardex Reactivos")
    root.geometry("600x400")
    
    app = LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
