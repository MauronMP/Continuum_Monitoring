#!/usr/bin/env python3
"""Enable Raspberry Pi memory cgroups in the boot command line; never reboot implicitly."""

from datetime import datetime, timezone
import os
from pathlib import Path
import shutil


def enable(path: Path) -> bool:
    original = path.read_text()
    words = original.split()
    if not words or words[0].startswith("#"):
        raise ValueError(
            "Expected the actual one-line kernel command line, not a redirect file"
        )
    updated = []
    for word in words:
        if word.startswith("cgroup_disable="):
            disabled = [
                value for value in word.split("=", 1)[1].split(",") if value != "memory"
            ]
            if disabled:
                updated.append("cgroup_disable=" + ",".join(disabled))
        elif word not in ("cgroup_memory=0", "cgroup_memory=1", "cgroup_enable=memory"):
            updated.append(word)
    updated.extend(["cgroup_memory=1", "cgroup_enable=memory"])
    text = " ".join(updated) + "\n"
    if text == original:
        return False
    backup = path.with_name(
        path.name
        + ".continuum-backup-"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    )
    shutil.copy2(path, backup)
    path.write_text(text)
    print(f"Backup: {backup}")
    return True


def main():
    if os.geteuid() != 0:
        raise SystemExit("Run with sudo on the Raspberry Pi host")
    path = next(
        (
            p
            for p in (Path("/boot/firmware/cmdline.txt"), Path("/boot/cmdline.txt"))
            if p.is_file()
        ),
        None,
    )
    if path is None:
        raise SystemExit(
            "No supported Raspberry Pi boot command line found; configure cgroups for this OS manually"
        )
    changed = enable(path)
    print(
        f"Boot configuration changed: {changed}. Reboot this host, then verify docker info and container-scale doctor."
    )


if __name__ == "__main__":
    main()
