"""Тест гігієни секретів: gitignore покриває ключі, приклад без секретів, CI ловить.

verifies: FR-001-09, FR-001-10
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def git_ignored(path: str) -> bool:
    p = subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=ROOT,
    )
    return p.returncode == 0


def test_key_material_is_gitignored():
    assert git_ignored("keys/validator.json")
    assert git_ignored("wallet.key")
    assert git_ignored(".env")


def test_env_example_has_no_secrets():
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    low = text.lower()
    assert "private" not in low and "mnemonic" not in low
    # значення порожні: жодного присвоєного URL чи ключа
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            _, _, value = line.partition("=")
            assert value.strip() in ("", "dry-run"), f"підозріле значення: {line}"


def test_ci_checks_secrets_and_trace():
    ci = ROOT / ".github" / "workflows" / "ci.yml"
    assert ci.is_file(), "CI-воркфлоу відсутній"
    text = ci.read_text(encoding="utf-8")
    assert "trace.py" in text
    assert "secret" in text.lower()
