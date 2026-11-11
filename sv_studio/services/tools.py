import asyncio
import json
import re
import shutil
import uuid
from pathlib import Path
from typing import Callable

from sv_studio.models import Run, now
from sv_studio.services.runner import DockerRunner, ToolError
from sv_studio.services.workspace import Workspace, IDENTIFIER


class ToolService:
    def __init__(self, workspace: Workspace, runner: DockerRunner | None = None):
        self.ws = workspace
        self.runner = runner or DockerRunner(workspace.root)
        self.busy = False
        self.viewer_name: str | None = None

    def directory(self, run: Run) -> Path:
        return self.ws.path(f'build/sv_studio/{run.project}/{run.id}')

    def persist(self, run: Run) -> None:
        directory = self.directory(run)
        run.artifacts = sorted(p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file() and p.name != 'metadata.json')
        (directory / 'metadata.json').write_text(json.dumps(run.to_dict(), indent=2), encoding='utf-8')

    def history(self, project: str) -> list[Run]:
        self.ws.project(project)
        base = self.ws.path(f'build/sv_studio/{project}')
        result = []
        for p in sorted(base.glob('*/metadata.json'), reverse=True):
            try:
                data = json.loads(self.ws.read(self.ws.relative(p)))
                run = Run(**data)
                if self.directory(run) != p.parent or run.project != project:
                    continue
                result.append(run)
            except (ValueError, OSError, TypeError):
                continue
        return result

    def artifact(self, run: Run, name: str) -> Path:
        if name not in run.artifacts:
            raise ValueError('Artifact does not belong to this run')
        p = self.ws.path(self.ws.relative(self.directory(run)) + '/' + name)
        if not p.is_relative_to(self.directory(run)):
            raise ValueError('Invalid artifact')
        return p

    async def run(self, project: str, operation: str, rtl_top: str, tb_top: str,
                  selected: list[str], output: Callable[[str], None] = lambda _: None) -> Run:
        if self.busy:
            raise ValueError('A tool is already running')
        if operation not in {'simulation', 'lint', 'synthesis', 'schematic'}:
            raise ValueError('Unknown operation')
        sources = self.ws.sources(project, selected)
        top = tb_top if operation == 'simulation' else rtl_top
        if not IDENTIFIER.fullmatch(top or ''):
            raise ValueError('Select a valid top module')
        if operation != 'simulation':
            sources = [s for s in sources if not self.ws.is_tb(s)]
        if top not in self.ws.modules(sources):
            raise ValueError(f'Module {top} is not in the selected sources. Select its source and dependencies.')
        config = self.ws.config(project)
        criterion = config.get('success', {}).get(tb_top)
        if criterion is not None and (not isinstance(criterion, str) or not criterion):
            raise ValueError('Success criteria must be nonempty literal log markers')
        run = Run(now().replace(':', '').replace('.', '-') + '-' + uuid.uuid4().hex[:8],
                  project, operation, rtl_top, tb_top, sources)
        directory = self.directory(run)
        directory.mkdir(parents=True)
        self.persist(run)
        self.busy = True
        self.runner.cancelled = False
        try:
            # A per-run project snapshot preserves relative test data paths and isolates
            # conventional $dumpfile("build/...") output from every other run.
            snapshot = directory / 'work'
            snapshot.mkdir()
            base = self.ws.project(project)
            for source in self.ws.files(project):
                rel = self.ws.path(source).relative_to(base)
                if 'build' in rel.parts or rel.suffix.lower() in {'.vcd', '.vvp', '.fst', '.lxt', '.lxt2'}:
                    continue
                target = snapshot / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(self.ws.path(source), target)
            (snapshot / 'build').mkdir(exist_ok=True)
            cwd = '/workspace/' + self.ws.relative(snapshot)
            source_args = [self.ws.path(s).relative_to(base).as_posix() for s in sources]
            # Yosys uses its own command language: restrict source names before quoting.
            if any(not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_./-]*', s) for s in source_args):
                raise ValueError('Tool sources require simple names (letters, digits, _, -, . and /)')
            include_dirs = sorted({str(Path(s).parent).replace('\\', '/') for s in source_args} | {'.'})

            async def command(stage: str, args: list[str], version: bool = False) -> tuple[int, str]:
                if self.runner.cancelled:
                    raise ToolError('Cancelled before next command')
                command_args = [self.runner.docker, 'compose', 'run', '--rm', '--no-deps', '--name',
                                'svstudio-' + uuid.uuid4().hex, '--workdir', cwd, 'sim', *args]
                record = {'stage': stage, 'argv': command_args, 'exit_code': None}
                run.commands.append(record)
                self.persist(run)
                output('\n$ ' + json.dumps(command_args) + '\n')
                log_path = directory / (stage + '.log')
                with log_path.open('w', encoding='utf-8') as log_file:
                    def emit(text: str) -> None:
                        log_file.write(text)
                        log_file.flush()
                        output(text)
                    self.runner.container = command_args[6]
                    try:
                        code, text = await self.runner.execute(command_args, emit)
                    finally:
                        self.runner.container = None
                record['exit_code'] = code
                if version:
                    run.versions[args[0]] = text.strip()
                self.persist(run)
                return code, text

            tool = {'simulation': 'iverilog', 'lint': 'verilator', 'synthesis': 'yosys', 'schematic': 'yosys'}[operation]
            code, _ = await command('version', [tool, '-V' if tool in {'iverilog', 'yosys'} else '--version'], True)
            if code:
                raise ToolError(f'{tool} version check failed; inspect version.log')
            if operation == 'simulation':
                code, text = await command('compile', ['iverilog', '-g2012', '-s', top, '-o', 'build/sim.vvp',
                    *[f'-I{d}' for d in include_dirs], *source_args])
                if code:
                    raise ToolError('Compilation failed; check diagnostics and selected dependencies')
                await command('runtime-version', ['vvp', '-V'], True)
                code, text = await command('simulation', ['vvp', 'build/sim.vvp'])
                if code or re.search(r'(?im)\b(?:FAIL(?:ED)?|FATAL|ERROR)\b', text):
                    raise ToolError('Simulation reported a failure')
                if criterion and criterion in text:
                    run.status, run.detail = 'Passed', 'Configured testbench success marker observed'
                else:
                    run.status, run.detail = 'Warning', 'Execution completed; no configured success marker met. Functional verification is not established.'
            elif operation == 'lint':
                lint_config = config.get('lint_config')
                lint_args = []
                if lint_config:
                    p = self.ws.path(f'projects/{project}/{lint_config}')
                    if p.suffix != '.vlt' or not p.is_relative_to(base) or not p.is_file():
                        raise ValueError('lint_config must be a project-local .vlt file')
                    lint_args = [p.relative_to(base).as_posix()]
                code, text = await command('lint', ['verilator', '--lint-only', '-Wall', '-Wno-fatal', '--timing',
                    '--top-module', top, *[f'-I{d}' for d in include_dirs], *lint_args, *source_args])
                if code:
                    raise ToolError('Lint failed')
                run.status = 'Warning' if '%Warning' in text else 'Passed'
                run.detail = 'Lint completed; this is not a functional verification result'
            else:
                await command('graphviz-version', ['dot', '-V'], True)
                script = ('read_verilog -sv ' + ' '.join(f'-I{d}' for d in include_dirs) + ' ' + ' '.join(source_args)
                    + f'; hierarchy -check -top {top}; synth -top {top}; stat; write_json build/netlist.json; '
                    + f'write_verilog -noattr build/netlist.v; show -format svg -prefix build/schematic {top}')
                (snapshot / 'synthesis.ys').write_text(script, encoding='utf-8')
                code, text = await command('synthesis', ['yosys', '-s', 'synthesis.ys'])
                if code:
                    raise ToolError('Yosys/Graphviz failed. The installed read_verilog -sv frontend supports a subset of SystemVerilog; source was not modified.')
                netlist = json.loads((snapshot / 'build/netlist.json').read_text())
                for cell in netlist['modules'][top].get('cells', {}).values():
                    kind = cell['type']
                    run.statistics[kind] = run.statistics.get(kind, 0) + 1
                if not (snapshot / 'build/schematic.svg').is_file():
                    raise ToolError('No SVG was generated')
                run.status, run.detail = 'Passed', 'Generic synthesis cells; not device utilization or timing closure'
        except (ToolError, OSError, ValueError, KeyError) as e:
            run.status = 'Cancelled' if self.runner.cancelled and 'timed out' not in str(e) else 'Failed'
            run.detail = str(e)
            output('\n' + str(e) + '\n')
        finally:
            for p in directory.glob('*.log'):
                for line in p.read_text(encoding='utf-8').splitlines():
                    severity = 'warning' if re.search(r'warning', line, re.I) else 'error' if re.search(r'error|fatal', line, re.I) else None
                    if severity:
                        location = re.search(r'([\w./-]+\.(?:sv|v)):(\d+)', line)
                        run.diagnostics.append({'severity': severity, 'message': line,
                            'file': f'projects/{project}/' + location[1] if location else None,
                            'line': int(location[2]) if location else None})
            run.ended = now()
            self.persist(run)
            self.busy = False
        return run

    async def waveform(self, run: Run, artifact: str) -> str:
        p = self.artifact(run, artifact)
        if p.suffix.lower() != '.vcd':
            raise ValueError('Select a VCD from this simulation run')
        if self.busy:
            raise ValueError('Wait for the active operation')
        self.busy = True
        try:
            await self.close_waveform()
            # The existing wave service accepts paths under projects/<project>/build.
            # A dedicated run copies no stale waveform and uses an explicit path.
            target = self.ws.path(f'projects/{run.project}/build/sv_studio/{run.id}/{p.name}')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
            relative = target.relative_to(self.ws.project(run.project) / 'build').as_posix()
            name = 'svstudio-wave-' + uuid.uuid4().hex
            args = [self.runner.docker, 'compose', 'run', '--rm', '--no-deps', '--name', name, '-d', '-p', '127.0.0.1:6081:6080',
                '-e', f'PROJECT={run.project}', '-e', f'WAVE_FILE={relative}', 'wave']
            code, text = await self.runner.execute(args, lambda _: None, timeout=30)
            if code:
                raise ToolError(text + '\nPort 6081 may be occupied by a previous viewer. Stop that viewer container first.')
            self.viewer_name = name
            # Docker's port proxy can accept TCP before websockify serves HTTP.
            for _ in range(75):
                writer = None
                try:
                    reader, writer = await asyncio.wait_for(asyncio.open_connection('127.0.0.1', 6081), 1)
                    writer.write(b'GET /vnc.html HTTP/1.0\r\nHost: localhost\r\n\r\n')
                    await writer.drain()
                    status = await asyncio.wait_for(reader.readline(), 1)
                    if b' 200 ' in status:
                        break
                except (OSError, TimeoutError):
                    pass
                finally:
                    if writer:
                        writer.close()
                        try:
                            await writer.wait_closed()
                        except OSError:
                            pass
                await asyncio.sleep(.2)
            else:
                _, logs = await self.runner.execute([self.runner.docker, 'logs', name], lambda _: None)
                await self.close_waveform()
                raise ToolError('Waveform viewer did not become ready: ' + logs)
            return 'http://127.0.0.1:6081/vnc.html?autoconnect=true&resize=scale'
        finally:
            self.busy = False

    async def close_waveform(self) -> None:
        if self.viewer_name:
            name, self.viewer_name = self.viewer_name, None
            code, text = await self.runner.execute([self.runner.docker, 'rm', '-f', name], lambda _: None, timeout=15)
            if code and 'No such container' not in text:
                raise ToolError('Could not stop previous SV Studio viewer: ' + text)
