"""Run with python -m sv_studio.app from the repository root."""
import logging
import os
from pathlib import Path

from nicegui import app, ui

from sv_studio.services.tools import ToolService
from sv_studio.services.workspace import Workspace
from sv_studio.ui.layout import Studio

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
workspace = Workspace(Path(__file__).resolve().parent.parent)
tools = ToolService(workspace)


async def shutdown() -> None:
    if tools.busy:
        await tools.runner.stop()
    await tools.close_waveform()


app.on_shutdown(shutdown)


@ui.page('/')
async def index(project: str = '', rtl: str = '', tb: str = '', view: str = ''):
    studio = Studio(workspace, tools)
    if project in workspace.projects():
        studio.project_select.value = project
    if rtl in studio.rtl_top.options:
        studio.rtl_top.value = rtl
    if tb in studio.tb_top.options:
        studio.tb_top.value = tb
    if view == 'waveform':
        await studio.open_wave()


if __name__ in {'__main__', '__mp_main__'}:
    ui.run(title='SV Studio', host='127.0.0.1', port=int(os.environ.get('SV_STUDIO_PORT', '8080')),
           reload=False, show=False, binding_refresh_interval=0.2)
