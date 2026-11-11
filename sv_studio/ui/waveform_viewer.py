"""Native VCD waveform view; no external viewer process or iframe."""
from pathlib import Path
from nicegui import run as background, ui

from sv_studio.models import Run
from sv_studio.services.tools import ToolService
from sv_studio.services.vcd import read_vcd
from sv_studio.ui.waveform_canvas import WaveformCanvas


class WaveformViewer:
    def __init__(self, tools: ToolService):
        self.tools = tools
        self.container = ui.column().classes('native-wave-panel')
        self.canvas: WaveformCanvas | None = None

    def clear(self, message: str = 'Select Waveform to load a simulation trace.') -> None:
        self.container.clear()
        self.canvas = None
        with self.container:
            with ui.element('div').classes('waveform-state'):
                ui.icon('show_chart', size='28px')
                ui.label(message).classes('waveform-state-message')

    async def show(self, run: Run, selected: str | None = None) -> None:
        files = {a: self.tools.artifact(run, a) for a in run.artifacts if a.endswith('.vcd')}
        await self.show_files(files, run.tb_top, f'{run.status} | Run {run.id}', selected)

    async def show_file(self, file: Path, label: str) -> None:
        await self.show_files({file.name: file}, file.name, label, file.name)

    async def show_files(self, files: dict[str, Path], title: str, origin: str, selected: str | None) -> None:
        self.container.clear()
        self.canvas = None
        waves = list(files)
        with self.container:
            if not waves:
                ui.label('No waveform generated for this simulation run.').classes('text-warning')
                ui.label('Add $dumpfile and $dumpvars to the testbench, then run Simulation again.')
                return
            with ui.element('div').classes('native-wave-heading'):
                title_label = ui.label(title).classes('native-wave-title')
                title_label.props['title'] = origin
                choice = ui.select(waves, value=selected if selected in files else waves[0], label='VCD').props('dense outlined options-dense').classes('native-wave-file')
                ui.space()
                load = ui.button(icon='refresh').props('flat dense').tooltip('Reload waveform')
                ui.button(icon='download', on_click=lambda: ui.download.file(files[choice.value])).props('flat dense').tooltip('Download VCD')
            message = ui.label('Reading simulation waveform…').classes('native-wave-info')
            viewport = ui.column().classes('native-wave-viewport')

        async def load_wave() -> None:
            viewport.clear()
            self.canvas = None
            load.disable()
            choice.disable()
            try:
                path = files[choice.value]
                data = await background.io_bound(read_vcd, path)
                if data is None or viewport.is_deleted:
                    return
                with viewport:
                    self.canvas = WaveformCanvas(data.to_dict()).classes('w-full h-full')
                message.set_text(f'{len(data.signals)} signals | {origin}')
                message.props['title'] = f'{choice.value} • Duration {data.end} × {data.timescale}'
            except (ValueError, OSError, UnicodeError) as e:
                if not message.is_deleted:
                    message.set_text(f'Cannot display waveform: {e}')
            finally:
                if not load.is_deleted:
                    load.enable()
                    choice.enable()

        load.on_click(load_wave)
        await load_wave()
