3 actions:
- Push
- Pull
- Remove

2 object types:
- File Envs
- Files

Every object has a passkey
After the end of the content of a playlist, a stop sequence will be present and all following items will be random.

CLI Args:
- sfs push -p <path/to/file> -k <passkey>
- sfs pull -d <destination/path> -i <id> -k <passkey>
- sfs rm -i <id> -k <passkey>
- sfs fe open <id> -i <id>
- sfs fe create <id>

Playlist format:
- Hashed passkey in name
- Hashed SFS playlist identifier in description, then begin contents.
- Stop elements scattered throughout entire playlist, but ignore upon parsing unless all of them are in a row.
- After content stream ends, all stop elements are present in a row, and all following data is random
- Content track count limited to 9950 to leave room for stop elements

Playlist Types:
- File Env - Nested dicts of file system
- File Header - Dict of file name and file content playlist ids
- File Content - Binary of file
