import asyncio
import json
import sys
from pathlib import Path

import pytest

from sv_studio.services.workspace import Workspace
from sv_studio.services.runner import DockerRunner, ToolError
from sv_studio.services.tools import ToolService


@pytest.fixture
def ws(tmp_path):
    project = tmp_path / 'projects/demo'
    (project / 'rtl').mkdir(parents=True)
    (project / 'tb').mkdir()
    (project / 'rtl/unrelated_name.sv').write_text('// module fake;\nmodule actual; endmodule')
    (project / 'rtl/dependency.sv').write_text('module dependency; endmodule')
    (project / 'tb/bench.sv').write_text('module bench; actual dut(); endmodule')
    return Workspace(tmp_path)


def test_discovery_modules_manifest(ws):
    assert ws.projects() == ['demo']
    sources = ws.sources('demo')
    assert set(ws.modules(sources)) == {'actual', 'dependency', 'bench'}
    assert len(sources) == 3
    ws.save('projects/demo/sv_studio.json', json.dumps({'sources': ['rtl/dependency.sv', 'rtl/unrelated_name.sv']}))
    assert ws.sources('demo')[0].endswith('dependency.sv')


def test_files_and_validation(ws):
    path = ws.create('demo', 'rtl/new.sv')
    ws.save(path, 'module renamed; endmodule')
    assert ws.read(path) == 'module renamed; endmodule'
    with pytest.raises(FileExistsError):
        ws.create('demo', 'rtl/new.sv')
    for invalid in ['../escape', 'C:/escape', 'projects/../../escape', 'projects\\demo', '/absolute']:
        with pytest.raises(ValueError):
            ws.path(invalid)
    for invalid in ['../bad.sv', 'rtl/bad name.sv', 'tb/-bad.sv']:
        with pytest.raises(ValueError):
            ws.create('demo', invalid)
    with pytest.raises(ValueError):
        ws.save('compose.yml', 'overwrite')
    with pytest.raises((ValueError, FileNotFoundError)):
        ws.sources('demo', ['projects/demo/rtl/missing.sv'])


def test_symlink_escape(ws, tmp_path):
    try:
        (tmp_path / 'projects/demo/linked').symlink_to(tmp_path.parent, target_is_directory=True)
    except OSError:
        pytest.skip('Windows symlink privilege unavailable')
    with pytest.raises(ValueError):
        ws.path('projects/demo/linked/outside')


