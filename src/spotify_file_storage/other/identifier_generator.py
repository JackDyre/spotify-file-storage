"""Test."""

import json
from pathlib import Path


def main() -> None:
    """Run the man logic."""
    with Path("trackinfo.json").open("r") as f:
        tinfo = json.load(f)

    itb = {}

    for i, t in enumerate(tinfo):
        if i < 2**16:
            itb[f"{t['duration_ms']}||{t['external_ids']['isrc']}||{t['name']}"] = bin(
                i
            )[2:].zfill(16)
        else:
            itb[f"{t['duration_ms']}||{t['external_ids']['isrc']}||{t['name']}"] = (
                f"{i - 2**16}"
            )

    with Path("identifiertobinary.json").open("w") as f:
        json.dump(itb, f, indent=4)


if __name__ == "__main__":
    main()
