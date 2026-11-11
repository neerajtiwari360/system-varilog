import asyncio

import pytest
from nicegui import ui

from sv_studio.services.tools import ToolService
from sv_studio.tests.test_services import FixtureRunner, ws
from sv_studio.ui.layout import Studio


@pytest.fixture
async def studio(user, ws):
    instances = {}
    @ui.page('/closing-test')
    def page():
        instances['studio'] = Studio(ws, ToolService(ws, FixtureRunner(ws)))
    await user.open('/closing-test')
    return instances['studio']


async def test_close_clean_file_reopen_and_close_last(studio, user, ws):
    first, second = 'projects/demo/rtl/dependency.sv', 'projects/demo/rtl/unrelated_name.sv'
    with user:
        studio.open_file(first)
        studio.open_file(second)
    assert studio.tab_labels[second].props['title'] == second
    await user.should_not_see(kind=ui.tooltip, content=second)
    user.find(marker='close-tab-' + second).click()
    await asyncio.sleep(.02)
    assert studio.tabs.value == first
    assert second not in studio.buffers and second not in studio.tab_panels
    with user:
        studio.open_file(second)
    assert studio.buffers[second] == ws.read(second)
    with user:
        studio.close_tab(first)  # closing an inactive tab retains the active file
    assert studio.tabs.value == second
    with user:
        studio.close_tab(second)
    assert studio.tabs.value == '__welcome__'
    assert not studio.tab_order


@pytest.mark.parametrize('action', ['Cancel', 'Discard changes', 'Save and close'])
async def test_unsaved_close_choices(studio, user, ws, action):
    path = 'projects/demo/rtl/dependency.sv'
    original = ws.read(path)
    with user:
        studio.open_file(path)
    user.find(ui.codemirror).type('\n// unsaved change')
    with user:
        studio.close_tab(path)
    await user.should_see('Save changes to dependency.sv?')
    user.find(action).click()
    await asyncio.sleep(.02)
    if action == 'Cancel':
        assert path in studio.buffers and studio.buffers[path] != original
        assert ws.read(path) == original
    elif action == 'Discard changes':
        assert path not in studio.buffers and ws.read(path) == original
    else:
        assert path not in studio.buffers
        assert '// unsaved change' in ws.read(path)


async def test_save_conflict_keeps_tab_open(studio, user, ws):
    path = 'projects/demo/rtl/dependency.sv'
    with user:
        studio.open_file(path)
    user.find(ui.codemirror).type('\n// unsaved')
    ws.save(path, '// externally changed')
    with user:
        studio.close_tab(path)
    user.find('Save and close').click()
    await asyncio.sleep(.02)
    assert path in studio.buffers
    assert ws.read(path) == '// externally changed'


async def test_waveform_can_close_and_reopen(studio, user, ws):
    with user:
        studio.rtl_top.value = 'actual'
        await studio.start('simulation')
        await studio.open_wave()
        studio.close_tab('__waveform__')
    assert studio.waveform_viewer is None
    assert studio.tabs.value == '__welcome__'
    assert not studio.focused
    with user:
        await studio.open_wave()
    assert studio.waveform_viewer.canvas is not None
