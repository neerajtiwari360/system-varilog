"""All browser supplied paths pass through Workspace.path before use."""
import json
import os
import re
from pathlib import Path

SOURCE_SUFFIXES = {'.sv', '.v'}
IDENTIFIER = re.compile(r'[A-Za-z_][A-Za-z0-9_$]*\Z')


class Workspace:
    def __init__(self, root: Path):
        self.root = root.resolve(strict=True)

    def path(self, relative: str | Path) -> Path:
        p = Path(relative)
        if p.is_absolute() or '..' in p.parts or ':' in str(relative) or '\\' in str(relative):
            raise ValueError('Use a workspace-relative path without traversal')
        resolved = (self.root / p).resolve()
        if not resolved.is_relative_to(self.root):
            raise ValueError('Path escapes workspace (possibly through a symlink)')
        # Refuse linked paths even when the target is still inside the workspace.
        current = self.root
        for part in p.parts:
            current /= part
            if current.is_symlink() or (hasattr(current, 'is_junction') and current.is_junction()):
                raise ValueError('Linked paths are not supported')
        return resolved

    def relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def projects(self) -> list[str]:
        base = self.path('projects')
        return sorted(p.name for p in base.iterdir() if p.is_dir() and not p.is_symlink()) if base.exists() else []

    def project(self, name: str) -> Path:
        if name not in self.projects():
            raise ValueError('Unknown project')
        return self.path(f'projects/{name}')

    def files(self, project: str, sources_only: bool = False) -> list[str]:
        base = self.project(project)
        result = []
        for directory, dirs, files in os.walk(base, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not (Path(directory) / d).is_symlink() and d not in {'.git', 'node_modules', '.venv'})
            for name in sorted(files):
                p = Path(directory) / name
                rel = self.relative(p)
                try:
                    self.path(rel)
                except ValueError:
                    continue
                if not sources_only or (p.suffix in SOURCE_SUFFIXES and 'build' not in p.relative_to(base).parts):
                    result.append(rel)
        return result

    @staticmethod
    def is_tb(source: str) -> bool:
        return any(p in {'tb', 'testbench', 'testbenches', 'tests'} for p in Path(source).parts)

    def read(self, relative: str) -> str:
        p = self.path(relative)
        if p.stat().st_size > 4_000_000:
            raise ValueError('File is too large for the editor; download it instead')
        return p.read_text(encoding='utf-8')

    def save(self, relative: str, text: str) -> None:
        p = self.path(relative)
        if p.suffix not in {'.sv', '.v', '.svh', '.vh', '.txt', '.md', '.json', '.vlt', '.mem', '.hex'}:
            raise ValueError('Unsupported editable file type')
        if not p.is_relative_to(self.path('projects')) or 'build' in p.relative_to(self.root).parts:
            raise ValueError('Only project source files can be edited')
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')

    def create(self, project: str, relative: str) -> str:
        base = self.project(project)
        if not re.fullmatch(r'(rtl|tb)/[A-Za-z_][A-Za-z0-9_/-]*\.(sv|v)', relative):
            raise ValueError('Use rtl/name.sv or tb/name.sv with simple identifiers')
        p = self.path(self.relative(base) + '/' + relative)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('x', encoding='utf-8') as f:
            f.write('// New SystemVerilog source\n')
        return self.relative(p)

    def modules(self, sources: list[str]) -> dict[str, str]:
        # Candidate discovery only. Tools do elaboration; never infer a dependency graph here.
        modules = {}
        for source in sources:
            text = self.read(source)
            text = re.sub(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"', ' ', text, flags=re.S)
            for name in re.findall(r'\bmodule\s+(?:(?:automatic|static)\s+)?([A-Za-z_][\w$]*)', text):
                modules[name] = source
        return modules

    def config(self, project: str) -> dict:
        p = self.project(project) / 'sv_studio.json'
        return json.loads(self.read(self.relative(p))) if p.exists() else {}

    def sources(self, project: str, selected: list[str] | None = None) -> list[str]:
        config = self.config(project)
        manifest = config.get('sources')
        files = ([f'projects/{project}/{s}' for s in manifest] if manifest is not None
                 else self.files(project, sources_only=True)) if selected is None else selected
        if not files:
            raise ValueError('Select at least one source file')
        for s in files:
            p = self.path(s)
            if not p.is_relative_to(self.project(project)) or not p.is_file() or p.suffix not in SOURCE_SUFFIXES or 'build' in p.relative_to(self.project(project)).parts:
                raise ValueError(f'Invalid source: {s}')
        return list(dict.fromkeys(files))
