"""Release gate regressions; these run in CI, not in the installed plugin suite."""

import importlib.util
import io
from pathlib import Path
import tarfile
import zipfile

import pytest


spec = importlib.util.spec_from_file_location(
    "validate_release", Path(__file__).parents[1] / "scripts" / "validate_release.py"
)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


@pytest.fixture
def run():
    return {
        "event": "push", "status": "completed", "conclusion": "success",
        "path": ".github/workflows/tests.yml", "head_branch": "v1.1.0",
        "head_sha": "a" * 40,
        "repository": {"full_name": "QuantumMisaka/abacuslite"},
        "head_repository": {"full_name": "QuantumMisaka/abacuslite"},
    }


def test_successful_tag_run_is_accepted(run):
    release.validate_run(run, "v1.1.0", "a" * 40)


@pytest.mark.parametrize("field,value", [
    ("event", "pull_request"), ("event", "workflow_dispatch"),
    ("status", "in_progress"), ("conclusion", "failure"),
    ("conclusion", "cancelled"), ("path", ".github/workflows/other.yml"),
    ("head_branch", "main"), ("head_sha", "b" * 40),
    ("repository", {"full_name": "someone/abacuslite"}),
    ("head_repository", {"full_name": "someone/abacuslite"}),
])
def test_unverified_or_wrong_source_run_is_rejected(run, field, value):
    run[field] = value
    with pytest.raises(ValueError):
        release.validate_run(run, "v1.1.0", "a" * 40)


@pytest.mark.parametrize("tag", ["v1.1.0rc1", "v1.1.0+local", "1.1.0", "v01.1.0", "v1.1.0\n"])
def test_only_stable_release_tags_are_accepted(tag):
    with pytest.raises(ValueError):
        release.release_version(tag)


def write_distributions(path, wheel_version="1.1.0", source_version="1.1.0"):
    with zipfile.ZipFile(path / "abacuslite-1.1.0-py3-none-any.whl", "w") as archive:
        archive.writestr("abacuslite-1.1.0.dist-info/METADATA",
                         f"Name: abacuslite\nVersion: {wheel_version}\n")
    with tarfile.open(path / "abacuslite-1.1.0.tar.gz", "w:gz") as archive:
        data = f"Name: abacuslite\nVersion: {source_version}\n".encode()
        member = tarfile.TarInfo("abacuslite-1.1.0/PKG-INFO")
        member.size = len(data)
        archive.addfile(member, io.BytesIO(data))


def test_matching_pair_returns_artifact_hashes(tmp_path):
    write_distributions(tmp_path)
    hashes = release.validate_distributions(tmp_path, "v1.1.0")
    assert set(hashes) == {"abacuslite-1.1.0-py3-none-any.whl", "abacuslite-1.1.0.tar.gz"}
    assert all(len(value) == 64 for value in hashes.values())


@pytest.mark.parametrize("wheel,source", [("1.1.0rc1", "1.1.0"), ("1.1.0", "1.0.0")])
def test_renamed_wrong_version_artifact_is_rejected(tmp_path, wheel, source):
    write_distributions(tmp_path, wheel, source)
    with pytest.raises(ValueError, match="metadata"):
        release.validate_distributions(tmp_path, "v1.1.0")


@pytest.mark.parametrize("incomplete", [True, False])
def test_missing_or_extra_artifacts_are_rejected(tmp_path, incomplete):
    write_distributions(tmp_path)
    if incomplete:
        (tmp_path / "abacuslite-1.1.0.tar.gz").rename(tmp_path.parent / "withheld.tar.gz")
    else:
        (tmp_path / "extra.whl").write_bytes(b"unexpected")
    with pytest.raises(ValueError, match="exactly"):
        release.validate_distributions(tmp_path, "v1.1.0")
