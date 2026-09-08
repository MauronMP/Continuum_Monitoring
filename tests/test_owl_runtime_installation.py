from __future__ import annotations

import re
import subprocess
import sys
import tomllib


def test_reasoner_pom_isolates_java_dependency_trees(root):
    pom = (root / "tools/owl/pom.xml").read_text(encoding="utf-8")

    for profile in ("hermit", "openllet", "jfact"):
        assert f"<id>{profile}</id>" in pom
    common = pom.split("<profiles>", maxsplit=1)[0]
    assert "org.semanticweb.hermit" not in common
    assert "openllet-owlapi" not in common
    assert "<artifactId>jfact</artifactId>" not in common
    jfact_profile = pom.split("<id>jfact</id>", maxsplit=1)[1].split(
        "</profile>", maxsplit=1
    )[0]
    assert "<artifactId>guice</artifactId>" in jfact_profile
    assert "<version>5.1.0</version>" in jfact_profile


def test_konclude_wrapper_rejects_help_only_invocation(root):
    ontology = root / "ontology/legacy/smartcity_continuum-v3.0.0.ttl"
    completed = subprocess.run(
        [
            sys.executable,
            str(root / "tools/owl/run_konclude.py"),
            "-i",
            str(ontology),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 2
    assert "only prints Konclude help" in completed.stderr


def test_konclude_configuration_runs_a_bounded_consistency_operation(root):
    with (root / "configs/owl-reasoners.toml").open("rb") as handle:
        config = tomllib.load(handle)

    konclude = config["reasoners"]["konclude"]
    assert konclude["command"][2:6] == ["consistency", "-w", "AUTO", "-i"]
    assert konclude["timeout_seconds"] > 0


def test_konclude_configuration_recognizes_native_success_output(root):
    with (root / "configs/owl-reasoners.toml").open("rb") as handle:
        config = tomllib.load(handle)
    pattern = config["reasoners"]["konclude"]["consistent_pattern"]
    native_output = (
        "Ontology '/tmp/continuum-konclude/ontology.owl.xml' is consistent."
    )

    assert re.search(pattern, native_output)
