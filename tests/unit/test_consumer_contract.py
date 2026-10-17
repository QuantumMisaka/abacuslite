"""Behavior required by independent calculator and I/O consumers."""

from pathlib import Path
import shutil

import numpy as np
import pytest

from abacuslite import core
from abacuslite.io.generalio import read_kpt


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_point_kpt_preserves_fractional_coordinates_and_weights(tmp_path):
    path = tmp_path / "KPT"
    path.write_text("K_POINTS\n2\nDirect\n0.25 -0.125 0.5 2\n0.0 0.5 -0.25 3\n")
    data = read_kpt(path)
    np.testing.assert_allclose(data["kpoints"], [[0.25, -0.125, 0.5], [0.0, 0.5, -0.25]])
    assert data["weights"] == [2, 3]


def test_scf_selects_current_structure_and_retains_fermi(tmp_path, monkeypatch):
    gold = FIXTURES / "multiframe_scf_trial_last"
    shutil.copy(gold / "STRU", tmp_path / "STRU")
    output = tmp_path / "OUT.ABACUS"
    output.mkdir()
    shutil.copy(gold / "running_scf.log", output / "running_scf.log")
    monkeypatch.setattr(core, "__LEGACYIO__", True)
    template = core.AbacusTemplate()
    template.suffix = "ABACUS"
    template.calculation = "scf"
    template.atomorder = [0, 1, 2]
    result = template.read_results(tmp_path)
    np.testing.assert_allclose(result["forces"], [[-0.5, -0.01, 0], [0.5, 0.01, 0], [0, 0, 0]])
    assert result["efermi"] == pytest.approx(-2.04)


@pytest.mark.parametrize("order", [("legacy", "latest"), ("latest", "legacy")])
def test_calculator_readers_remain_independent(tmp_path, monkeypatch, order):
    class VersionProfile(core.AbacusProfile):
        def __init__(self, version):
            super().__init__("unused-abacus")
            self._test_version = version

        def version(self):
            return self._test_version

    monkeypatch.setattr(core, "__LEGACYIO__", core.__LEGACYIO__)
    versions = {"legacy": "v3.10.1", "latest": "v3.11.0"}
    energies = {"legacy": -210.6230563530, "latest": -1940.6311063727}
    calculators = {}
    for name in order:
        directory = tmp_path / name
        calculators[name] = core.Abacus(VersionProfile(versions[name]), directory=directory)
        source = FIXTURES / ("lts_native_md" if name == "legacy"
                             else "multiframe_md_latest")
        shutil.copytree(source, directory / "OUT.ABACUS")
        calculators[name].template.suffix = "ABACUS"
        calculators[name].template.calculation = "md"

    # The compatibility default may change; already-created calculators must not.
    for default in ("v3.11.0", "v3.10.1"):
        core.switch_io_backend_version(default)
        for name in reversed(order):
            result = calculators[name].template.read_results(tmp_path / name)
            assert result["energy"] == pytest.approx(energies[name])


def test_bare_39_version_resets_compatibility_switch(monkeypatch):
    monkeypatch.setattr(core, "__LEGACYIO__", core.__LEGACYIO__)
    core.switch_io_backend_version("v3.11.0")
    assert core.switch_io_backend_version("v3.9.0") is True


def test_fixed_density_uses_upstream_output_directory_default(monkeypatch, tmp_path):
    """Base fixed-density calculations retain upstream OUT.ABACUS discovery."""
    from abacuslite import Abacus

    calculator = object.__new__(Abacus)
    calculator.profile = object()
    calculator.directory = tmp_path
    captured = {}

    def fake_restart(cls, **kwargs):
        captured.update(kwargs)
        return kwargs

    monkeypatch.setattr(Abacus, "restart", classmethod(fake_restart))
    calculator.fixed_density({"mode": "gamma", "nk": 1})

    assert captured["inp"]["read_file_dir"] == "OUT.ABACUS"


def test_abacusprofile_version_keeps_native_probe(monkeypatch):
    """The base abacuslite profile should not contain ATST's fallback policy."""
    from abacuslite import AbacusProfile

    calls = []

    def fake_read_stdout(command):
        calls.append(command)
        return "ABACUS version v3.9.0.17\n"

    from abacuslite import core

    monkeypatch.setattr(core, "read_stdout", fake_read_stdout)

    profile = AbacusProfile("mpirun -np 4 abacus")

    assert profile.version() == "v3.9.0.17"
    assert calls == [["mpirun", "-np", "4", "abacus", "--version"]]


def test_file_safe_backup_preserves_noncanonical_numeric_suffixes(tmp_path):
    """Only canonical non-negative backup indexes should be rotated."""
    from abacuslite.io.generalio import file_safe_backup

    live = tmp_path / "STRU"
    backup0 = tmp_path / "STRU.bak.0"
    leading_zero_backup = tmp_path / "STRU.bak.01"
    signed_positive_backup = tmp_path / "STRU.bak.+1"
    signed_negative_backup = tmp_path / "STRU.bak.-1"

    live.write_text("live\n", encoding="utf-8")
    backup0.write_text("old-zero\n", encoding="utf-8")
    leading_zero_backup.write_text("leading-zero\n", encoding="utf-8")
    signed_positive_backup.write_text("signed-positive\n", encoding="utf-8")
    signed_negative_backup.write_text("signed-negative\n", encoding="utf-8")

    file_safe_backup(live)

    assert not live.exists()
    assert backup0.read_text(encoding="utf-8") == "live\n"
    assert (tmp_path / "STRU.bak.1").read_text(encoding="utf-8") == "old-zero\n"
    assert leading_zero_backup.read_text(encoding="utf-8") == "leading-zero\n"
    assert signed_positive_backup.read_text(encoding="utf-8") == "signed-positive\n"
    assert signed_negative_backup.read_text(encoding="utf-8") == "signed-negative\n"
