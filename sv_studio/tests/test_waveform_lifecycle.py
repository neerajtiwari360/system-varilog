import asyncio

from nicegui import ui

from sv_studio.services.tools import ToolService
from sv_studio.tests.test_services import FixtureRunner, ws
from sv_studio.ui.layout import Studio


async def test_rerunning_simulation_never_leaves_empty_waveform(user, ws, monkeypatch):
    tools = ToolService(ws, FixtureRunner(ws))
    instances = {}

    @ui.page('/waveform-rerun-test')
    def page():
        instances['studio'] = Studio(ws, tools)

    await user.open('/waveform-rerun-test')
    studio = instances['studio']
    with user:
        studio.rtl_top.value = 'actual'
        await studio.start('simulation')
        await studio.open_wave()
    previous_id = studio.run_result.id
    assert studio.waveform_viewer.canvas is not None

    original_run = tools.run
    started, release = asyncio.Event(), asyncio.Event()
    async def delayed_run(*args, **kwargs):
        started.set()
        await release.wait()
        return await original_run(*args, **kwargs)
    monkeypatch.setattr(tools, 'run', delayed_run)
    user.find('Simulation').click()
    await asyncio.wait_for(started.wait(), 2)
    await user.should_see('Simulation running — the new waveform will load when it finishes.')
    assert studio.waveform_viewer.canvas is None
    release.set()
    for _ in range(100):
        await asyncio.sleep(.02)
        if studio.waveform_viewer.canvas is not None:
            break
    assert studio.waveform_viewer.canvas is not None
    assert studio.run_result.id != previous_id
    await user.should_see(f'Run {studio.run_result.id}')

    # A subsequent run with no dump must replace the trace with an explanation.
    tools.runner.scenario = 'no_vcd'
    user.find('Simulation').click()
    await asyncio.sleep(.2)
    assert studio.waveform_viewer.canvas is None
    await user.should_see('No waveform generated for this simulation run.')
