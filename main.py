"""
CECIF - Kardex Reactivos
Sistema de Gestión de Inventario
Prototipo funcional v1.0
"""

import tkinter as tk
import tkinter.messagebox as mb
from database import init_db_hybrid
from config.config import IMAGES_PATH
from ui.login import LoginWindow


def _apply_app_icon(root: tk.Tk) -> None:
    """Aplica el ícono del matraz a la ventana (y por lo tanto a la barra de tareas)."""
    icon_path = IMAGES_PATH / "kardex_reactivos.ico"
    if not icon_path.exists():
        return
    try:
        root.iconbitmap(default=str(icon_path))
    except Exception:
        pass


def _install_messagebox_parent_fallback(root: tk.Tk) -> None:
    """Attach message dialogs to the active window when parent is omitted."""

    def _ensure_parent(kwargs: dict) -> None:
        if kwargs.get("parent") is not None:
            return
        try:
            focused = root.focus_get()
            if focused is not None and focused.winfo_exists():
                kwargs["parent"] = focused.winfo_toplevel()
                return
        except Exception:
            pass
        kwargs["parent"] = root

    def _wrap(func):
        def _wrapped(*args, **kwargs):
            _ensure_parent(kwargs)
            return func(*args, **kwargs)

        return _wrapped

    mb.showerror = _wrap(mb.showerror)
    mb.showwarning = _wrap(mb.showwarning)
    mb.showinfo = _wrap(mb.showinfo)
    mb.askyesno = _wrap(mb.askyesno)
    mb.askokcancel = _wrap(mb.askokcancel)
    mb.askretrycancel = _wrap(mb.askretrycancel)
    mb.askquestion = _wrap(mb.askquestion)


def main():
    init_db_hybrid()

    root = tk.Tk()
    root.title("CECIF - Kardex Reactivos")
    root.geometry("600x400")
    _apply_app_icon(root)

    _install_messagebox_parent_fallback(root)
    app = LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
