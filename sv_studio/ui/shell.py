"""Viewport-based IDE shell. Sidebars never take width from a focused waveform."""
from pathlib import Path
from nicegui import ui


def build_shell(s) -> None:
    ui.add_css(Path(__file__).with_name('studio.css').read_text(encoding='utf-8'))
    with ui.element('div').classes('studio-shell'):
        with ui.element('header').classes('studio-header'):
            with ui.element('div').classes('studio-brand'):
                ui.icon('memory', size='24px')
                ui.label('SV STUDIO')
            s.project_select = ui.select(s.ws.projects(), label='Project', on_change=s.change_project).props('dense outlined options-dense').classes('studio-project')
            s.rtl_top = ui.select([], label='RTL top', with_input=True).props('dense outlined options-dense').classes('studio-rtl')
            s.tb_top = ui.select([], label='Testbench top', with_input=True).props('dense outlined options-dense').classes('studio-tb')
            ui.space()
            ui.button(icon='contrast', on_click=s.dark.toggle).props('flat round dense').tooltip('Toggle theme')
        with ui.element('nav').classes('studio-actions'):
            ui.button('Save all', icon='save', on_click=s.save_all).props('flat no-caps')
            ui.separator().props('vertical')
            ui.button('Simulation', icon='play_arrow', on_click=lambda: s.start('simulation')).props('flat no-caps')
            ui.button('Waveform', icon='show_chart', on_click=lambda: s.open_wave()).props('flat no-caps')
            ui.separator().props('vertical')
            for title, op, icon in [('Lint', 'lint', 'fact_check'), ('Synthesis', 'synthesis', 'account_tree'), ('Generate schematic', 'schematic', 'schema')]:
                ui.button(title, icon=icon, on_click=lambda _, op=op: s.start(op)).props('flat no-caps')
            ui.button('Stop', icon='stop', on_click=s.stop).props('flat no-caps color=negative')
            ui.space()
            ui.button(icon='folder_open', on_click=lambda: s.toggle_panel('explorer')).props('flat dense').tooltip('Show / hide explorer')
            ui.button(icon='terminal', on_click=lambda: s.toggle_panel('console')).props('flat dense').tooltip('Show / hide console')
            ui.button(icon='description', on_click=lambda: s.toggle_panel('results')).props('flat dense').tooltip('Show / hide run results')
            s.focus_button = ui.button('Focus', icon='fullscreen', on_click=lambda: s.set_focus(not s.focused)).props('flat no-caps').tooltip('Use the entire workspace for the active tab')
        s.workspace_shell = ui.element('div').classes('studio-workspace')
        with s.workspace_shell:
            s.explorer_pane = ui.element('aside').classes('studio-side studio-explorer')
            with s.explorer_pane:
                with ui.element('div').classes('studio-side-heading'):
                    ui.label('PROJECT EXPLORER').classes('pane-title')
                    with ui.row().classes('gap-1'):
                        ui.button(icon='refresh', on_click=lambda: s.guard(s.refresh)).props('flat round dense').tooltip('Refresh')
                        ui.button(icon='note_add', on_click=s.new_file).props('flat round dense').tooltip('New file')
                s.explorer = ui.column().classes('studio-tree')
                with ui.expansion('Source files', icon='checklist').classes('studio-sources'):
                    ui.label('Select dependencies; manifest controls compile order.').classes('text-xs opacity-60')
                    s.source_select = ui.select([], multiple=True, label='Compile sources').props('dense use-chips options-dense').classes('w-full')
            with ui.element('main').classes('studio-center'):
                with ui.splitter(value=190, horizontal=True, reverse=True, limits=(0, 450)).props('unit=px').classes('w-full h-full') as vertical:
                    s.editor_console_splitter = vertical
                    with vertical.before:
                        with ui.element('div').classes('studio-editor-pane'):
                            s.tabs = ui.tabs(on_change=s.tab_changed).props('dense inline-label no-caps align=left').classes('w-full studio-tabs')
                            s.panels = ui.tab_panels(s.tabs, animated=False).classes('studio-tab-panels')
                            with s.panels:
                                with ui.tab_panel('__welcome__'):
                                    with ui.element('div').classes('studio-empty'):
                                        ui.icon('code', size='34px')
                                        ui.label('Open a source file to edit, or run a simulation to inspect waveforms.')
                            s.tabs.value = '__welcome__'
                    with vertical.after:
                        with ui.element('section').classes('studio-console').style('width:100%;min-width:0;max-width:100%;box-sizing:border-box'):
                            with ui.element('div').classes('studio-console-top'):
                                ui.label('CONSOLE').classes('pane-title')
                                s.search = ui.input('Search log', on_change=lambda _: s.filter_logs()).props('dense clearable')
                                ui.space()
                                ui.button(icon='content_copy', on_click=lambda: ui.clipboard.write(s.log_text)).props('flat round dense').tooltip('Copy logs')
                                ui.button(icon='download', on_click=lambda: ui.download.content(s.log_text, 'sv-studio.log')).props('flat round dense').tooltip('Export logs')
                                ui.button(icon='clear_all', on_click=s.clear_logs).props('flat round dense').tooltip('Clear display')
                                ui.button(icon='close', on_click=lambda: s.toggle_panel('console')).props('flat round dense').tooltip('Hide console')
                            s.console = ui.log(max_lines=20000).props('visible').classes('w-full').style('width:100%;max-width:100%;min-width:0;flex:1 1 0;height:0')
            s.results_pane = ui.element('aside').classes('studio-side studio-results')
            with s.results_pane:
                with ui.element('div').classes('studio-side-heading'):
                    ui.label('RUNS & ARTIFACTS').classes('pane-title')
                    ui.button(icon='close', on_click=lambda: s.toggle_panel('results')).props('flat round dense')
                s.history_select = ui.select({}, label='Reopen run', on_change=s.reopen).props('dense outlined options-dense').classes('w-full')
                s.results = ui.column().classes('studio-result-content')
                with s.results:
                    ui.label('No run selected').classes('text-xs opacity-60')
        with ui.element('footer').classes('studio-status'):
            s.status = ui.label('Ready')
            ui.space()
            ui.label('Local workspace • Icarus / Verilator / Yosys')
