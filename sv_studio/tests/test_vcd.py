import pytest
from sv_studio.services.vcd import read_vcd


HEADER = '''$date today $end
$timescale 10 ps $end
$scope module tb $end
$var wire 1 ! clk $end
$var reg 4 " data [3:0] $end
$scope module dut $end
$var wire 1 ! clk_alias $end
$upscope $end
$upscope $end
$enddefinitions $end
'''


def parse(tmp_path, text):
    p = tmp_path / 'wave.vcd'
    p.write_text(text)
    return read_vcd(p)


def test_vcd_aliases_timescale_vectors_unknowns_and_delta_cycles(tmp_path):
    data = parse(tmp_path, HEADER + '$dumpvars\n0!\nbx "\n$end\n#5\n1!\nb11 "\n#5\n0!\n#10\nbz "\n#20')
    assert data.timescale == '10ps'
    assert data.end == 20
    assert [s['name'] for s in data.signals] == ['tb.clk', 'tb.data[3:0]', 'tb.dut.clk_alias']
    assert data.changes['!'] == [[0, '0'], [5, '0']]
    assert data.changes['"'] == [[0, 'xxxx'], [5, '0011'], [10, 'zzzz']]


def test_vcd_dump_off_is_unknown_not_held(tmp_path):
    data = parse(tmp_path, HEADER + '#0\n1!\n#3\n$dumpoff\nx!\n$end\n#8\n$dumpon\n0!\n$end')
    assert data.changes['!'] == [[0, '1'], [3, 'x'], [8, '0']]


@pytest.mark.parametrize('tail', ['#5\n#3', '#0\n1unknown', '#0\nb123 "', '#0\nb11111 "', '#9007199254740992', '#0\nb1'])
def test_malformed_vcd_rejected(tmp_path, tail):
    with pytest.raises(ValueError):
        parse(tmp_path, HEADER + tail)


def test_empty_and_truncated_header(tmp_path):
    for text in ['', '$scope module broken', '$enddefinitions $end']:
        with pytest.raises(ValueError):
            parse(tmp_path, text)
