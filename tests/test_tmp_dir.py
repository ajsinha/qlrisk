from datetime import date
from pathlib import Path

from qlrisk import config
from qlrisk.reporting.report import RiskReport


def test_default_is_tmp(monkeypatch):
    monkeypatch.delenv(config.TMP_DIR_ENV, raising=False)
    config.set_tmp_dir(None)
    assert config.get_tmp_dir() == Path("/tmp")


def test_env_and_override(monkeypatch, tmp_path):
    monkeypatch.setenv(config.TMP_DIR_ENV, str(tmp_path / "env"))
    assert config.get_tmp_dir() == tmp_path / "env" and (tmp_path / "env").is_dir()
    config.set_tmp_dir(tmp_path / "own")
    try:
        assert config.tmp_path("x.csv") == tmp_path / "own" / "x.csv"
        d = config.make_tmp_dir()
        assert d.parent == tmp_path / "own" and d.name.startswith("qlrisk-")
        report = RiskReport(date(2026, 10, 9), "USD")
        report.metrics["pv.total"] = 1.0
        out = Path(report.to_csv())
        assert out.parent == tmp_path / "own" and out.read_text().startswith("node,metric,value")
    finally:
        config.set_tmp_dir(None)
