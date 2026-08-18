# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

CECIF - Kardex Reactivos: a Tkinter desktop app (Spanish-language) for tracking chemical-reagent
inventory (entradas/salidas/stock/vigencias) for a lab. Single-user desktop app, no web server.

## Commands

```bash
# Setup (Windows)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Run
python main.py
```

There is no test suite, linter, or build step configured in this repo.

## Architecture

### Data layer: `database.py` -> `utils/data_handler.py` -> UI

- **`database.py`** is the only place that speaks SQL. It supports two engines, selected in
  `config.json` (`"motor": "sqlite"` or `"sqlserver"`):
  - SQLite (default, local dev) via `sqlite3`.
  - SQL Server (production) via `pyodbc`, only loaded if installed.
  - `init_db_hybrid()` creates/migrates the schema for whichever engine is configured and is
    idempotent (safe to call on every startup — `main.py` does this before opening any window).
  - Schema creation and column-migration logic is duplicated per engine (`_init_schema` /
    `_migrar_schema` for SQLite, `_init_schema_sqlserver` / `_migrar_schema_sqlserver` for SQL
    Server) because DDL syntax differs (`AUTOINCREMENT` vs `IDENTITY`, etc). When changing the
    schema, update **both** paths and add the new column(s) to the corresponding `extra = {...}`
    migration dict so existing databases pick it up on next launch.
  - `get_db()` returns a `KardexDB` instance wrapping a live connection; callers are expected to
    `db.close()` when done (most call sites use `try/finally`).
  - `KardexDB` exposes one method group per table/entity (proveedores, unidades, sustancias,
    entradas, salidas, usuarios, bitacora, checklists, catalogs...). Placeholder style (`?`) is
    shared between engines; SQL Server-specific quirks (e.g. `SCOPE_IDENTITY()` for last-insert-id,
    `OFFSET/FETCH` vs `LIMIT/OFFSET`) are branched inline on `self._motor`.

- **`utils/data_handler.py`** is a compatibility adapter kept from an older JSON-file-based version
  of the app. UI code still calls `DataHandler.load_json(SOME_FILE)`, `add_record(...)`,
  `update_record(...)` using the legacy `*_FILE` path constants from `config/config.py`
  (e.g. `ENTRADAS_FILE`, `SUSTANCIAS_FILE`) as routing keys — these no longer point at real JSON
  files. `_file_key()` extracts the basename (minus `.json`) and `DataHandler` dispatches to the
  matching `KardexDB` method. When adding a new entity, add a `_ROUTE_*` constant, wire it into
  `load_json` / `add_record` / `update_record`, and add the corresponding methods to `KardexDB` —
  don't bypass the adapter and call `database.py` directly from UI code, since the UI relies on the
  adapter's dict-shape normalization (e.g. boolean coercion, legacy field fallbacks).
  - `sync_inventario()` is a deprecated no-op kept for backward-compat calls; stock is always
    computed live from `entradas` minus `salidas` (see `_ROUTE_INVENTARIO` handling and
    `ui/stock.py` / `ui/stock_analista.py`), never stored.
  - `Lookups` and the `build_*_indexes` / `*_from_id` / `*_from_code` helpers in this file are used
    throughout the UI to resolve foreign keys (id_sustancia, id_ubicacion, etc.) to display names
    without re-querying the DB per row.

### Configuration: `config/config.py` vs `config.json`

Two separate, easily confused config files:
- **`config.json`** (repo root) — runtime DB engine selection (`motor`, sqlite path, SQL Server
  connection details). Read directly by `database.py`.
- **`config/config.py`** — UI constants (`COLORS`, window dimensions, `PROJECT_NAME`) and the
  legacy `*_FILE` path constants used as `DataHandler` routing keys (see above). `PROJECT_ROOT` is
  computed as `Path(__file__).resolve().parents[1]`, so this file must stay directly inside a
  single-level subfolder (`config/`) of the repo root.

### UI layer (`ui/`)

- Plain Tkinter, no framework. Each major feature is a `Toplevel`-opening class instantiated from
  `ui/menu.py` (`MainMenuWindow`), e.g. `EntryFormWindow` (`ui/entradas.py`), `SalidasWindow`
  (`ui/salidas.py`), `VigenciasWindow`, `StockWindow` / `StockAnalistaWindow`, `CreateUserWindow`,
  `MasterCatalogWindow` / `SubstanceMasterWindow` / `LocationMasterWindow` (`ui/maestras.py`),
  `BitacoraWindow`, `ReportesWindow`, `CheckListWindow`.
- `MainMenuWindow._can_open_window()` caps the app at 3 simultaneously open `Toplevel` windows;
  new feature windows should call `self._track_window(w)` after opening so they're counted and
  auto-cleaned.
- Permissions are role/permission-key gated per button in the main menu
  (`_has_permission` / `_guard_access`): `"admin"` role bypasses all checks; other roles are
  checked against the `permisos` dict loaded on the user record (`inventario`, `entradas`,
  `salidas`, `stock`, `consulta`, `vigencias`, `auditoria`). `usuarios_admin` and `inventario`
  (master-catalog edits) are admin-only regardless of the permisos dict.
- `ui/forms.py` is a thin backward-compat shim re-exporting `EntryFormWindow` from
  `ui/entradas.py` — don't add new code there.
- `ui/input_behaviors.py` holds shared Tkinter widget behaviors (e.g. input validation/formatting)
  reused across forms.
- `main.py` monkey-patches `tkinter.messagebox` (`_install_messagebox_parent_fallback`) so dialogs
  called without an explicit `parent=` still attach to the currently focused Toplevel instead of
  the hidden root window — keep this in mind if a messagebox appears behind another window.

### Core domain model

- `sustancias` (reagent catalog) is the central entity. `entradas` (stock-in / lot receipts) and
  `salidas` (stock-out / consumption) both reference `id_sustancia` and are the append-only ledger
  the app is named after (Kardex). Records are never hard-deleted — they're soft-voided via
  `anulado` + `motivo_anulacion` (see `anular_entrada` / `anular_salida`).
  - Active lots per substance must be unique: `entradas(id_sustancia, lote)` has a partial unique
    index `WHERE anulado = 0 AND lote <> ''`.
- Stock is always a derived value (sum of non-anulado `entradas.total` minus non-anulado
  `salidas.cantidad`, per substance and/or per lote), never persisted — see
  `DataHandler.load_json` under `_ROUTE_INVENTARIO` and `MainMenuWindow._check_notifications` for
  the two canonical implementations of this computation.
- `bitacora` is an audit log table (who/when/what field changed old->new value); `hoja` identifies
  which screen/entity the change belongs to.
- Reports (`ui/reportes.py`, `ui/etiquetas.py`) render from `openpyxl` templates in
  `reportes/templates/` and write output into `reportes/`.
- User signatures (image files, used on printed reports/labels) live in `firmas/`, referenced by
  `usuarios.firma_path`.

### Assets

`Imagenes/` holds UI icons and the login/menu background image, referenced via `IMAGES_PATH` in
`config/config.py`. Image loading always goes through a `try/except` around a lazy `PIL.Image` /
`PIL.ImageTk` import, falling back to a text placeholder if Pillow or the file is missing.
