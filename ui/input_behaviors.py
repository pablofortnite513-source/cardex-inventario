import tkinter as tk
from tkinter import ttk
from typing import Callable


def bind_uppercase(target: tk.StringVar | tk.Text) -> None:
    """Aplica normalizacion a mayusculas para StringVar o Text."""
    if isinstance(target, tk.StringVar):
        bind_uppercase_var(target)
        return
    if isinstance(target, tk.Text):
        bind_uppercase_text(target)
        return
    raise TypeError("bind_uppercase solo soporta tk.StringVar o tk.Text")


def bind_uppercase_var(var: tk.StringVar) -> None:
    """Convierte un StringVar a mayusculas en tiempo real."""

    def _normalize(*_args) -> None:
        current = var.get()
        upper = current.upper()
        if current != upper:
            var.set(upper)

    var.trace_add("write", _normalize)


def bind_uppercase_text(widget: tk.Text) -> None:
    """Convierte el contenido de un Text a mayusculas conservando cursor y scroll."""

    def _normalize(_event=None) -> None:
        current = widget.get("1.0", "end-1c")
        upper = current.upper()
        if current == upper:
            return

        insert_idx = widget.index("insert")
        yview = widget.yview()
        widget.delete("1.0", tk.END)
        widget.insert("1.0", upper)
        try:
            widget.mark_set("insert", insert_idx)
        except tk.TclError:
            pass
        if yview:
            widget.yview_moveto(yview[0])

    widget.bind("<KeyRelease>", _normalize, add="+")
    widget.bind("<<Paste>>", lambda _e: widget.after_idle(_normalize), add="+")


def bind_code_combo_autofill(
    combo: ttk.Combobox,
    get_source: Callable[[], list[str]],
    on_exact_match: Callable[[str], None],
    on_clear: Callable[[], None] | None = None,
    clear_invalid_on_focus_out: bool = True,
) -> None:
    """Autocompleta por codigo exacto con lista completa (filtro por desplazamiento)."""

    nav_keys = {"Up", "Down", "Page_Up", "Page_Down", "Tab", "Shift_L", "Shift_R", "Control_L", "Control_R"}

    def _source() -> list[str]:
        return [str(v).strip() for v in get_source() if str(v).strip()]

    def _exact(text: str, source: list[str]) -> str | None:
        target = text.strip().lower()
        if not target:
            return None
        for value in source:
            if value.lower() == target:
                return value
        return None

    def _is_dropdown_open() -> bool:
        try:
            popdown = combo.tk.call("ttk::combobox::PopdownWindow", str(combo))
            popup = combo.nametowidget(popdown)
            return bool(popup.winfo_ismapped())
        except Exception:
            return False

    def _sync_values() -> tuple[str, list[str], str | None]:
        source = _source()
        typed = combo.get().strip()
        combo["values"] = source
        return typed, source, _exact(typed, source)

    def _on_key_release(event: tk.Event) -> None:
        if event.keysym in nav_keys:
            return

        typed, _, exact = _sync_values()
        if not typed:
            if on_clear is not None:
                on_clear()
            return

        if exact is not None:
            if combo.get().strip() != exact:
                combo.set(exact)
            on_exact_match(exact)
        elif on_clear is not None:
            on_clear()

        values = combo.cget("values")
        if values and not _is_dropdown_open():
            try:
                combo.event_generate("<Down>")
            except tk.TclError:
                pass

    def _on_focus_out(_event: tk.Event) -> None:
        typed, source, exact = _sync_values()
        combo["values"] = source
        if not typed:
            if on_clear is not None:
                on_clear()
            return
        if exact is not None:
            combo.set(exact)
            on_exact_match(exact)
            return
        if clear_invalid_on_focus_out:
            combo.set("")
            if on_clear is not None:
                on_clear()
            return
        if on_clear is not None:
            on_clear()

    def _on_selected(_event: tk.Event) -> None:
        source = _source()
        exact = _exact(combo.get(), source)
        if exact is not None:
            on_exact_match(exact)
            combo["values"] = source

    combo.bind("<KeyRelease>", _on_key_release, add="+")
    combo.bind("<FocusOut>", _on_focus_out, add="+")
    combo.bind("<<ComboboxSelected>>", _on_selected, add="+")
