"""Shared central-tab viewers for source files and generated artifacts."""
from pathlib import Path
from nicegui import ui


def language_for(path: Path) -> str | None:
    return {'.sv':'SystemVerilog', '.v':'Verilog', '.svh':'SystemVerilog', '.vh':'Verilog',
            '.json':'JSON', '.md':'Markdown', '.py':'Python', '.ys':'Tcl', '.sdc':'Tcl',
            '.xdc':'Tcl', '.yaml':'YAML', '.yml':'YAML', '.sh':'Shell', '.ps1':'PowerShell'}.get(path.suffix.lower())


def svg_view(path: Path) -> None:
    with ui.column().classes('document-preview'):
        with ui.row().classes('w-full items-center gap-2'):
            ui.label(path.name).classes('text-xs')
            ui.button('Fit', on_click=lambda: zoom.set_value(100)).props('flat dense no-caps')
            ui.button('Download original SVG', icon='download', on_click=lambda: ui.download.file(path)).props('flat dense no-caps')
        ui.label('Zoom with slider; drag scrollbars to pan.').classes('text-xs opacity-60')
        zoom = ui.slider(min=25, max=500, value=100).classes('w-full')
        with ui.scroll_area().classes('w-full flex-grow min-h-0'):
            picture = ui.image(path).classes('max-w-none').style('width:100%')
            zoom.on_value_change(lambda e: picture.style(f'width:{e.value}%'))
