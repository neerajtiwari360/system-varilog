"""Native VCD waveform view; no external viewer process or iframe."""
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

    async def show(self, run: Run) -> None:
        self.container.clear()
        self.canvas = None
        waves = [a for a in run.artifacts if a.endswith('.vcd')]
        with self.container:
            if not waves:
                ui.label('No waveform generated for this simulation run.').classes('text-warning')
                ui.label('Add $dumpfile and $dumpvars to the testbench, then run Simulation again.')
                return
            with ui.element('div').classes('native-wave-heading'):
                ui.label(run.tb_top).classes('native-wave-title').tooltip(f'{run.project} • Run {run.id}')
                choice = ui.select(waves, value=waves[0], label='VCD').props('dense outlined options-dense').classes('native-wave-file')
                ui.space()
                load = ui.button(icon='refresh').props('flat dense').tooltip('Reload waveform')
                ui.button(icon='download', on_click=lambda: ui.download.file(self.tools.artifact(run, choice.value))).props('flat dense').tooltip('Download VCD')
            message = ui.label('Reading simulation waveform…').classes('native-wave-info')
            viewport = ui.column().classes('native-wave-viewport')

        async def load_wave() -> None:
            viewport.clear()
            self.canvas = None
            load.disable()
            choice.disable()
            try:
                path = self.tools.artifact(run, choice.value)
                data = await background.io_bound(read_vcd, path)
                if viewport.is_deleted:
                    return
                with viewport:
                    self.canvas = WaveformCanvas(data.to_dict()).classes('w-full h-full')
                message.set_text(f'{run.status} • {len(data.signals)} signals • Run {run.id}')
                message.tooltip(f'{choice.value} • Duration {data.end} × {data.timescale}')
            except (ValueError, OSError, UnicodeError) as e:
                if not message.is_deleted:
                    message.set_text(f'Cannot display waveform: {e}')
            finally:
                if not load.is_deleted:
                    load.enable()
                    choice.enable()

        load.on_click(load_wave)
        await load_wave()
