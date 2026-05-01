"""Estilos visuales reutilizables — focus, hover, asteriscos obligatorios."""

import importlib
import tkinter as tk
from tkinter import ttk

from config.config import COLORS, IMAGES_PATH

# ── Colores principales ──────────────────────────────────────
PINK = "#f48fb1"              # Rosa suave (focus / selección)
PINK_LIGHT = "#fce4ec"        # Rosa muy claro (highlight de fondo)
BORDER_NORMAL = "#cccccc"     # Borde normal
BORDER_FOCUS = PINK           # Borde al enfocar
ASTERISK_COLOR = "#e53935"    # Rojo para asterisco obligatorio


def _attach_tooltip(widget: tk.Widget, text: str) -> None:
    """Tooltip simple para widgets pequeños (ej. asterisco obligatorio)."""
    if not text:
        return

    tooltip_win: dict[str, tk.Toplevel | None] = {"win": None}

    def _show(event: tk.Event) -> None:
        if tooltip_win["win"] is not None and tooltip_win["win"].winfo_exists():
            return
        top = tk.Toplevel(widget)
        top.overrideredirect(True)
        top.attributes("-topmost", True)
        tk.Label(
            top,
            text=text,
            bg="#FFF8C6",
            fg="#222222",
            relief="solid",
            bd=1,
            padx=6,
            pady=4,
            font=("Segoe UI", 9),
        ).pack()
        top.geometry(f"+{event.x_root + 12}+{event.y_root + 10}")
        tooltip_win["win"] = top

    def _hide(_event: tk.Event | None = None) -> None:
        win = tooltip_win["win"]
        if win is not None and win.winfo_exists():
            win.destroy()
        tooltip_win["win"] = None

    widget.bind("<Enter>", _show, add="+")
    widget.bind("<Leave>", _hide, add="+")
    widget.bind("<Button-1>", _hide, add="+")


def apply_focus_bindings(widget: tk.Widget) -> None:
    """Agrega efectos de focus (borde rosa) a un Entry o Text."""
    # Excluir ttk.Entry (DateEntry internos, etc.)
    if isinstance(widget, ttk.Entry):
        return
    if isinstance(widget, tk.Entry):
        widget.configure(highlightthickness=1, highlightcolor=BORDER_FOCUS, highlightbackground=BORDER_NORMAL)
        widget.bind("<FocusIn>", lambda e: _on_focus_in(e.widget), add="+")
        widget.bind("<FocusOut>", lambda e: _on_focus_out(e.widget), add="+")
    elif isinstance(widget, tk.Text):
        widget.configure(highlightthickness=1, highlightcolor=BORDER_FOCUS, highlightbackground=BORDER_NORMAL)
        widget.bind("<FocusIn>", lambda e: _on_focus_in(e.widget), add="+")
        widget.bind("<FocusOut>", lambda e: _on_focus_out(e.widget), add="+")


def _on_focus_in(w: tk.Widget) -> None:
    try:
        w.configure(highlightbackground=BORDER_FOCUS, highlightcolor=BORDER_FOCUS)
    except tk.TclError:
        pass


def _on_focus_out(w: tk.Widget) -> None:
    try:
        w.configure(highlightbackground=BORDER_NORMAL, highlightcolor=BORDER_FOCUS)
    except tk.TclError:
        pass


def setup_ttk_styles(root: tk.Widget) -> None:
    """Configura estilos ttk para Combobox y Checkbutton con la paleta rosa."""
    style = ttk.Style(root)

    # Combobox con borde de selección rosa
    style.map(
        "TCombobox",
        fieldbackground=[("focus", PINK_LIGHT), ("!focus", "white")],
        bordercolor=[("focus", PINK), ("!focus", BORDER_NORMAL)],
        lightcolor=[("focus", PINK)],
        darkcolor=[("focus", PINK)],
    )

    # Checkbutton con indicador rosa
    style.configure("Pink.TCheckbutton", indicatorcolor=PINK)
    style.map(
        "Pink.TCheckbutton",
        indicatorcolor=[("selected", PINK), ("!selected", "white")],
    )

    # Treeview con selección visible (fondo primario y texto blanco)
    style.configure(
        "Treeview",
        background="white",
        foreground="black",
        rowheight=25,
        fieldbackground="white",
    )
    style.map(
        "Treeview",
        background=[("selected", COLORS["primary"])],
        foreground=[("selected", "white")],
    )


