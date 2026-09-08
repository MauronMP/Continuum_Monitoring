"""Reproduction evidence for the exact source, dependencies and experiment inputs."""
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import subprocess
import tarfile


def snapshot(root: Path, output: Path) -> dict:
    files = []
    for folder in ('src', 'configs', 'ontology', 'queries', 'requirements', 'tools', 'docs', 'tests'):
        files.extend(p for p in (root/folder).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts and not p.name.endswith('.pyc')
                     and not any(part.endswith('.egg-info') for part in p.parts)
                     and not p.name.endswith('.local.toml') and 'local' not in p.relative_to(root).parts)
    files.extend(p for p in (root/'pyproject.toml', root/'requirements-node.txt', root/'README.md') if p.is_file())
    hashes = {str(p.relative_to(root)): sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    with tarfile.open(output/'source.tar.gz', 'w:gz') as archive:
        for p in sorted(files): archive.add(p, arcname=str(p.relative_to(root)), recursive=False)
    try:
        commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True,stderr=subprocess.DEVNULL).strip()
    except (OSError,subprocess.CalledProcessError): commit = None
    dependencies = {}
    for name in ('rdflib','owlrl','pyshacl','pyoxigraph','numpy','matplotlib'):
        try: dependencies[name] = version(name)
        except PackageNotFoundError: dependencies[name] = None
    return {'git_commit':commit, 'source_sha256':hashes, 'dependency_versions':dependencies,
            'source_archive':'source.tar.gz'}
