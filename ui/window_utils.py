import tkinter as tk


def maximize_window(window: tk.Misc) -> None:
    """Maximize a Tk window using the best available method for the platform."""
    try:
        window.state("zoomed")
        return
    except tk.TclError:
        pass

    try:
        window.attributes("-zoomed", True)
    except tk.TclError:
        pass
