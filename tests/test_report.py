"""Тест таблиць звіту: Markdown і CSV з тими самими цифрами.

verifies: FR-003-06
"""

from itb.report import render_csv, render_markdown


def sample():
    return [
        {"validator": "agave-1", "arm": "A", "n_pairs": 120,
         "agreement": {"fee": 0.97, "reward": 0.96, "send": 0.51},
         "tau": 0.93, "ci_low": 0.89, "ci_high": 0.97, "p_value": 0.001,
         "verdict": "strict"},
        {"validator": "jito-1", "arm": "A", "n_pairs": 8,
         "agreement": {"fee": 0.6, "reward": 0.6, "send": 0.5},
         "tau": 0.1, "ci_low": 0.0, "ci_high": 0.5, "p_value": 0.5,
         "verdict": "insufficient-data"},
    ]


def test_markdown_contains_all_cells():
    md = render_markdown(sample(), source="data/")
    assert "agave-1" in md and "0.97" in md and "strict" in md
    assert "insufficient-data" in md and "data/" in md


def test_csv_same_numbers():
    csv_text = render_csv(sample())
    lines = csv_text.strip().splitlines()
    assert lines[0].startswith("validator,arm,n_pairs")
    assert "agave-1,A,120,0.97" in lines[1]
