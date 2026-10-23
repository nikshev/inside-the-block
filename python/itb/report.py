# impl: FR-003-06
"""Таблиці звіту: validator × hypothesis. Джерело кожної таблиці — data/."""

from __future__ import annotations


def _fmt(x, ndigits: int = 3) -> str:
    if x is None:
        return "—"
    return f"{x:.{ndigits}f}"


def render_markdown(results: list, source: str = "data/") -> str:
    """Markdown-таблиця для вставки у звіт."""
    lines = [f"<!-- згенеровано report.py з `{source}` -->", "",
             "| Валідатор | Рукав | Пар | Agr fee | Agr reward | Agr send | τ | 95% CI | p | Вердикт |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        a = r.get("agreement", {})
        lines.append(
            f"| {r['validator']} | {r['arm']} | {r['n_pairs']} "
            f"| {_fmt(a.get('fee'))} | {_fmt(a.get('reward'))} | {_fmt(a.get('send'))} "
            f"| {_fmt(r.get('tau'))} | [{_fmt(r.get('ci_low'))}, {_fmt(r.get('ci_high'))}] "
            f"| {_fmt(r.get('p_value'), 4)} | {r['verdict']} |")
    return "\n".join(lines) + "\n"


def render_csv(results: list) -> str:
    """Та сама таблиця у CSV."""
    lines = ["validator,arm,n_pairs,agr_fee,agr_reward,agr_send,tau,ci_low,ci_high,p_value,verdict"]
    for r in results:
        a = r.get("agreement", {})
        lines.append(
            f"{r['validator']},{r['arm']},{r['n_pairs']},"
            f"{a.get('fee')},{a.get('reward')},{a.get('send')},"
            f"{r.get('tau')},{r.get('ci_low')},{r.get('ci_high')},"
            f"{r.get('p_value')},{r['verdict']}")
    return "\n".join(lines) + "\n"
