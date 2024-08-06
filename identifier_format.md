```python
identifier = "||".join(
            [
                f"{track['duration_ms']}",
                track["external_ids"]["isrc"],
                track["name"],
                track["album"]["name"],
                track["album"]["images"][0]["url"],
            ]
        )
```