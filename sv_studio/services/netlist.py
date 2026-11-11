"""Count instantiated leaf cells, including repeated hierarchical instances."""
from collections import Counter


def leaf_cell_counts(modules: dict, top: str) -> dict[str, int]:
    cache: dict[str, Counter] = {}

    def count(name: str, ancestors: frozenset[str]) -> Counter:
        if name in ancestors:
            raise ValueError('Recursive module hierarchy in synthesized netlist')
        if name in cache:
            return cache[name]
        totals: Counter = Counter()
        for cell in modules[name].get('cells', {}).values():
            kind = cell['type']
            module = modules.get(kind)
            blackbox = module and str(module.get('attributes', {}).get('blackbox', '0')).strip('0')
            if module is not None and not blackbox:
                totals.update(count(kind, ancestors | {name}))
            else:
                totals[kind] += 1
        cache[name] = totals
        return totals

    return dict(sorted(count(top, frozenset()).items()))
