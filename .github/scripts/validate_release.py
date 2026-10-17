"""Validate the source run and distributions before requesting PyPI credentials."""

import argparse
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile
import zipfile


REPOSITORY = "QuantumMisaka/abacuslite"


def release_version(tag):
    if not re.fullmatch(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", tag):
        raise ValueError("A stable vMAJOR.MINOR.PATCH tag is required")
    return tag[1:]


def validate_run(run, tag, sha):
    release_version(tag)
    required = {
        "event": "push",
        "status": "completed",
        "conclusion": "success",
        "path": ".github/workflows/tests.yml",
        "head_branch": tag,
        "head_sha": sha,
    }
    for field, expected in required.items():
        if run.get(field) != expected:
            raise ValueError(f"Source run {field} must be {expected!r}")
    for field in ("repository", "head_repository"):
        if run.get(field, {}).get("full_name") != REPOSITORY:
            raise ValueError(f"Source run {field} must be {REPOSITORY}")


def validate_distributions(directory, tag):
    version = release_version(tag)
    wheel_name = f"abacuslite-{version}-py3-none-any.whl"
    sdist_name = f"abacuslite-{version}.tar.gz"
    files = list(directory.iterdir())
    if {p.name for p in files} != {wheel_name, sdist_name}:
        raise ValueError("Expected exactly one release wheel and one source distribution")
    if any(not p.is_file() or p.is_symlink() for p in files):
        raise ValueError("Distributions must be regular files")
    with zipfile.ZipFile(directory / wheel_name) as archive:
        metadata = archive.read(f"abacuslite-{version}.dist-info/METADATA")
    with tarfile.open(directory / sdist_name, "r:gz") as archive:
        member = archive.getmember(f"abacuslite-{version}/PKG-INFO")
        if not member.isfile():
            raise ValueError("Source metadata must be a regular file")
        source_metadata = archive.extractfile(member).read()
    for content in (metadata, source_metadata):
        parsed = BytesParser().parsebytes(content)
        if parsed.get_all("Name") != ["abacuslite"] or parsed.get_all("Version") != [version]:
            raise ValueError("Distribution metadata does not match the release tag")
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    source = commands.add_parser("source")
    source.add_argument("--run", type=Path, required=True)
    source.add_argument("--main-sha", required=True)
    dist = commands.add_parser("distributions")
    dist.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    release_version(args.tag)
    if args.command == "source":
        sha = subprocess.check_output(
            ["git", "rev-parse", "--verify", f"refs/tags/{args.tag}^{{commit}}"], text=True
        ).strip()
        subprocess.run(["git", "merge-base", "--is-ancestor", sha, args.main_sha], check=True)
        validate_run(json.loads(args.run.read_text()), args.tag, sha)
        print(f"Verified {args.tag} at {sha}")
    else:
        print(json.dumps(validate_distributions(args.directory, args.tag), indent=2))


if __name__ == "__main__":
    main()
