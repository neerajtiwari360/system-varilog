"""Bounded native VCD reader. All times remain integer VCD ticks."""
from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class VCD:
    timescale: str = '1 tick (timescale unspecified)'
    end: int = 0
    signals: list[dict] = field(default_factory=list)
    changes: dict[str, list[list]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {'timescale': self.timescale, 'end': self.end, 'signals': self.signals, 'changes': self.changes}


def read_vcd(path: Path) -> VCD:
    if path.stat().st_size > 16_000_000:
        raise ValueError('Native viewer limit: 16 MB VCD. Reduce dump scope or simulation duration.')
    tokens = iter(path.read_text(encoding='utf-8', errors='strict').split())
    data = VCD()
    scopes: list[str] = []
    widths: dict[str, int] = {}
    declared = False

    def directive() -> list[str]:
        parts = []
        for token in tokens:
            if token == '$end':
                return parts
            parts.append(token)
        raise ValueError('Truncated VCD directive (missing $end)')

    try:
        for token in tokens:
            parts = directive()
            if token == '$scope':
                scopes.append(parts[1])
            elif token == '$upscope':
                scopes.pop()
            elif token == '$timescale':
                scale = ''.join(parts)
                if not re.fullmatch(r'(1|10|100)(s|ms|us|ns|ps|fs)', scale):
                    raise ValueError('Unsupported VCD timescale: ' + scale)
                data.timescale = scale
            elif token == '$var':
                kind, width_text, code, reference, *extra = parts
                width = int(width_text)
                if not 1 <= width <= 4096:
                    raise ValueError('Signal width must be between 1 and 4096 bits')
                if code in widths and widths[code] != width:
                    raise ValueError('VCD aliases have inconsistent widths')
                widths[code] = width
                data.changes.setdefault(code, [])
                data.signals.append({'name': '.'.join([*scopes, reference]) + ''.join(extra), 'code': code, 'width': width, 'kind': kind})
                if len(data.signals) > 4096:
                    raise ValueError('Native viewer limit: 4096 declared signals')
            elif token == '$enddefinitions':
                declared = True
                break
        if not declared or not data.signals:
            raise ValueError('VCD has no signal definitions')
        time = count = 0
        dumping = True
        for token in tokens:
            if token.startswith('#'):
                updated = int(token[1:])
                if updated < time or updated > 2**53 - 1:
                    raise ValueError('VCD timestamps must be increasing safe integers')
                time = data.end = updated
                continue
            if token in {'$dumpvars', '$dumpall', '$end', '$dumpon', '$dumpoff'}:
                if token == '$dumpoff':
                    dumping = False
                    for code in data.changes:
                        data.changes[code].append([time, 'x' * widths[code]])
                        count += 1
                        if count > 500_000:
                            raise ValueError('Native viewer limit: 500,000 value changes')
                elif token in {'$dumpon', '$dumpvars', '$dumpall'}:
                    dumping = True
                continue
            if token.startswith('$'):
                directive()
                continue
            binary = False
            if token[0].lower() in 'brs':
                value, code = token[1:], next(tokens)
                binary = token[0].lower() == 'b'
                if binary:
                    if not re.fullmatch('[01xzXZ]+', value):
                        raise ValueError('Invalid VCD binary vector')
                    value = value.lower()
            elif token[0].lower() in '01xz':
                value, code = token[0].lower(), token[1:]
                binary = True
            else:
                raise ValueError('Unsupported VCD value record: ' + token[:60])
            if code not in widths:
                raise ValueError('VCD references an undeclared signal code')
            if not dumping:
                continue
            if binary:
                if len(value) > widths[code]:
                    raise ValueError('VCD value exceeds declared signal width')
                value = value.rjust(widths[code], value[0] if value[0] in 'xz' else '0')
            changes = data.changes[code]
            if changes and changes[-1][0] == time:
                changes[-1][1] = value
            elif not changes or changes[-1][1] != value:
                changes.append([time, value])
            count += 1
            if count > 500_000:
                raise ValueError('Native viewer limit: 500,000 value changes')
    except (IndexError, StopIteration) as e:
        raise ValueError('Truncated or malformed VCD') from e
    return data
