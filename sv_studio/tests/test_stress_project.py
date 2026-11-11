"""Real UI-to-Docker acceptance test for the hierarchical streaming stress design."""
import asyncio
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import uuid

import pytest
from nicegui import ui

from sv_studio.services.tools import ToolService
from sv_studio.services.vcd import read_vcd
from sv_studio.services.workspace import Workspace
from sv_studio.ui.layout import Studio

pytestmark = pytest.mark.skipif(os.environ.get('SV_STUDIO_DOCKER_TESTS') != '1', reason='Opt-in real Docker stress test')


async def test_streaming_stress_through_studio(user):
    ws = Workspace(Path(__file__).resolve().parents[2])
    tools = ToolService(ws)
    instances = {}
    report = {}

    @ui.page('/stress-acceptance')
    def page():
        instances['studio'] = Studio(ws, tools)

    await user.open('/stress-acceptance')
    studio = instances['studio']
    with user:
        studio.project_select.value = '02_streaming_stress'
        studio.rtl_top.value = 'stress_engine'
        studio.tb_top.value = 'tb_stress_engine'
        studio.open_file('projects/02_streaming_stress/rtl/streaming_engine.sv')
        studio.open_file('projects/02_streaming_stress/tb/tb_stress_engine.sv')
    user.find('Save all').click()

    async def click_operation(label, operation, *, expected=('Passed', 'Warning'), report_key=None):
        user.find(label).click()
        for _ in range(9000):
            await asyncio.sleep(.02)
            if studio.run_result is not None and not tools.busy:
                break
        run = studio.run_result
        assert run is not None and run.operation == operation
        report[report_key or operation] = {'id':run.id, 'status':run.status, 'detail':run.detail,
                             'statistics':run.statistics, 'diagnostics':run.diagnostics}
        # Save evidence even if an operation exposes an application/tool defect.
        evidence = ws.path('build/stress_acceptance.json')
        evidence.write_text(json.dumps(report, indent=2), encoding='utf-8')
        assert run.status in expected, run.detail
        return run

    sim = await click_operation('Simulation', 'simulation')
    assert sim.status == 'Passed', sim.detail
    text = tools.artifact(sim, 'simulation.log').read_text()
    summary = re.search(r'SUMMARY (.+)', text)
    assert summary
    counters = {k:int(v) for k,v in re.findall(r'(\w+)=(\d+)', summary[1])}
    assert counters['accepted'] == counters['checked'] + counters['discarded']
    assert counters['checked'] >= 4000 and counters['stalls'] >= 1000
    assert len(re.findall(r'OPCODE_COVERAGE \d+ \d+', text)) == 8
    report['simulation']['counters'] = counters

    user.find('Waveform').click()
    for _ in range(1000):
        await asyncio.sleep(.02)
        if studio.waveform_viewer and studio.waveform_viewer.canvas:
            break
    assert studio.waveform_viewer.canvas is not None
    data = studio.waveform_viewer.canvas.props['data']
    assert data['end'] > 150_000_000  # 1ps ticks, >150us simulated time
    assert len(data['signals']) >= 15
    assert tools.viewer_name is None
    waveform = read_vcd(tools.artifact(sim, 'work/build/stress_engine.vcd'))
    level_code = next(s['code'] for s in waveform.signals if s['name'].split('[')[0].endswith('.fifo_level'))
    assert max(int(v, 2) for _,v in waveform.changes[level_code] if not re.search('[xz]', v)) == 8
    report['waveform'] = {'signals':len(data['signals']), 'end_ticks':data['end'], 'timescale':data['timescale'],
                          'transitions':sum(len(c) for c in data['changes'].values())}

    lint = await click_operation('Lint', 'lint')
    assert len(lint.diagnostics) == 1  # Intentional module/filename mismatch only.
    synthesis = await click_operation('Synthesis', 'synthesis')
    assert synthesis.status == 'Passed'
    netlist = json.loads(tools.artifact(synthesis, 'work/build/netlist.json').read_text())
    assert 'stress_engine' in netlist['modules']
    assert len(netlist['modules']) >= 3
    assert sum(synthesis.statistics.values()) > 1000
    assert sum(n for kind, n in synthesis.statistics.items() if 'DFF' in kind.upper()) >= 360
    assert not any(t in netlist['modules'] for t in synthesis.statistics)
    hierarchy_report = tools.artifact(synthesis, 'synthesis.log').read_text().rsplit('=== design hierarchy ===', 1)[1]
    yosys_cells = {kind:int(n) for kind,n in re.findall(r'^\s+(\$_\S+)\s+(\d+)\s*$', hierarchy_report, re.M)}
    assert synthesis.statistics == yosys_cells
    assert any('DFF' in t.upper() for m in netlist['modules'].values() for t in (c['type'] for c in m.get('cells', {}).values()))
    assert tools.artifact(synthesis, 'work/build/netlist.v').stat().st_size > 1000
    svg = tools.artifact(synthesis, 'work/build/schematic.svg')
    assert ET.parse(svg).getroot().tag.endswith('svg')
    user.find('View SVG').click()
    await asyncio.sleep(.05)
    await user.should_see('Zoom with slider; drag scrollbars to pan.')
    user.find('Close').click()
    schematic = await click_operation('Generate schematic', 'schematic')
    assert schematic.status == 'Passed' and schematic.id != synthesis.id
    assert ET.parse(tools.artifact(schematic, 'work/build/schematic.svg')).getroot().tag.endswith('svg')

    # Re-run the same scoreboard against the actual synthesized Verilog, not the RTL.
    directory = tools.directory(synthesis)
    cwd = '/workspace/' + ws.relative(directory / 'work')
    post_commands = []
    for stage, args in [
        ('post_synth_compile', ['iverilog', '-g2012', '-s', 'tb_stress_engine', '-o', 'build/post_synth.vvp', 'build/netlist.v', 'tb/tb_stress_engine.sv']),
        ('post_synth_simulation', ['vvp', 'build/post_synth.vvp']),
    ]:
        code, output, argv = await tools.runner.tool('svstudio-check-' + uuid.uuid4().hex, cwd, args, lambda _: None)
        (directory / (stage + '.log')).write_text(output, encoding='utf-8')
        post_commands.append({'stage':stage, 'argv':argv, 'exit_code':code})
        report['post_synthesis'] = {'commands':post_commands, 'status':'Running'}
        ws.path('build/stress_acceptance.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        assert code == 0, output[-4000:]
    assert summary[0] in output
    assert 'STRESS_ENGINE_ALL_CHECKS_COMPLETE' in output
    synthesis.commands.extend(post_commands)
    tools.persist(synthesis)
    report['post_synthesis']['status'] = 'Passed'
    report['post_synthesis']['counters'] = counters

    with user:
        studio.tb_top.value = 'tb_stress_expected_failure'
    failed = await click_operation('Simulation', 'simulation', expected=('Failed',), report_key='expected_failure')
    assert 'Intentional negative-control failure' in tools.artifact(failed, 'simulation.log').read_text()
    assert 'Simulation reported a failure' in failed.detail
    with user:
        studio.tb_top.value = 'tb_stress_engine'
    ws.path('build/stress_acceptance.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
