# Rekordbox SoundCloud Matcher

A tool for Rekordbox that converts SoundCloud streaming tracks into local audio files (MP3, WAV, AIFF, etc.) by matching the tracks in your `RB.xml` file with downloaded files, renaming them exactly as expected in the XML if necessary, and updating the file paths.

Cue points, beat grids, and playlists are entirely preserved!

## Features

- **Graphical User Interface (GUI):** Can be started directly as an app by double-clicking, without using the terminal.
- **Automated Fuzzy Matching:** Intelligently compares local files with your SoundCloud tracks from Rekordbox.
- **Auto-Renaming:** Renames the local files to match what Rekordbox expects.
- **XML Updating:** Replaces the size, path, and kind attributes in the exported XML file.
- **CLI Mode:** Can also be automated in scripts using command-line arguments.

## Prerequisites

- **Python 3.6+** (No external dependencies, strictly uses the standard library)
- **Mac Users (Homebrew):** If you installed Python via Homebrew, the `tkinter` library is often not included by default. You may need to install it via Homebrew, e.g., for Python 3.14 with:
  ```bash
  brew install python-tk@3.14
  ```

## Usage

### 1. Export Rekordbox XML
In Rekordbox, go to `File -> Export Collection in xml format` and save the `RB.xml`.

### 2. Start the Program

**Option A: Graphical User Interface (Easy / Double-Click)**
Double-click on `rekordbox_soundcloud_matcher.py` (Windows/Mac) or run it without arguments in the terminal:
```bash
python3 rekordbox_soundcloud_matcher.py
```
A GUI window will open. Select the downloaded XML, the folder containing the downloaded tracks, enter the playlist name, and click on "Start Matching & Renaming".

**Option B: Terminal / Command Line (Advanced)**
```bash
python3 rekordbox_soundcloud_matcher.py -p "PlaylistName" -i "PATH_TO_RB.xml" -d "PATH_TO_LOCAL_MUSIC"
```

### 3. Import XML back into Rekordbox
1. Go to Rekordbox Preferences -> "Advanced" -> "Database".
2. Under "rekordbox xml", select the newly generated modified `.xml` file.
3. Expand "rekordbox xml" in the sidebar, navigate to your playlist, and import it back (Right Click -> Import Playlist).

## License
MIT License