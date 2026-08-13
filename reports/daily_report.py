def render_report(report_date, pools: dict) -> str:
    lines = [f"# A股连板接力日报 — {report_date}", ""]
    for name, rows in pools.items():
        lines += [f"## {name}", ""]
        for row in rows:
            lines.append(f"- {row}")
        lines.append("")
    return "\n".join(lines)
