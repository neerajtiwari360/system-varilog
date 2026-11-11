import asyncio
from nicegui import ui

from sv_studio.tests.test_tab_closing import studio
from sv_studio.tests.test_services import ws


async def test_netlist_log_and_svg_share_closable_central_tabs(studio, user, ws):
    source = 'projects/demo/rtl/unrelated_name.sv'
    with user:
        studio.open_file(source)
    result = await studio.tools.run('demo', 'synthesis', 'actual', '', ws.sources('demo'))
    assert result.status == 'Passed'
    with user:
        studio.run_result = result
        studio.show_result()
    user.find('netlist.v').click()
    await asyncio.sleep(.02)
    assert studio.tabs.value.endswith('/netlist.v')
    opened = []
    for artifact in ['work/build/netlist.v', 'work/build/netlist.json', 'synthesis.log', 'work/build/schematic.svg']:
        path = ws.relative(studio.tools.artifact(result, artifact))
        with user:
            studio.open_artifact(result, artifact)
        assert studio.tabs.value == path
        assert path in studio.tab_panels and path not in studio.buffers
        if path in studio.editors:
            assert not studio.editors[path].enabled
        opened.append(path)
    await user.should_see('Zoom with slider; drag scrollbars to pan.')
    await user.should_not_see(ui.dialog)
    previous_count = len(studio.tab_order)
    with user:
        studio.open_file(opened[0])  # same artifact through another UI entry point
    assert len(studio.tab_order) == previous_count
    assert studio.tabs.value == opened[0]
    for path in opened:
        user.find(marker='close-tab-' + path).click()
        await asyncio.sleep(.01)
        assert path not in studio.tab_order
    assert studio.tabs.value == source


async def test_explorer_svg_and_binary_open_in_tabs(studio, user, ws):
    directory = ws.path('projects/demo/build')
    directory.mkdir()
    svg = directory / 'design.svg'
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    binary = directory / 'sim.vvp'
    binary.write_bytes(b'\x00\x01binary')
    for file in (svg, binary):
        path = ws.relative(file)
        with user:
            studio.open_file(path)
        assert studio.tabs.value == path and path not in studio.buffers
    await user.should_see('This file type has no inline preview. Download it to inspect it locally.')


async def test_vcd_artifact_opens_native_view_in_its_own_tab(studio, user, ws):
    result = await studio.tools.run('demo', 'simulation', 'actual', 'bench', ws.sources('demo'))
    artifact = 'work/build/waves.vcd'
    path = ws.relative(studio.tools.artifact(result, artifact))
    with user:
        studio.open_artifact(result, artifact)
    for _ in range(100):
        await asyncio.sleep(.02)
        if studio.document_tasks[path].done():
            break
    assert studio.tabs.value == path
    assert path in studio.tab_panels and path not in studio.buffers
    from sv_studio.ui.waveform_canvas import WaveformCanvas
    assert user.find(WaveformCanvas).elements
    with user:
        studio.close_tab(path)
    assert path not in studio.document_tasks
