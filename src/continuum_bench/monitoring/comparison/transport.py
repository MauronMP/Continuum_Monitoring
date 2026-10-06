"""Temporary source bundles over SSH, with bounded remote process lifetime."""
from __future__ import annotations

import base64
import io
import json
import math
from pathlib import Path
import shlex
import subprocess
import sys
import zipfile

BOOTSTRAP = '''import base64, io, json, signal, sys, tempfile, zipfile
def terminate(signum, frame):
    raise SystemExit(124)
signal.signal(signal.SIGTERM, terminate)
request = json.load(sys.stdin)
with tempfile.TemporaryDirectory(prefix="continuum-comparison-") as directory:
    zipfile.ZipFile(io.BytesIO(base64.b64decode(request["bundle"]))).extractall(directory)
    sys.path.insert(0, directory)
    from continuum_bench.monitoring.comparison.worker import execute
    print(json.dumps(execute(request["payload"]), allow_nan=False))
'''


def source_bundle() -> bytes:
    root = Path(__file__).resolve().parents[2]
    memory = io.BytesIO()
    with zipfile.ZipFile(memory, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*.py")):
            entry = zipfile.ZipInfo(str(path.relative_to(root.parent)))
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, path.read_bytes())
    return memory.getvalue()


def command(node, inventory, config, program: str, timeout: float):
    python = sys.executable if node.local else inventory.remote_python
    invocation = ["timeout", "--signal=TERM", "--kill-after=3s", f"{timeout}s", python, "-c", program]
    if node.local:
        return invocation
    return ["ssh", "-o", "BatchMode=yes", "-o", f"ConnectTimeout={max(1, math.ceil(config['connect_timeout_seconds']))}",
            "-o", "ServerAliveInterval=5", "-o", "ServerAliveCountMax=2",
            f"{inventory.ssh_user}@{node.host}", shlex.join(invocation)]


def invoke(node, inventory, config, bundle, payload):
    request = json.dumps({"bundle": base64.b64encode(bundle).decode(), "payload": payload})
    try:
        result = subprocess.run(command(node, inventory, config, BOOTSTRAP, config["timeout_seconds"]),
                                input=request, text=True, capture_output=True,
                                timeout=config["timeout_seconds"] + config["connect_timeout_seconds"] + 10)
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "error": "Coordinator transport deadline exceeded; remote GNU timeout bounds execution"}
    except OSError as error:
        return {"status": "failed", "error": f"Transport unavailable: {error}"}
    if result.returncode in (124, 137):
        return {"status": "timeout", "error": result.stderr[-4000:] or "Worker job exceeded the configured deadline"}
    if result.returncode:
        return {"status": "failed", "error": result.stderr[-4000:] or f"Exit {result.returncode}"}
    try:
        response = json.loads(result.stdout)
        if response.get("status") != "completed" or not isinstance(response.get("events"), list):
            raise ValueError("Invalid worker response")
        from .validation import validate_measurement
        validate_measurement(response, len(payload["events"]))
        for received, requested in zip(response["events"], payload["events"]):
            if received["context"] != requested["context"] or received["expected"] != requested["expected"] or received["scenario"] != requested["id"]:
                raise ValueError("Worker returned decisions for a different requested trace")
        return response
    except (ValueError, AttributeError, KeyError, TypeError) as error:
        return {"status": "failed", "error": f"Worker protocol: {error}; stdout={result.stdout[-1000:]}"}


def probe(node, inventory, config):
    program = "import json,platform,rdflib,owlrl,sys; from pathlib import Path; assert sys.platform.startswith('linux') and Path('/proc/self/status').is_file(), 'Linux procfs required for physical comparison'; print(json.dumps({'python':platform.python_version(),'rdflib':rdflib.__version__}))"
    try:
        result = subprocess.run(command(node, inventory, config, program, 10), text=True, capture_output=True,
                                timeout=config["connect_timeout_seconds"] + 15)
        return {"node": node.role, "host": node.host, "tier": node.tier, "available": result.returncode == 0,
                "detail": result.stdout.strip() if result.returncode == 0 else result.stderr[-2000:]}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"node": node.role, "host": node.host, "tier": node.tier, "available": False, "detail": str(error)}
