"""Exercise final-result collection and handling of an empty parser result."""

import shutil
from pathlib import Path

import numpy as np
import pytest

from abacuslite.core import AbacusTemplate
from abacuslite.io import legacyio


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _template(calculation, atomorder=None, legacy=True):
    template = AbacusTemplate()
    template.suffix = "ABACUS"
    template.calculation = calculation
    template.atomorder = atomorder
    template._legacyio = legacy
    return template


@pytest.mark.parametrize("calculation", ["scf", "relax"])
def test_calculator_reports_empty_parsed_results(tmp_path, monkeypatch, calculation):
    monkeypatch.setattr(legacyio, "read_abacus_out", lambda *args, **kwargs: [])
    log = tmp_path / "OUT.ABACUS" / f"running_{calculation}.log"
    with pytest.raises(RuntimeError) as error:
        _template(calculation).read_results(tmp_path)
    assert str(log) in str(error.value)


def test_native_relax_multiframe_returns_last_result(tmp_path):
    source = FIXTURES / "multiframe_scf_trial_last" / "running_scf.log"
    output = tmp_path / "OUT.ABACUS"
    output.mkdir()
    shutil.copyfile(source, output / "running_relax.log")
    results = _template("relax").read_results(tmp_path)
    np.testing.assert_allclose(
        results["forces"], [[-0.45, -0.014, 0], [0.45, 0.014, 0], [0, 0, 0]],
        atol=1e-12,
    )


@pytest.mark.parametrize("backend,energy,energy_without_entropy,forces", [
    ("legacy", -1940.5509086572, -1940.3851061129,
     [[1.0712942948, 2.1781413019, 1.2152201133],
      [-1.0712942948, -2.1781413019, -1.2152201133]]),
    ("latest", -1940.6311063727, -1940.4234898941,
     [[0.1191299488, 0.2678988387, 1.5033416041],
      [-0.1191299488, -0.2678988387, -1.5033416041]]),
])
def test_native_md_collects_final_result(tmp_path, backend, energy, energy_without_entropy, forces):
    shutil.copytree(FIXTURES / f"multiframe_md_{backend}", tmp_path / "OUT.ABACUS")
    template = _template("md", atomorder=[0, 1], legacy=backend == "legacy")
    results = template.read_results(tmp_path)
    np.testing.assert_allclose(results["forces"], forces, atol=1e-12)
    assert results["energy"] == pytest.approx(energy)
    assert results["free_energy"] == pytest.approx(energy)
    assert results["energy_without_entropy"] == pytest.approx(energy_without_entropy, abs=1e-9)
