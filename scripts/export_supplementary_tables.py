from __future__ import annotations

from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "data" / "source_tables"
OUT = REPO_ROOT / "outputs" / "tables"


def markdown_escape(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def to_markdown_table(df: pd.DataFrame) -> str:
    columns = [str(c) for c in df.columns]
    lines = [
        "| " + " | ".join(markdown_escape(c) for c in columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in df.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(markdown_escape(v) for v in row) + " |")
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for csv_path in sorted(SOURCE.glob("supplementary_table_*.csv")):
        df = pd.read_csv(csv_path)
        out = OUT / f"{csv_path.stem}.md"
        out.write_text(to_markdown_table(df), encoding="utf-8")
        print(out)


if __name__ == "__main__":
    main()
