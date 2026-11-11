import pytest
from sv_studio.services.netlist import leaf_cell_counts


def test_statistics_count_repeated_instances_and_ignore_unused_modules():
    modules = {
        'top': {'cells': {'a': {'type':'child'}, 'b': {'type':'child'}, 'c': {'type':'$_AND_'}}},
        'child': {'cells': {'ff': {'type':'$_DFF_P_'}, 'mux': {'type':'$_MUX_'}}},
        'unused': {'cells': {'other': {'type':'$_OR_'}}},
    }
    assert leaf_cell_counts(modules, 'top') == {'$_AND_':1, '$_DFF_P_':2, '$_MUX_':2}


def test_statistics_keep_blackboxes_as_opaque_cells():
    modules = {'top': {'cells': {'a': {'type':'external'}}},
               'external': {'attributes': {'blackbox':'0001'}, 'cells': {}}}
    assert leaf_cell_counts(modules, 'top') == {'external':1}


def test_recursive_netlist_rejected():
    with pytest.raises(ValueError, match='Recursive'):
        leaf_cell_counts({'top': {'cells': {'a': {'type':'top'}}}}, 'top')
