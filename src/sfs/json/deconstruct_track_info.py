import os
from itertools import batched
from pathlib import Path

with Path("src/sfs/json/track_info.json").open("r") as f:
    track_info = f.read()

batched_track_info = batched(track_info, 45_000_000)

for i, batch in enumerate(batched_track_info):
    with Path(f"src/sfs/json/track_info/track_info{i}.json").open("w") as f:
        f.write("".join(batch))


os.remove("src/sfs/json/track_info.json")
