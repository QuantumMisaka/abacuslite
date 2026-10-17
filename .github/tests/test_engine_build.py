"""Guard the two-engine cold-build contract without compiling ABACUS in pytest."""

import json
import os
from pathlib import Path
import re
import subprocess

import pytest


ROOT = Path(__file__).parents[2]
BUILD = ROOT / "scripts/ci/build_abacus.sh"
REFS = ROOT / "tests/engine-refs.json"


@pytest.fixture
def checkout(tmp_path):
    source = tmp_path / "engine"
    source.mkdir()
    (source / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.16)\n")
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    subprocess.run(["git", "-C", str(source), "add", "CMakeLists.txt"], check=True)
    env = os.environ | {"GIT_AUTHOR_NAME": "CI Test", "GIT_AUTHOR_EMAIL": "ci@example.invalid",
                        "GIT_COMMITTER_NAME": "CI Test", "GIT_COMMITTER_EMAIL": "ci@example.invalid"}
    subprocess.run(["git", "-C", str(source), "commit", "-qm", "test source"],
                   check=True, env=env)
    sha = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"],
                                  text=True).strip()
    return source, sha


def command(tmp_path, source, sha, variant="develop"):
    return [str(BUILD), "--variant", variant, "--source-dir", str(source),
            "--build-dir", str(tmp_path / "build"),
            "--report-dir", str(tmp_path / "report"), "--expected-sha", sha]


def test_manifest_pins_distinct_full_engine_shas_and_curated_assets():
    refs = json.loads(REFS.read_text())
    assert refs["schema"] == "abacus-engine-compatibility-refs-v1"
    assert refs["engine_repository"] == refs["assets"]["repository"]
    assert set(refs["engines"]) == {"develop", "lts"}
    assert {row["expected_format"] for row in refs["engines"].values()} == {
        "latest", "legacy"}
    assert {row["binary"] for row in refs["engines"].values()} == {
        "abacus_basic_para", "abacus"}
    shas = [row["ref"] for row in refs["engines"].values()]
    assert len(set(shas)) == 2
    assert all(re.fullmatch(r"[0-9a-f]{40}", sha) for sha in shas)
    assert refs["assets"]["ref"] == refs["engines"]["develop"]["ref"]
    assert refs["harness"]["repository"] == "QuantumMisaka/abacus-develop"
    assert re.fullmatch(r"[0-9a-f]{40}", refs["harness"]["ref"])
    required = refs["assets"]["required_sha256"]
    assert set(required) == {"Si_ONCV_PBE-1.0.upf", "Si_gga_8au_100Ry_2s2p1d.orb",
                             "Fe_ONCV_PBE-1.0.upf", "Fe.upf",
                             "Fe_gga_6au_100Ry_4s2p2d1f.orb"}
    assert all(re.fullmatch(r"[0-9a-f]{64}", value) for value in required.values())


def test_wrong_commit_is_rejected_before_configure(tmp_path, checkout):
    source, sha = checkout
    result = subprocess.run(command(tmp_path, source, "0" * 40), text=True,
                            capture_output=True)
    assert result.returncode != 0
    assert "source SHA mismatch" in result.stderr
    assert not (tmp_path / "build").exists()
    assert sha != "0" * 40


def test_dirty_source_is_rejected_before_configure(tmp_path, checkout):
    source, sha = checkout
    (source / "CMakeLists.txt").write_text("changed\n")
    result = subprocess.run(command(tmp_path, source, sha), text=True,
                            capture_output=True)
    assert result.returncode != 0
    assert "checkout is dirty" in result.stderr
    assert not (tmp_path / "build").exists()


def test_existing_build_output_is_not_reused(tmp_path, checkout):
    source, sha = checkout
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "old-object.o").write_bytes(b"old")
    result = subprocess.run(command(tmp_path, source, sha), text=True,
                            capture_output=True)
    assert result.returncode != 0
    assert "must be empty for a cold build" in result.stderr
    assert (tmp_path / "build" / "old-object.o").read_bytes() == b"old"


@pytest.mark.parametrize("variant,openmp,elpa,forbidden", [
    ("develop", "-DENABLE_OPENMP=ON", "-DENABLE_ELPA=OFF", "-DUSE_OPENMP=ON"),
    ("lts", "-DUSE_OPENMP=ON", "-DUSE_ELPA=OFF", "-DENABLE_OPENMP=ON"),
])
def test_branch_switches_and_unused_cmake_options_fail(
        tmp_path, checkout, variant, openmp, elpa, forbidden):
    source, sha = checkout
    fakebin = tmp_path / "fakebin"
    fakebin.mkdir()
    args_log = tmp_path / "cmake-args.txt"
    fake_cmake = fakebin / "cmake"
    fake_cmake.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$@\" > \"$ARGS_LOG\"\n"
        "echo 'CMake Warning: Manually-specified variables were not used by the project:'\n"
        "echo '  TYPO_OPTION'\n")
    fake_cmake.chmod(0o755)
    env = os.environ | {"PATH": f"{fakebin}:{os.environ['PATH']}",
                        "ARGS_LOG": str(args_log)}
    result = subprocess.run(command(tmp_path, source, sha, variant), text=True,
                            capture_output=True, env=env)
    assert result.returncode != 0
    assert "ignored an explicit build option" in result.stderr
    args = args_log.read_text().splitlines()
    assert openmp in args and elpa in args and forbidden not in args
    assert "-DENABLE_MPI=ON" in args and "-DENABLE_LCAO=ON" in args
    assert not (tmp_path / "report/build-provenance.json").exists()
