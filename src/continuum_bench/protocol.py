from __future__ import annotations

import json
from time import monotonic, sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request_json(
    url: str,
    *,
    method: str = "GET",
    payload: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = 120,
) -> dict:
    request = Request(url, data=payload, method=method, headers=headers or {})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{url}: HTTP {error.code}: {body}") from error
    except (URLError, TimeoutError) as error:
        raise RuntimeError(f"{url}: {error}") from error


def wait_ready(
    endpoint: str, *, deadline_seconds: float, require_idle: bool = False, expected: dict[str, object] | None = None
) -> dict:
    deadline = monotonic() + deadline_seconds
    last_error = "no response"
    while monotonic() < deadline:
        try:
            health = request_json(f"{endpoint}/health", timeout=min(5, deadline_seconds))
            compatible = (
                health.get("service") == "continuum-worker"
                and health.get("protocol_version") == "continuum-rdf-worker-v1"
            )
            matches = all(health.get(key) == value for key, value in (expected or {}).items())
            idle = not require_idle or (
                health.get("idle") is True and health.get("active_requests") == 0 and health.get("queue_depth") == 0
            )
            if health.get("status") == "ready" and compatible and matches and idle:
                return health
            last_error = f"ready={compatible} assets={matches} idle={idle}"
        except RuntimeError as error:
            last_error = str(error)
        sleep(0.5)
    raise TimeoutError(f"{endpoint} did not become ready: {last_error}")
