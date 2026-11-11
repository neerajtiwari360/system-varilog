from nicegui.element import Element


class WaveformCanvas(Element, component='waveform_canvas.js'):
    def __init__(self, data: dict):
        super().__init__()
        self._props['data'] = data
