"""Cancellable Docker subprocess execution, with no browser controlled shell commands."""
import asyncio
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Callable

log = logging.getLogger(__name__)


class ToolError(RuntimeError):
    pass


class DockerRunner:
    def __init__(self, root: Path, timeout: float = 120):
        self.root = root
        self.timeout = timeout
        candidates = [Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs/DockerDesktop/resources/bin/docker.exe',
                      Path(os.environ.get('ProgramFiles', '')) / 'Docker/Docker/resources/bin/docker.exe']
        self.docker = shutil.which('docker') or 'docker'
        if self.docker == 'docker':
            for candidate in candidates:
                try:
                    if candidate.is_file():
                        self.docker = str(candidate)
                        break
                except OSError:
                    continue
        self.active: asyncio.subprocess.Process | None = None
        self.container: str | None = None
        self.cancelled = False

    async def stop(self) -> None:
        self.cancelled = True
        if self.container:
            # Kill the container, not merely the Docker CLI; otherwise vvp may survive.
            try:
                p = await asyncio.create_subprocess_exec(self.docker, 'rm', '-f', self.container,
                    cwd=self.root, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
                await asyncio.wait_for(p.communicate(), 15)
            except (OSError, TimeoutError):
                log.exception('Container cleanup failed: %s', self.container)
        if self.active and self.active.returncode is None:
            self.active.kill()
            await self.active.wait()

    async def execute(self, args: list[str], output: Callable[[str], None], *, timeout: float | None = None) -> tuple[int, str]:
        log.info('command=%s', json.dumps(args))
        try:
            self.active = await asyncio.create_subprocess_exec(*args, cwd=self.root,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        except OSError as e:
            raise ToolError(f'Cannot launch {args[0]}: {e}. Check Docker Desktop and PATH.') from e
        chunks: list[str] = []

        async def consume() -> None:
            assert self.active and self.active.stdout
            while data := await self.active.stdout.read(4096):
                text = data.decode('utf-8', errors='replace')
                chunks.append(text)
                output(text)
            await self.active.wait()

        try:
            await asyncio.wait_for(consume(), timeout or self.timeout)
        except TimeoutError as e:
            await self.stop()
            raise ToolError('Execution timed out; container cleanup requested') from e
        finally:
            if self.active and self.active.returncode is None:
                await self.stop()
        return self.active.returncode or 0, ''.join(chunks)

    async def tool(self, name: str, cwd: str, command: list[str], output: Callable[[str], None]) -> tuple[int, str, list[str]]:
        self.container = name
        args = [self.docker, 'compose', 'run', '--rm', '--no-deps', '--name', name,
                '--workdir', cwd, 'sim', *command]
        try:
            code, text = await self.execute(args, output)
            return code, text, args
        finally:
            self.container = None
