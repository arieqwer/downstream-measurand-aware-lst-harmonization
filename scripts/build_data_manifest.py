import argparse
import hashlib
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed"
MANIFEST = ROOT / "data/metadata/processed_file_manifest_sha256.csv"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def current() -> pd.DataFrame:
    rows = []
    for path in sorted(DATA.rglob("*.csv")):
        rows.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": digest(path),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    observed = current()
    if args.verify:
        expected = pd.read_csv(MANIFEST)
        if not observed.equals(expected):
            raise SystemExit("Processed-data manifest does not match archived files.")
        print("Processed-data manifest verified.")
        return
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    observed.to_csv(MANIFEST, index=False)
    print(f"Manifest written to {MANIFEST}")


if __name__ == "__main__":
    main()
