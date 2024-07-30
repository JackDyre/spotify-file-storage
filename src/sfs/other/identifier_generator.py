"""Test."""

import json
from pathlib import Path


def main() -> None:
    """Run the main logic."""
    with Path("src/sfs/json/track_info.json").open("r") as f:
        tinfo = json.load(f)

    itb = {}
    bti = {}

    identifiers = []

    for i, t in enumerate(tinfo):
        identifier = "||".join(
            [
                f"{t['duration_ms']}",
                t["external_ids"]["isrc"],
                t["name"],
                t["album"]["name"],
                t["album"]["images"][0]["url"],
            ]
        )
        # if identifier in identifiers:
        #     print(i, t["name"], t["artists"][0]["name"])
        # else:
        #     identifiers.append(identifier)
        tid = t["id"]
        binary = bin(i)[2:].zfill(16) if i < 2**16 else f"{i - 2 ** 16}"

        itb[identifier] = binary
        bti[binary] = tid

    print(len(itb) - len(tinfo))

    with Path("src/sfs/json/fixed_bti.json").open("w") as f:
        json.dump(bti, f, indent=4)
    with Path("src/sfs/json/fixed_itb.json").open("w") as f:
        json.dump(itb, f, indent=4)


if __name__ == "__main__":
    main()
