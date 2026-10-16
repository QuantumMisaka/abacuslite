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


def test_calculator_reader_is_not_changed_by_a_second_calculator(tmp_path):
    class VersionProfile(core.AbacusProfile):
        def __init__(self, version):
            super().__init__("unused-abacus")
            self._test_version = version

        def version(self):
            return self._test_version

    legacy = core.Abacus(VersionProfile("v3.10.1"), directory=tmp_path / "legacy")
    core.Abacus(VersionProfile("v3.11.0"), directory=tmp_path / "latest")
    gold = FIXTURES / "multiframe_md_legacy"
    output = tmp_path / "legacy/OUT.ABACUS"
    output.mkdir(parents=True)
    shutil.copy(gold / "running_md.log", output / "running_md.log")
    legacy.template.suffix = "ABACUS"
    legacy.template.calculation = "md"
    result = legacy.template.read_results(tmp_path / "legacy")
    assert result["energy"] == pytest.approx(-1940.5509086572)


def test_bare_39_version_resets_compatibility_switch():
    core.switch_io_backend_version("v3.11.0")
    assert core.switch_io_backend_version("v3.9.0") is True
