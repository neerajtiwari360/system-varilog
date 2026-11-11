import asyncio

from nicegui import ui

from sv_studio.services.tools import ToolService
from sv_studio.ui.layout import Studio
from sv_studio.tests.test_services import FixtureRunner, ws


async def test_ui_editor_and_tool_actions(user, ws, monkeypatch):
    tools = ToolService(ws, FixtureRunner(ws))
    async def external_viewer(*args):
        raise AssertionError('Native waveform view must not launch GTKWave/noVNC')
    monkeypatch.setattr(tools, 'waveform', external_viewer)
    instance = {}

    @ui.page('/studio-test')
    def page():
        instance['studio'] = Studio(ws, tools)

    await user.open('/studio-test')
    await user.should_see('SV STUDIO')
    studio = instance['studio']
    labels = [b.text for b in sorted(user.find(ui.button).elements, key=lambda b: b.id)]
    workflow = ['Save all', 'Simulation', 'Waveform', 'Lint', 'Synthesis', 'Generate schematic', 'Stop']
    assert [labels.index(label) for label in workflow] == sorted(labels.index(label) for label in workflow)
    with user:
        studio.rtl_top.value = 'actual'
        studio.open_file('projects/demo/rtl/unrelated_name.sv')
    user.find(ui.codemirror).type('\n// edited through UI')
    user.find('Save all').click()
    await asyncio.sleep(.05)
    assert '// edited through UI' in ws.read('projects/demo/rtl/unrelated_name.sv')
    for label, operation in [('Simulation', 'simulation'), ('Lint', 'lint'), ('Synthesis', 'synthesis'), ('Generate schematic', 'schematic')]:
        user.find(label).click()
        await asyncio.sleep(.2)
        assert studio.run_result is not None
        assert studio.run_result.operation == operation
        assert studio.run_result.status != 'Failed', studio.run_result.detail
    user.find('Waveform').click()
    await asyncio.sleep(.2)
    assert studio.tabs.value == '__waveform__'
    assert studio.focused
    assert not any(studio.panel_visibility.values())
    assert studio.editor_console_splitter.value == 0
    user.find('Restore layout').click()
    assert not studio.focused
    assert all(studio.panel_visibility.values())
    assert studio.editor_console_splitter.value == 190
    with user:
        studio.toggle_panel('results')
        studio.set_focus(True)
        studio.set_focus(False)
    assert not studio.panel_visibility['results']  # restore keeps the user's panel choice
    simulation = next(r for r in tools.history('demo') if r.operation == 'simulation')
    data = studio.waveform_viewer.canvas.props['data']
    assert data['signals'][0]['name'] == 'bench.clk'
    assert data['changes']['!'] == [[0, '0'], [5, '1'], [10, '0']]
    await user.should_see(f'Run {simulation.id}')


async def test_waveform_does_not_fall_back_to_stale_run(user, ws):
    tools = ToolService(ws, FixtureRunner(ws))
    sources = ws.sources('demo')
    first = await tools.run('demo', 'simulation', 'actual', 'bench', sources)
    tools.runner.scenario = 'no_vcd'
    latest = await tools.run('demo', 'simulation', 'actual', 'bench', sources)
    assert first.id != latest.id
    instance = {}
    @ui.page('/waveform-state-test')
    def page():
        instance['studio'] = Studio(ws, tools)
    await user.open('/waveform-state-test')
    studio = instance['studio']
    assert studio.waveform_run().id == latest.id
    user.find('Waveform').click()
    await asyncio.sleep(.05)
    await user.should_see('No waveform generated for this simulation run.')
    assert studio.waveform_viewer.canvas is None
    with user:
        studio.tb_top.set_options(['other'], value='other')
    assert studio.waveform_run() is None
    user.find('Waveform').click()
    await asyncio.sleep(.05)
    await user.should_see('Run Simulation first for the selected testbench')
