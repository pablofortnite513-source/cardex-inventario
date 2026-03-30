"""Compatibilidad retroactiva para importaciones antiguas.

El formulario de entradas ahora vive en ui/entradas.py.
"""

from ui.entradas import EntryFormWindow

__all__ = ["EntryFormWindow"]
