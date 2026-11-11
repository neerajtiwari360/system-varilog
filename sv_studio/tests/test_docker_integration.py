"""Opt-in real HDL tests: $env:SV_STUDIO_DOCKER_TESTS='1'; python -m pytest -q."""
import asyncio
import os
import shutil
import uuid
from pathlib import Path

import pytest

from sv_studio.services.tools import ToolService
from sv_studio.services.workspace import Workspace

pytestmark = pytest.mark.skipif(os.environ.get('SV_STUDIO_DOCKER_TESTS') != '1', reason='Opt-in real Docker integration')


async def test_real_examples():
    ws = Workspace(Path(__file__).resolve().parents[2])
    tools = ToolService(ws)
    project = 'sv_studio_examples'
    sources = ws.sources(project)
    for top in ['studio_and', 'studio_registered_and', 'studio_counter']:
        simulation = await tools.run(project, 'simulation', top, 'tb_' + top, sources)
        assert simulation.status == 'Passed', simulation.detail
        assert any(a.endswith('.vcd') for a in simulation.artifacts)
        lint = await tools.run(project, 'lint', top, '', sources)
        assert lint.status in {'Passed', 'Warning'}, lint.detail
        synth = await tools.run(project, 'synthesis', top, '', sources)
        assert synth.status == 'Passed', synth.detail
        assert synth.statistics
        assert any(a.endswith('.svg') for a in synth.artifacts)
    # Legacy example includes $readmemb("tb/inputs.txt"); snapshot must preserve it.
    legacy = await tools.run('01_logic_gates', 'simulation', 'registered_io_and', 'tb_registered_io_and', ws.sources('01_logic_gates'))
    assert legacy.status == 'Warning', legacy.detail  # no success criteria configured
    log = tools.artifact(legacy, 'simulation.log').read_text()
    assert 'PASS: All AND tests completed' in log
    assert 'Unable to open' not in log


async def test_real_failures_isolation_timeout_cancel():
    ws = Workspace(Path(__file__).resolve().parents[2])
    project = 'studio_test_' + uuid.uuid4().hex
    base = ws.path(f'projects/{project}')
    (base / 'rtl').mkdir(parents=True)
    (base / 'tb').mkdir()
    (base / 'rtl/design.sv').write_text('module device_under_test; endmodule')
    bench = base / 'tb/bench.sv'
    tools = ToolService(ws)
    try:
        bench.write_text('module bench; initial $fatal(1, "intentional failure"); endmodule')
        run = await tools.run(project, 'simulation', 'device_under_test', 'bench', ws.sources(project))
        assert run.status == 'Failed' and 'Simulation' in run.detail
        bench.write_text('module bench; this is invalid syntax; endmodule')
        run = await tools.run(project, 'simulation', 'device_under_test', 'bench', ws.sources(project))
        assert run.status == 'Failed' and 'Compilation' in run.detail
        bench.write_text('module bench; initial begin $display("finished"); $finish; end endmodule')
        run = await tools.run(project, 'simulation', 'device_under_test', 'bench', ws.sources(project))
        assert run.status == 'Warning'
        assert not any(a.endswith('.vcd') for a in run.artifacts)
        (base / 'rtl/design.sv').write_text('module device_under_test; logic a; broken syntax; endmodule')
        run = await tools.run(project, 'synthesis', 'device_under_test', '', ws.sources(project))
        assert run.status == 'Failed'
        assert not any(a.endswith('.svg') for a in run.artifacts)
        (base / 'rtl/design.sv').write_text('module device_under_test; endmodule')
        bench.write_text('module bench; reg clk=0; always #1 clk=~clk; endmodule')
        tools.runner.timeout = 3
        run = await tools.run(project, 'simulation', 'device_under_test', 'bench', ws.sources(project))
        assert run.status == 'Failed' and 'timed out' in run.detail
        tools.runner.timeout = 60
        pending = asyncio.create_task(tools.run(project, 'simulation', 'device_under_test', 'bench', ws.sources(project)))
        for _ in range(500):
            if tools.runner.active and tools.runner.active.returncode is None:
                # Cancel an actual container process, even if it is still compiling.
                await tools.runner.stop()
                break
            await asyncio.sleep(.02)
        run = await pending
        assert run.status == 'Cancelled'
    finally:
        assert base.resolve().is_relative_to(ws.root / 'projects')
        shutil.rmtree(base)


async def test_real_waveform_viewer():
    import httpx
    ws = Workspace(Path(__file__).resolve().parents[2])
    tools = ToolService(ws)
    run = await tools.run('sv_studio_examples', 'simulation', 'studio_and', 'tb_studio_and', ws.sources('sv_studio_examples'))
    assert run.status == 'Passed', run.detail
    vcd = next(a for a in run.artifacts if a.endswith('.vcd'))
    try:
        url = await tools.waveform(run, vcd)
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            assert response.status_code == 200
            assert 'noVNC' in response.text
        code, logs = await tools.runner.execute([tools.runner.docker, 'logs', tools.viewer_name], lambda _: None)
        assert code == 0
        assert f'sv_studio/{run.id}/and.vcd' in logs
        assert 'Opening GTKWave' in logs
    finally:
        await tools.close_waveform()


async def test_real_ui_tool_buttons(user):
    from nicegui import ui
    from sv_studio.ui.layout import Studio
    ws = Workspace(Path(__file__).resolve().parents[2])
    tools = ToolService(ws)
    instances = {}

    @ui.page('/real-studio-test')
    def page():
        instances['studio'] = Studio(ws, tools)

    await user.open('/real-studio-test')
    studio = instances['studio']
    with user:
        studio.project_select.value = 'sv_studio_examples'
        studio.rtl_top.value = 'studio_and'
        studio.tb_top.value = 'tb_studio_and'
        studio.open_file('projects/sv_studio_examples/rtl/designs.sv')
    user.find('Save all').click()
    for label, operation in [('Simulation', 'simulation'), ('Lint', 'lint'), ('Synthesis', 'synthesis'), ('Generate schematic', 'schematic')]:
        user.find(label).click()
        for _ in range(1200):
            await asyncio.sleep(.05)
            if studio.run_result is not None and not tools.busy:
                break
        assert studio.run_result is not None
        assert studio.run_result.operation == operation
        assert studio.run_result.status in {'Passed', 'Warning'}, studio.run_result.detail
    user.find('View SVG').click()
    await asyncio.sleep(.1)
    await user.should_see('Zoom with slider; drag scrollbars to pan.')
    # Native waveform remains accessible after synthesis/schematic, with no viewer process.
    user.find('Close').click()
    user.find('Waveform').click()
    try:
        for _ in range(1200):
            await asyncio.sleep(.05)
            if studio.waveform_viewer and studio.waveform_viewer.canvas:
                break
        assert studio.tabs.value == '__waveform__'
        assert studio.waveform_viewer.canvas is not None
        data = studio.waveform_viewer.canvas.props['data']
        assert data['end'] > 0
        assert any(s['name'].endswith('.a') for s in data['signals'])
        assert any(len(changes) > 1 for changes in data['changes'].values())
        assert tools.viewer_name is None
    finally:
        await tools.close_waveform()