class FixtureRunner(DockerRunner):
    """Deterministic process boundary for unit tests; never used by application."""
    def __init__(self, ws, scenario='success'):
        super().__init__(ws.root)
        self.ws = ws
        self.scenario = scenario

    async def execute(self, args, output, **kwargs):
        cwd = self.ws.root / args[8].removeprefix('/workspace/')
        stage = args[10]
        code, text = 0, 'tool version\n'
        if stage == 'iverilog' and '-o' in args:
            if self.scenario == 'compile':
                code, text = 1, 'rtl/unrelated_name.sv:1: error: syntax error\n'
            else:
                (cwd / 'build/sim.vvp').write_text('unit test process fixture')
        if stage == 'vvp' and '-V' not in args:
            text = 'COMPLETE\n'
            if self.scenario == 'runtime': code, text = 1, 'FATAL: test failed\n'
            if self.scenario == 'reported': text = 'ERROR: assertion failed\nCOMPLETE\n'
            if self.scenario == 'cancel':
                self.cancelled = True
                code, text = -1, 'cancelled'
            if self.scenario != 'no_vcd':
                (cwd / 'build/waves.vcd').write_text('$timescale 1ns $end\n$scope module bench $end\n$var wire 1 ! clk $end\n$upscope $end\n$enddefinitions $end\n#0\n0!\n#5\n1!\n#10\n0!')
        if stage == 'verilator' and '--lint-only' in args:
            text = '%Warning-WIDTH: rtl/unrelated_name.sv:2: width mismatch\n ... For warning description see https://verilator.org/warn/WIDTH\n'
        if stage == 'yosys' and '-s' in args:
            if self.scenario == 'synth_error': code, text = 1, 'ERROR: unsupported syntax'
            else:
                (cwd / 'build/netlist.json').write_text(json.dumps({'modules': {'actual': {'cells': {'a': {'type': '$_AND_'}}}}}))
                (cwd / 'build/netlist.v').write_text('module actual; endmodule')
                (cwd / 'build/schematic.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
        output(text)
        return code, text


async def invoke(ws, scenario='success', operation='simulation', success=True):
    if success:
        ws.save('projects/demo/sv_studio.json', json.dumps({'success': {'bench': 'COMPLETE'}}))
    service = ToolService(ws, FixtureRunner(ws, scenario))
    run = await service.run('demo', operation, 'actual', 'bench', ws.sources('demo'))
    return service, run


@pytest.mark.parametrize('scenario,status', [('success','Passed'), ('compile','Failed'), ('runtime','Failed'),
    ('reported','Failed'), ('cancel','Cancelled'), ('no_vcd','Passed')])
async def test_simulation_results(ws, scenario, status):
    service, run = await invoke(ws, scenario)
    assert run.status == status
    assert run.ended
    assert service.history('demo')[0].id == run.id
    assert all('compose' in command['argv'] for command in run.commands)
    if scenario == 'compile':
        assert not any(c['stage'] == 'simulation' for c in run.commands)
    if scenario == 'no_vcd':
        assert not any(a.endswith('.vcd') for a in run.artifacts)


async def test_unconfigured_execution_not_pass(ws):
    _, run = await invoke(ws, success=False)
    assert run.status == 'Warning'


async def test_independent_runs_and_dependency_selection(ws):
    service, first = await invoke(ws)
    second = await service.run('demo', 'simulation', 'actual', 'bench', ws.sources('demo'))
    assert first.id != second.id
    assert service.directory(first) != service.directory(second)
    compile_args = next(c['argv'] for c in first.commands if c['stage'] == 'compile')
    assert 'rtl/dependency.sv' in compile_args
    assert 'rtl/unrelated_name.sv' in compile_args
    assert '-s' in compile_args and 'bench' in compile_args
    with pytest.raises(ValueError):
        service.artifact(first, '../' + second.id + '/metadata.json')


async def test_lint_and_synthesis(ws):
    _, lint = await invoke(ws, operation='lint')
    assert lint.status == 'Warning'
    assert lint.diagnostics[0]['line'] == 2
    assert len(lint.diagnostics) == 1
    assert not any('/tb/' in s for s in lint.sources)
    _, synth = await invoke(ws, operation='synthesis')
    assert synth.status == 'Passed'
    assert synth.statistics == {'$_AND_': 1}
    assert 'work/build/schematic.svg' in synth.artifacts
    _, bad = await invoke(ws, scenario='synth_error', operation='schematic')
    assert bad.status == 'Failed'
    assert not any(a.endswith('.svg') for a in bad.artifacts)


async def test_invalid_top(ws):
    service = ToolService(ws)
    with pytest.raises(ValueError, match='not in the selected'):
        await service.run('demo', 'lint', 'wrong', 'bench', ws.sources('demo'))


async def test_process_timeout_and_cancellation(ws):
    runner = DockerRunner(ws.root, timeout=.1)
    with pytest.raises(ToolError, match='timed out'):
        await runner.execute([sys.executable, '-c', 'import time; time.sleep(10)'], lambda _: None)
    assert runner.active.returncode is not None
    runner = DockerRunner(ws.root)
    task = asyncio.create_task(runner.execute([sys.executable, '-c', 'import time; time.sleep(10)'], lambda _: None))
    while runner.active is None:
        await asyncio.sleep(.01)
    await runner.stop()
    await task
    assert runner.cancelled and runner.active.returncode is not None
