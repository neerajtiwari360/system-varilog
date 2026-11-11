import asyncio
from datetime import datetime
from pathlib import Path

from nicegui import ui

from sv_studio.models import Run
from sv_studio.services.tools import ToolService
from sv_studio.services.workspace import Workspace
from sv_studio.ui.waveform_viewer import WaveformViewer
from sv_studio.ui.shell import build_shell


class Studio:
    def __init__(self, ws: Workspace, tools: ToolService):
        self.ws, self.tools = ws, tools
        self.project = ''
        self.focused = False
        self.panel_visibility = {'explorer': True, 'results': True, 'console': True}
        self.saved_panel_visibility = self.panel_visibility.copy()
        self.buffers: dict[str, str] = {}
        self.originals: dict[str, str] = {}
        self.editors: dict[str, object] = {}
        self.tab_labels: dict[str, object] = {}
        self.run_result: Run | None = None
        self.waveform_viewer: WaveformViewer | None = None
        self.log_text = ''
        self.task: asyncio.Task | None = None
        self.build()

    def guard(self, action):
        try:
            return action()
        except (ValueError, OSError, UnicodeError) as e:
            ui.notify(str(e), type='negative')

    def apply_panels(self) -> None:
        for name in ('explorer', 'results'):
            visible = self.panel_visibility[name]
            getattr(self, f'{name}_pane').set_visibility(visible)
            self.workspace_shell.classes(remove=f'no-{name}' if visible else '', add=f'no-{name}' if not visible else '')
        self.editor_console_splitter.value = 190 if self.panel_visibility['console'] else 0

    def toggle_panel(self, name: str) -> None:
        self.panel_visibility[name] = not self.panel_visibility[name]
        self.apply_panels()

    def set_focus(self, enabled: bool) -> None:
        if enabled == self.focused:
            return
        if enabled:
            self.saved_panel_visibility = self.panel_visibility.copy()
            self.panel_visibility = dict.fromkeys(self.panel_visibility, False)
        else:
            self.panel_visibility = self.saved_panel_visibility.copy()
        self.focused = enabled
        self.focus_button.set_text('Restore layout' if enabled else 'Focus')
        self.focus_button.props('icon=fullscreen_exit' if enabled else 'icon=fullscreen')
        self.apply_panels()

    def tab_changed(self, e) -> None:
        if e.value != '__waveform__' and self.focused:
            self.set_focus(False)

    def build(self) -> None:
        ui.colors(primary='#5796cf', positive='#4cba8b', negative='#df6973', warning='#d6ad55')
        self.dark = ui.dark_mode(True)
        build_shell(self)
        ui.keyboard(on_key=self.keypress)
        ui.add_head_html('''<script>window.addEventListener('keydown', e => {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') e.preventDefault();
        }); window.addEventListener('beforeunload', e => {
            if (window.svStudioDirty) {e.preventDefault(); e.returnValue = '';}
        });</script>''')
        projects = self.ws.projects()
        if projects:
            self.project_select.value = projects[0]

    async def keypress(self, e) -> None:
        if e.action.keydown and e.key.name.lower() == 's' and (e.modifiers.ctrl or e.modifiers.meta):
            self.save_all()

    def change_project(self, e) -> None:
        if e.value == self.project:
            return
        self.set_focus(False)
        self.project = e.value
        self.run_result = None
        if self.waveform_viewer:
            self.waveform_viewer.clear()
        self.annotate()
        self.status.set_text('Ready')
        self.status.style('color:#9aa5b5')
        self.results.clear()
        self.clear_logs()
        self.guard(self.refresh)

    def refresh(self) -> None:
        files = self.ws.files(self.project)
        sources = self.ws.files(self.project, sources_only=True)
        selected = self.ws.sources(self.project)
        self.source_select.set_options(sources, value=selected)
        candidates = self.ws.modules(sources)
        rtl = [m for m, f in candidates.items() if not self.ws.is_tb(f)]
        tb = [m for m, f in candidates.items() if self.ws.is_tb(f)]
        self.rtl_top.set_options(rtl, value=self.rtl_top.value if self.rtl_top.value in rtl else next(iter(rtl), None))
        self.tb_top.set_options(tb, value=self.tb_top.value if self.tb_top.value in tb else next(iter(tb), None))
        self.explorer.clear()
        tree: dict = {}
        prefix = f'projects/{self.project}/'
        for file in files:
            branch = tree
            parts = file.removeprefix(prefix).split('/')
            for part in parts[:-1]:
                branch = branch.setdefault(part, {})
            branch[parts[-1]] = file

        def render(branch: dict) -> None:
            for name, item in branch.items():
                if isinstance(item, dict):
                    with ui.expansion(name, icon='folder', value=name in {'rtl', 'tb'}).classes('w-full'):
                        render(item)
                else:
                    ui.button(name, icon='description', on_click=lambda _, p=item: self.guard(lambda: self.open_file(p))).props('flat no-caps dense').classes('w-full justify-start')
        with self.explorer:
            render(tree)
        self.update_history()

    def open_file(self, path: str, line: int | None = None) -> None:
        if path not in self.buffers:
            text = self.ws.read(path)
            self.buffers[path] = self.originals[path] = text
            with self.tabs:
                tab = ui.tab(path, label='/'.join(Path(path).parts[-3:]))
                self.tab_labels[path] = tab
            with self.panels:
                with ui.tab_panel(path).classes('p-0 h-full'):
                    editor = ui.codemirror(text, language='SystemVerilog', theme='vscodeDark',
                        keymap={'Ctrl-s': lambda _: self.save_all(), 'Meta-s': lambda _: self.save_all()},
                        on_change=lambda e, p=path: self.changed(p, e.value)).classes('h-full w-full')
                    self.editors[path] = editor
        self.tabs.value = path
        self.annotate()
        if line:
            self.editors[path].reveal_line(line)

    def changed(self, path: str, text: str) -> None:
        self.buffers[path] = text
        dirty = text != self.originals[path]
        self.tab_labels[path].set_label('/'.join(Path(path).parts[-3:]) + (' *' if dirty else ''))
        ui.run_javascript('window.svStudioDirty = ' + str(any(self.buffers[p] != self.originals[p] for p in self.buffers)).lower())

    def save_all(self) -> bool:
        try:
            for p, text in self.buffers.items():
                if text != self.originals[p]:
                    # Avoid silently replacing edits made by another editor after opening.
                    if self.ws.read(p) != self.originals[p]:
                        raise ValueError(f'{p} changed on disk. Reload the page or reconcile changes before saving.')
                    self.ws.save(p, text)
                    self.originals[p] = text
                    self.changed(p, text)
            ui.notify('Saved', type='info')
            return True
        except (ValueError, OSError) as e:
            ui.notify(str(e), type='negative')
            return False

    def new_file(self) -> None:
        with ui.dialog() as dialog, ui.card():
            ui.label('Create source file')
            name = ui.input('Project-relative path', placeholder='rtl/counter.sv')
            def create():
                result = self.guard(lambda: self.ws.create(self.project, name.value))
                if result:
                    self.refresh()
                    self.open_file(result)
                    dialog.close()
            ui.button('Create', on_click=create)
            ui.button('Cancel', on_click=dialog.close).props('flat')
        dialog.open()

    def append(self, text: str) -> None:
        self.log_text += text
        self.console.push(text)

    def clear_logs(self) -> None:
        self.log_text = ''
        self.console.clear()

    def filter_logs(self) -> None:
        self.console.clear()
        needle = (self.search.value or '').lower()
        for line in self.log_text.splitlines():
            if needle in line.lower():
                self.console.push(line)

    async def start(self, operation: str) -> None:
        if self.tools.busy:
            ui.notify('A tool is already running', type='warning')
            return
        if not self.save_all():
            return
        self.set_focus(False)
        self.panel_visibility['console'] = True
        self.apply_panels()
        if operation == 'simulation' and self.waveform_viewer:
            self.waveform_viewer.clear('Simulation running — the new waveform will load when it finishes.')
        self.run_result = None
        self.annotate()
        self.results.clear()
        self.clear_logs()
        self.status.set_text('Running • ' + operation)
        self.status.style('color:#9aa5b5')
        try:
            completed_run = await self.tools.run(self.project, operation, self.rtl_top.value or '',
                self.tb_top.value or '', list(self.source_select.value or []), self.append)
            if completed_run.project != self.project:
                return
            self.run_result = completed_run
            self.show_result()
            self.update_history()
            if operation == 'simulation' and self.waveform_viewer and self.tabs.value == '__waveform__':
                await self.waveform_viewer.show(completed_run)
        except (ValueError, OSError) as e:
            self.status.set_text('Failed')
            self.status.style('color:#df6973')
            if operation == 'simulation' and self.waveform_viewer:
                self.waveform_viewer.clear(f'Simulation could not start: {e}')
            ui.notify(str(e), type='negative')

    async def stop(self) -> None:
        if self.tools.busy:
            await self.tools.runner.stop()

    def update_history(self) -> None:
        history = self.tools.history(self.project)
        self.history_select.set_options({r.id: f'{r.operation} • {r.status} • {r.id}' for r in history})

    def reopen(self, e) -> None:
        run = next((r for r in self.tools.history(self.project) if r.id == e.value), None)
        if run:
            self.run_result = run
            self.clear_logs()
            for artifact in run.artifacts:
                if artifact.endswith('.log'):
                    self.append(f'\n--- {artifact} ---\n' + self.tools.artifact(run, artifact).read_text(encoding='utf-8'))
            self.show_result()

    def show_result(self) -> None:
        run = self.run_result
        if not run:
            return
        self.annotate()
        self.status.set_text(f'{run.status} • {run.operation}')
        self.status.style('color:' + {'Passed': '#4cba8b', 'Failed': '#df6973', 'Warning': '#d6ad55'}.get(run.status, '#9aa5b5'))
        self.results.clear()
        with self.results:
            ui.label(f'{run.project} • {run.operation.upper()}').classes('text-lg font-semibold')
            ui.label(run.detail).classes('text-sm')
            ui.label(f'Run: {run.id}').classes('text-xs break-all opacity-60')
            ui.label(f'Top: {run.tb_top if run.operation == "simulation" else run.rtl_top}')
            if run.ended:
                duration = (datetime.fromisoformat(run.ended) - datetime.fromisoformat(run.started)).total_seconds()
                ui.label(f'Duration: {duration:.2f}s')
            for cmd in run.commands:
                ui.label(f'{cmd["stage"]}: exit {cmd["exit_code"]}').classes('text-xs')
            if run.statistics:
                ui.label('Generic cell counts (not KV260 utilization)').classes('font-semibold')
                ui.table(columns=[{'name':'type','label':'Cell','field':'type'}, {'name':'count','label':'Count','field':'count'}],
                    rows=[{'type':k, 'count':v} for k,v in run.statistics.items()]).classes('w-full')
                if sum(run.statistics.values()) > 300:
                    ui.label('Large design: full schematic may be difficult to read.').classes('text-warning')
            ui.label(f'Warnings: {sum(d["severity"] == "warning" for d in run.diagnostics)} • Errors: {sum(d["severity"] == "error" for d in run.diagnostics)}')
            for d in run.diagnostics:
                ui.button(d['message'], on_click=lambda _, d=d: self.guard(lambda: self.open_file(d['file'], d['line'])) if d['file'] else None).props('flat no-caps').classes('text-xs text-left')
            ui.separator()
            if run.operation == 'simulation' and not any(a.endswith('.vcd') for a in run.artifacts):
                ui.label('No waveform generated').classes('opacity-60')
            elif run.operation == 'simulation':
                ui.button('View this waveform', icon='show_chart', on_click=lambda: self.open_wave(run)).props('flat')
            for artifact in run.artifacts:
                # Source snapshots remain available on disk; avoid thousands of UI rows.
                if '/build/' not in artifact and not artifact.endswith('.log'):
                    continue
                with ui.element('div').classes('studio-artifact'):
                    ui.label(Path(artifact).name).classes('studio-artifact-name').tooltip(artifact)
                    ui.button(icon='download', on_click=lambda _, a=artifact: ui.download.file(self.tools.artifact(run, a))).props('flat round dense')
                    if artifact.endswith('.svg'):
                        ui.button('View SVG', on_click=lambda _, a=artifact: self.view_svg(run, a)).props('flat dense')
                    elif artifact.endswith(('.v', '.json')):
                        ui.button('Inspect', on_click=lambda _, a=artifact: self.inspect(run, a)).props('flat dense')

    def annotate(self) -> None:
        for path, editor in self.editors.items():
            editor.line_tooltips = {d['line']: d['message'] for d in self.run_result.diagnostics
                                    if d['file'] == path and d['line']} if self.run_result else {}

    def inspect(self, run: Run, artifact: str) -> None:
        with ui.dialog() as dialog, ui.card().classes('w-[90vw] max-w-none'):
            ui.label(artifact)
            ui.code(self.tools.artifact(run, artifact).read_text(encoding='utf-8'), language='verilog' if artifact.endswith('.v') else 'json').classes('w-full max-h-[75vh] overflow-auto')
            ui.button('Close', on_click=dialog.close)
        dialog.open()

    def view_svg(self, run: Run, artifact: str) -> None:
        with ui.dialog() as dialog, ui.card().classes('w-[95vw] max-w-none'):
            ui.label(f'{run.rtl_top} • synthesized gate-level • {run.id}')
            scale = {'value': 100}
            with ui.row():
                ui.button('Download original SVG', on_click=lambda: ui.download.file(self.tools.artifact(run, artifact)))
                ui.button('Fit', on_click=lambda: zoom.set_value(100))
                ui.button('Close', on_click=dialog.close)
            ui.label('Zoom with slider; drag scrollbars to pan.')
            zoom = ui.slider(min=25, max=500, value=100).classes('w-full')
            with ui.scroll_area().classes('w-full h-[70vh]'):
                # ui.image serves a local file as an image: SVG scripts cannot execute inline.
                picture = ui.image(self.tools.artifact(run, artifact)).classes('max-w-none').style('width:100%')
                zoom.on_value_change(lambda e: picture.style(f'width:{e.value}%'))
        dialog.open()

    def waveform_run(self) -> Run | None:
        if self.run_result and self.run_result.operation == 'simulation' and self.run_result.project == self.project:
            return self.run_result  # An explicitly reopened simulation takes precedence.
        return next((r for r in self.tools.history(self.project)
                     if r.operation == 'simulation' and r.tb_top == self.tb_top.value), None)

    async def open_wave(self, run: Run | None = None) -> None:
        if self.tools.busy:
            ui.notify('Wait for the active operation before opening the waveform', type='warning')
            return
        run = run or self.waveform_run()
        if not run:
            if self.waveform_viewer:
                self.waveform_viewer.clear()
            ui.notify('Run Simulation first for the selected testbench', type='warning')
            return
        if self.waveform_viewer is None:
            with self.tabs:
                ui.tab('__waveform__', label='Waveform', icon='show_chart')
            with self.panels:
                with ui.tab_panel('__waveform__').classes('p-0 h-full'):
                    self.waveform_viewer = WaveformViewer(self.tools)
        self.tabs.value = '__waveform__'
        self.set_focus(True)
        await self.waveform_viewer.show(run)