def apply_hover_button(btn: tk.Button, normal_bg: str | None = None) -> None:
    """Agrega hover sutil a un botón tk (oscurecer ligeramente)."""
    if normal_bg is None:
        normal_bg = btn.cget("bg")
    hover_bg = _darken(normal_bg, 0.12)
    btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg), add="+")
    btn.bind("<Leave>", lambda e: btn.configure(bg=normal_bg), add="+")


def make_required_label(parent: tk.Widget, text: str, **kwargs) -> tk.Label:
    """Crea un Label con asterisco rojo para campo obligatorio."""
    frame = tk.Frame(parent, bg=kwargs.get("bg", "white"))
    tk.Label(frame, text=text, bg=kwargs.get("bg", "white"),
             font=kwargs.get("font")).pack(side="left")
    star = tk.Label(frame, text=" *", fg=ASTERISK_COLOR, bg=kwargs.get("bg", "white"),
                    font=kwargs.get("font"), cursor="question_arrow")
    star.pack(side="left")
    _attach_tooltip(star, "Campo obligatorio")
    return frame


def style_checkbutton(cb: tk.Checkbutton) -> None:
    """Aplica colores rosa al Checkbutton de tk."""
    cb.configure(
        selectcolor=PINK,
        activebackground=PINK_LIGHT,
    )


def apply_styles_to_window(window: tk.Widget) -> None:
    """Recorre todos los widgets de una ventana y aplica estilos de focus/hover."""
    setup_ttk_styles(window)
    _apply_recursive(window)


def _apply_recursive(widget: tk.Widget) -> None:
    """Recorre recursivamente y aplica focus a Entry/Text, hover a Button, estilo a Checkbutton."""
    # Saltar widgets ttk.Entry (DateEntry internos, etc.)
    if isinstance(widget, ttk.Entry):
        pass
    elif isinstance(widget, tk.Entry):
        apply_focus_bindings(widget)
    elif isinstance(widget, tk.Text):
        apply_focus_bindings(widget)
    elif isinstance(widget, tk.Button):
        bg = widget.cget("bg")
        if bg not in ("white", "#F0F0F0", "SystemButtonFace"):
            apply_hover_button(widget, bg)
    elif isinstance(widget, tk.Checkbutton):
        style_checkbutton(widget)

    for child in widget.winfo_children():
        _apply_recursive(child)


def _darken(hex_color: str, factor: float = 0.12) -> str:
    """Oscurece un color hex en un porcentaje dado."""
    try:
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            return f"#{hex_color}"
        r = max(0, int(hex_color[0:2], 16) - int(255 * factor))
        g = max(0, int(hex_color[2:4], 16) - int(255 * factor))
        b = max(0, int(hex_color[4:6], 16) - int(255 * factor))
        return f"#{r:02x}{g:02x}{b:02x}"
    except (ValueError, TypeError):
        return hex_color


# ── Header con logo ──────────────────────────────────────────

_header_logos: list = []  # Mantener referencia para evitar garbage collection


def build_header(parent: tk.Widget, title: str, logo_height: int = 45) -> tk.Frame:
    """Crea la barra rosa con título a la izquierda y logo CECIF a la derecha."""
    header = tk.Frame(parent, bg=COLORS["primary"])
    header.pack(fill="x", pady=(0, 10))

    tk.Label(
        header,
        text=title,
        bg=COLORS["primary"],
        fg="white",
        font=("Segoe UI", 18, "bold"),
        padx=14,
        pady=8,
    ).pack(side="left", fill="x", expand=True)

    logo_path = IMAGES_PATH / "imgLogocecif.png"
    if logo_path.exists():
        try:
            image_mod = importlib.import_module("PIL.Image")
            image_tk_mod = importlib.import_module("PIL.ImageTk")
            img = image_mod.open(logo_path)
            ratio = logo_height / img.height
            new_w = int(img.width * ratio)
            resampling = getattr(image_mod, "Resampling", None)
            method = resampling.LANCZOS if resampling else image_mod.LANCZOS
            img = img.resize((new_w, logo_height), method)
            logo_tk = image_tk_mod.PhotoImage(img)
            _header_logos.append(logo_tk)
            tk.Label(header, image=logo_tk, bg=COLORS["primary"]).pack(
                side="right", padx=(8, 12), pady=4,
            )
        except Exception:
            pass

    return header
