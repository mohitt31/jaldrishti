"""Public rename keeps both installed commands backed by the unchanged engine."""
from pathlib import Path
import subprocess
import sys


def test_cli_help_uses_public_brand():
    result = subprocess.run([sys.executable, '-m', 'jaldrishti.cli', '--help'], capture_output=True, text=True, check=True)
    assert 'usage: neertathya' in result.stdout


def test_legacy_command_is_retained_as_same_entrypoint():
    project = (Path(__file__).resolve().parents[1] / 'pyproject.toml').read_text()
    assert 'neertathya = "jaldrishti.cli:main"' in project
    assert 'jaldrishti = "jaldrishti.cli:main"' in project
