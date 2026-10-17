"""Reference selection preserves pinned PR baselines and resolves schedules once."""

import hashlib
import importlib.util
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location(
    "engine_refs", Path(__file__).parents[2] / "scripts" / "ci" / "engine_refs.py"
)
refs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refs)


@pytest.fixture
def manifest():
    return {
        "schema": "abacus-engine-compatibility-refs-v1",
        "engine_repository": "engine/project",
        "engines": {
            "develop": {"ref": "a" * 40, "expected_format": "latest"},
            "lts": {"ref": "b" * 40, "expected_format": "legacy"},
        },
        "harness": {"repository": "owner/project", "ref": "c" * 40},
        "assets": {"repository": "engine/project", "ref": "d" * 40,
                   "directory": "tests/assets", "required_sha256": {}},
    }


def test_pr_does_not_follow_moving_engine_heads(manifest):
    calls = []
    def resolve(repository, ref):
        calls.append((repository, ref))
        return ref
    result = refs.resolve_matrix(manifest, "pull_request", {}, resolve)
    assert result["matrix"]["include"] == [
        {"variant": "develop", "ref": "a" * 40, "format": "latest"},
        {"variant": "lts", "ref": "b" * 40, "format": "legacy"},
    ]
    assert calls == [("engine/project", "a" * 40), ("engine/project", "b" * 40),
                     ("owner/project", "c" * 40), ("engine/project", "d" * 40)]


def test_schedule_resolves_branch_heads_but_retains_reviewed_harness(manifest):
    def resolve(repository, ref):
        return {"develop": "e" * 40, "LTS": "f" * 40}.get(ref, ref)
    result = refs.resolve_matrix(manifest, "schedule", {}, resolve)
    assert [lane["ref"] for lane in result["matrix"]["include"]] == ["e" * 40, "f" * 40]
    assert result["harness_ref"] == "c" * 40
    assert result["assets_ref"] == "d" * 40


def test_manual_candidate_refs_are_resolved_without_shell_interpolation(manifest):
    calls = []
    def resolve(repository, ref):
        calls.append(ref)
        return "e" * 40
    refs.resolve_matrix(manifest, "workflow_dispatch",
                        {"develop": "refs/pull/3/merge", "lts": "candidate", "harness": "reviewed"}, resolve)
    assert calls == ["refs/pull/3/merge", "candidate", "reviewed", "d" * 40]


def test_missing_or_changed_required_assets_fail(manifest, tmp_path):
    manifest["assets"]["required_sha256"] = {"Si.upf": hashlib.sha256(b"reference").hexdigest()}
    with pytest.raises(FileNotFoundError):
        refs.verify_assets(manifest, tmp_path)
    (tmp_path / "Si.upf").write_bytes(b"reference")
    refs.verify_assets(manifest, tmp_path)
    (tmp_path / "Si.upf").write_bytes(b"wrong potential")
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        refs.verify_assets(manifest, tmp_path)


def test_assets_cannot_escape_manifest_directory(manifest, tmp_path):
    manifest["assets"]["required_sha256"] = {"../outside": "0" * 64}
    with pytest.raises(ValueError, match="escapes"):
        refs.verify_assets(manifest, tmp_path)
