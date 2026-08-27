"""Bounded, streaming subprocess execution with actionable persistent logs."""

from __future__ import annotations

import math
import os
import shlex
import signal
import subprocess
import tempfile
from collections import deque
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from time import monotonic
from typing import Mapping

from .environment import failure_hint


class CommandFailure(RuntimeError):
    def __init__(
        self,
        command: list[str],
        returncode: int,
        output: str,
        log_path: Path,
        *,
        timed_out: bool = False,
    ):
        self.command = command
        self.returncode = returncode
        self.output = output
        self.log_path = log_path
        self.timed_out = timed_out
        super().__init__(
            f"{'Timeout' if timed_out else 'Fallo'} ejecutando: {shlex.join(command)}\n"
            f"Código de salida: {returncode}\nLog completo: {log_path}\n"
            f"Últimas líneas:\n{output or '(sin salida)'}\n{failure_hint(output)}"
        )


def _stop_owned_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait(timeout=3)
    except ProcessLookupError:
        pass


def run_logged(
    command: list[str],
    *,
    root: Path,
    environment: Mapping[str, str] | None = None,
    timeout: float = 1200,
    label: str = "setup",
) -> Path:
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("El timeout debe ser positivo")
    directory = root / "outputs" / "runtime" / "setup"
    directory.mkdir(parents=True, exist_ok=True)
    recent: deque[str] = deque(maxlen=40)
    queue: Queue[str | None] = Queue()
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix=f"{label}-",
        suffix=".log",
        dir=directory,
        delete=False,
    ) as log:
        log_path = Path(log.name)
        log.write(f"command={shlex.join(command)}\n")
        log.flush()
        print(f"[{label}] command={shlex.join(command)} log={log_path}", flush=True)
        try:
            process = subprocess.Popen(
                command,
                cwd=root,
                env=dict(environment) if environment is not None else None,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                start_new_session=os.name == "posix",
            )
        except OSError as error:
            log.write(str(error) + "\n")
            raise CommandFailure(command, 127, str(error), log_path) from error

        def read_output() -> None:
            assert process.stdout is not None
            try:
                for line in process.stdout:
                    queue.put(line)
            finally:
                queue.put(None)

        reader = Thread(target=read_output, daemon=True)
        reader.start()
        started = last_output = monotonic()
        ended = False
        timed_out = False
        try:
            while not ended:
                if monotonic() - started >= timeout:
                    timed_out = True
                    _stop_owned_process(process)
                    break
                try:
                    line = queue.get(timeout=0.2)
                except Empty:
                    if monotonic() - last_output >= 30:
                        print(
                            f"[{label}] status=running elapsed_s={monotonic() - started:.0f} log={log_path}",
                            flush=True,
                        )
                        last_output = monotonic()
                    continue
                if line is None:
                    ended = True
                else:
                    recent.append(line)
                    log.write(line)
                    log.flush()
                    print(line, end="", flush=True)
                    last_output = monotonic()
            remaining = max(0.1, timeout - (monotonic() - started))
            try:
                code = process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                timed_out = True
                _stop_owned_process(process)
                code = process.returncode or 124
        except BaseException:
            _stop_owned_process(process)
            raise
        finally:
            reader.join(timeout=2)
            if not reader.is_alive() and process.stdout is not None:
                process.stdout.close()
        while not queue.empty():
            line = queue.get_nowait()
            if line is not None:
                recent.append(line)
                log.write(line)
        log.write(f"\nreturncode={code} timed_out={timed_out}\n")
        if code or timed_out:
            raise CommandFailure(
                command,
                code or 124,
                "".join(recent).strip(),
                log_path,
                timed_out=timed_out,
            )
    return log_path
