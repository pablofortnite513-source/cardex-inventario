"""
CECIF - Kardex Reactivos
Sistema de Gestión de Inventario
Prototipo funcional v1.0
"""

import tkinter as tk
import tkinter.messagebox as mb
from database import init_db_hybrid
from ui.login import LoginWindow
from ui.window_utils import maximize_window


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
    maximize_window(root)

    _install_messagebox_parent_fallback(root)
    LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
