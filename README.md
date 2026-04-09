# Rekordbox SoundCloud to Local Matcher

A Python tool that helps DJs transition from SoundCloud streaming in Rekordbox to local, downloaded audio files (WAV, MP3, AIFF, M4A). 

It intelligently fuzz-matches your local audio files to the tracks in a Rekordbox XML playlist. When a match is found, it automatically renames your local audio file to EXACTLY match the Rekordbox track name, and updates the XML database to redirect the streaming track to the new local file.

**Crucial advantage:** Transitioning this way preserves all your track analysis, beat grids, cue points (`<POSITION_MARK>`), and placement within your playlists. 

## Features

- **Automated renaming:** Renames local files based on Rekordbox track names safely.
- **Smart matching:** Ignores suffixes like "(Free DL)", "(Edit)" or "Remix" to find the right audio file.
- **Preserves Cues & Grids:** Modifies only the `<TRACK>` location and size, leaving hot cues and BPM metadata intact.
- **Cross-format support:** Works out-of-the-box with `.mp3`, `.wav`, `.aif`, `.aiff`, and `.m4a` files.

## Prerequisites

- **Python 3.6+** (No external dependencies required, strictly uses the Python standard library).
- **Rekordbox Database Export:** Export your Rekordbox collection as an XML file (`File -> Export Collection in xml format`).

## Usage

1. Export your Rekordbox Collection as an `.xml` file (e.g., `RB.xml`).
2. Move all your downloaded audio files into a dedicated folder (e.g., `/Users/name/Music/MyPlaylist`).
3. Run the script via your terminal:

```bash
python3 rekordbox_soundcloud_matcher.py \
    --playlist "Playlist Name" \
    --input "path/to/RB.xml" \
    --output "path/to/RB_modified.xml" \
    --dir "path/to/local/audio/folder"
```

Oder in Kurzform:
```bash
python3 rekordbox_soundcloud_matcher.py -p "My Playlist" -i "RB.xml" -o "RB_modified.xml" -d "/Users/name/Music/MyPlaylist"
```

4. Open Rekordbox, go to Preferences -> Advanced -> Database, and import the generated `RB_modified.xml` file.

## Options

- `-p`, `--playlist` : Name of the playlist in rekordbox (must match exactly)
- `-i`, `--input`    : Path to your original Rekordbox XML file
- `-o`, `--output`   : Destination path for the modified Rekordbox XML file
- `-d`, `--dir`      : Path to the local folder containing the downloaded audio files

## Flow & Safety

- The script reads the XML file and extracts all SoundCloud tracks of the given `-p` playlist.
- It collects all local audio files in the given `-d` folder.
- It attempts to fuzzy match the streaming track name with the local file name.
- If a confident match is found, the file is renamed in your operating system directly.
- A new XML file (`-o`) is generated with updated file paths. Your original XML file (`-i`) is **never** overwritten or modified directly.
- Simply import the newly generated XML if you are happy with the matching results.
