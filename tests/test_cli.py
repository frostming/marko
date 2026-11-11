"""Tests for the marko command line interface."""

import subprocess
import sys

from marko import cli


def test_unknown_extension_is_clean_error(tmp_path, capsys):
    doc = tmp_path / "doc.md"
    doc.write_text("# Hello\n")
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "marko",
            "--extension",
            "no_such_ext_xyz",
            str(doc),
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    assert "no_such_ext_xyz" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_valid_extension_still_works(tmp_path, monkeypatch, capsys):
    doc = tmp_path / "doc.md"
    doc.write_text("# Hello\n")
    monkeypatch.setattr(sys, "argv", ["marko", "--extension", "footnote", str(doc)])
    assert cli.main() is None
    out, _ = capsys.readouterr()
    assert "<h1>Hello</h1>" in out
