#!/usr/bin/env python3
"""
Matches local files in /Users/jonas/Music/Schranz to RB.xml Tracks,
renames the local files to EXACTLY match the XML Name,
and creates a modified RB.xml with updated Locations.
"""
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import re
import html
import argparse
import unicodedata
import difflib
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape

SUPPORTED_EXTS = {".mp3", ".wav", ".aif", ".aiff", ".m4a"}
KIND_BY_EXT = {
    ".mp3": "Mp3-Datei ",
    ".wav": "Wav-Datei ",
    ".aif": "Aiff-Datei ",
    ".aiff": "Aiff-Datei ",
    ".m4a": "M4a-Datei ",
}

def clean_for_match(s):
    s = html.unescape(s)
    s = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8")
    s = s.lower()
    
    stopwords = ['free dl', 'free download', 'schranz edit', 'schranz remix', 'techno remix', 
                 'hard techno', 'edit', 'remix', 'bootleg', 'rework', 'original mix', 
                 'master', 'wav', 'mp3', 'click buy for free download', '( )', '[ ]', '()', '[]']
    for word in stopwords:
        s = s.replace(word, '')
        
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

def extract_playlist_ids(source_xml, playlist_name):
    ids = set()
    node_re = re.compile(rf'<NODE\s+Name="{re.escape(playlist_name)}"\s+Type="1"[^>]*>')
    key_re = re.compile(r'<TRACK\s+Key="(\d+)"\s*/?>')
    in_node = False
    
    with source_xml.open("r", encoding="utf-8", newline="") as f:
        for line in f:
            if not in_node:
                if node_re.search(line):
                    in_node = True
                continue
            if "</NODE>" in line:
                break
            m = key_re.search(line)
            if m:
                ids.add(m.group(1))
    return ids

def get_track_names(ids, source_xml):
    names = {}
    track_re = re.compile(r'<TRACK\s+TrackID="(\d+)".*?Name="([^"]+)"')
    with source_xml.open("r", encoding="utf-8", newline="") as f:
        for line in f:
            if "<TRACK" in line:
                m = track_re.search(line)
                if m:
                    tid, name = m.group(1), m.group(2)
                    if tid in ids:
                        names[tid] = html.unescape(name)
    return names

def sanitize_filename(name):
    """Make raw string safe for macOS filesystem without changing its display too much."""
    safe_name = name.replace("/", "_").replace(":", "_")
    # Clean up excessive spaces
    safe_name = re.sub(r'\s+', ' ', safe_name).strip()
    return safe_name

def match_and_rename_files(xml_names, local_dir):
    file_paths = []
    for ext in SUPPORTED_EXTS:
        file_paths.extend(local_dir.rglob(f"*{ext}"))
        file_paths.extend(local_dir.rglob(f"*{ext.upper()}"))
        
    file_clean = {p: clean_for_match(p.stem) for p in file_paths}
    xml_clean = {tid: clean_for_match(name) for tid, name in xml_names.items()}
    
    unassigned_files = list(file_paths)
    assignment = {}  # xml track_id -> new Path

    # Identify assignments
    for tid, xml_name in xml_names.items():
        xc = xml_clean[tid]
        if not xc:
            continue
            
        best_score = 0
        best_file = None
        
        for p in unassigned_files:
            fc = file_clean[p]
            score = difflib.SequenceMatcher(None, xc, fc).ratio()
            if xc in fc or fc in xc:
                score += 0.4
                
            if score > best_score:
                best_score = score
                best_file = p
        
        if best_score > 0.55 and best_file:
            unassigned_files.remove(best_file)
            
            # Found a match, renaming it on disk
            ext = best_file.suffix.lower()
            safe_xml_name = sanitize_filename(xml_name)
            new_name = f"{safe_xml_name}{ext}"
            new_path = local_dir / new_name
            
            # Skip rename if it's already exactly the same or name conflict exists
            if best_file.name != new_name:
                # Resolve conflicts if a file with this name already exists
                counter = 1
                while new_path.exists() and not best_file.samefile(new_path):
                    new_name = f"{safe_xml_name}_{counter}{ext}"
                    new_path = local_dir / new_name
                    counter += 1
                    
                if not new_path.exists() or not best_file.samefile(new_path): # Safely rename
                    print(f"Umbenannt: {best_file.name} -> {new_name}")
                    os.rename(best_file, new_path)
            
            assignment[tid] = new_path

    return assignment

def update_track_tag(start_tag, tid, assignment, local_dir):
    if tid not in assignment:
        return start_tag, False

    local_path = assignment[tid]
    
    def repl_attr(text, attr, val):
        return re.sub(rf'{re.escape(attr)}="[^"]*"', f'{attr}="{val}"', text, count=1)
    
    # 1. Size
    try:
        size_val = str(os.path.getsize(local_path))
    except Exception:
        size_val = "10000000"
    
    start_tag = repl_attr(start_tag, "Size", size_val) if 'Size="' in start_tag else start_tag.replace(">", f' Size="{size_val}">', 1)
    
    # 2. Kind
    ext = local_path.suffix.lower()
    kind_val = KIND_BY_EXT.get(ext, "Unbekanntes Format")
    start_tag = repl_attr(start_tag, "Kind", kind_val) if 'Kind="' in start_tag else start_tag.replace(">", f' Kind="{kind_val}">', 1)
    
    # 3. Location
    rel_name = local_path.name
    encoded_name = quote(rel_name, safe="!$'()*+,;=:@[]-_.~")
    new_location_value = f"file://localhost{local_dir.as_posix()}/{encoded_name}"
    escaped_location_value = escape(new_location_value, {'"': '&quot;', "'": '&apos;'})
    
    if start_tag.find('Location="') != -1:
        start_tag = repl_attr(start_tag, "Location", escaped_location_value)
    else:
        start_tag = start_tag.replace(">", f' Location="{escaped_location_value}">', 1)
    
    return start_tag, True

def modify_xml(allowed_ids, assignment, source_xml, target_xml, local_dir):
    in_collection = False
    buffering_track = False
    buffer_lines = []
    
    updated_count = 0
    
    with source_xml.open("r", encoding="utf-8", newline="") as src, target_xml.open("w", encoding="utf-8", newline="") as dst:
        for line in src:
            if "<COLLECTION" in line:
                in_collection = True
            if in_collection and "</COLLECTION>" in line:
                in_collection = False
                
            if in_collection and not buffering_track and "<TRACK" in line:
                buffering_track = True
                buffer_lines = [line]
                if ">" in line:
                    start_tag = "".join(buffer_lines)
                    buffering_track = False
                    buffer_lines = []
                    
                    tid_m = re.search(r'TrackID="(\d+)"', start_tag)
                    if tid_m:
                        tid = tid_m.group(1)
                        if tid in allowed_ids and tid in assignment:
                            start_tag, changed = update_track_tag(start_tag, tid, assignment, local_dir)
                            if changed: updated_count += 1
                    dst.write(start_tag)
                continue
                
            if buffering_track:
                buffer_lines.append(line)
                if ">" in line:
                    start_tag = "".join(buffer_lines)
                    buffering_track = False
                    buffer_lines = []
                    
                    tid_m = re.search(r'TrackID="(\d+)"', start_tag)
                    if tid_m:
                        tid = tid_m.group(1)
                        if tid in allowed_ids and tid in assignment:
                            start_tag, changed = update_track_tag(start_tag, tid, assignment, local_dir)
                            if changed: updated_count += 1
                    dst.write(start_tag)
                continue
            
            dst.write(line)
            
    return updated_count


def run_logic(playlist_name, input_xml, output_xml, local_dir):
    try:
        if not input_xml.exists() or not input_xml.is_file():
            return False, f"Fehler: Die Eingabedatei {input_xml} existiert nicht."
            
        if not local_dir.exists() or not local_dir.is_dir():
            return False, f"Fehler: Das Verzeichnis {local_dir} existiert nicht."

        playlist_ids = extract_playlist_ids(input_xml, playlist_name)
        
        if not playlist_ids:
            return False, f"Keine Tracks für die Playlist '{playlist_name}' gefunden."
            
        xml_names = get_track_names(playlist_ids, input_xml)
        assignment = match_and_rename_files(xml_names, local_dir)
        
        updates = modify_xml(playlist_ids, assignment, input_xml, output_xml, local_dir)
        return True, f"{len(assignment)} Dateien gematcht und {updates} Tracks in die Datei {output_xml.name} geschrieben."
    except Exception as e:
        return False, f"Unerwarteter Fehler: {str(e)}"

def run_gui():
    root = tk.Tk()
    root.title("Rekordbox SoundCloud Matcher")
    root.geometry("650x450")
    root.resizable(False, False)

    style = ttk.Style()
    style.theme_use('clam')

    main_frame = ttk.Frame(root, padding="20 20 20 20")
    main_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    ttk.Label(main_frame, text="🎵 Rekordbox SoundCloud to Local Matcher", font=("-weight", "bold", "-size", 16)).grid(column=0, row=0, columnspan=3, pady=(0, 20))

    # Playlist Name
    ttk.Label(main_frame, text="Rekordbox Playlist Name:").grid(column=0, row=1, sticky=tk.W, pady=5)
    playlist_var = tk.StringVar(value="Schraaaaanz")
    ttk.Entry(main_frame, textvariable=playlist_var, width=40).grid(column=1, row=1, columnspan=2, sticky=tk.W, pady=5)

    # Input XML
    ttk.Label(main_frame, text="Originale RB.xml Datei:").grid(column=0, row=2, sticky=tk.W, pady=5)
    input_var = tk.StringVar()
    ttk.Entry(main_frame, textvariable=input_var, width=40, state='readonly').grid(column=1, row=2, sticky=tk.W, pady=5)
    def browse_input():
        filename = filedialog.askopenfilename(title="Wähle Rekordbox XML", filetypes=[("XML Dateien", "*.xml")])
        if filename: input_var.set(filename)
    ttk.Button(main_frame, text="Suchen...", command=browse_input).grid(column=2, row=2, padx=(10,0), pady=5)

    # Local Dir
    ttk.Label(main_frame, text="Lokaler Musikordner:").grid(column=0, row=3, sticky=tk.W, pady=5)
    dir_var = tk.StringVar()
    ttk.Entry(main_frame, textvariable=dir_var, width=40, state='readonly').grid(column=1, row=3, sticky=tk.W, pady=5)
    def browse_dir():
        dirname = filedialog.askdirectory(title="Wähle lokalen Musikordner (MP3/WAV/etc.)")
        if dirname: dir_var.set(dirname)
    ttk.Button(main_frame, text="Suchen...", command=browse_dir).grid(column=2, row=3, padx=(10,0), pady=5)

    # Log Area
    log_text = tk.Text(main_frame, height=8, width=70, state='disabled')
    log_text.grid(column=0, row=5, columnspan=3, pady=20)
    
    def log(msg):
        log_text.config(state='normal')
        log_text.insert(tk.END, msg + "\n")
        log_text.see(tk.END)
        log_text.config(state='disabled')
        root.update()

    # Progress / Execute
    def execute():
        playlist = playlist_var.get().strip()
        input_path = input_var.get().strip()
        local_dir = dir_var.get().strip()
        
        if not playlist or not input_path or not local_dir:
            messagebox.showwarning("Fehlende Angaben", "Bitte alle Felder (Playlist, XML, lokaler Ordner) ausfüllen!")
            return
            
        p_in = Path(input_path)
        p_dir = Path(local_dir)
        p_out = p_in.parent / f"{p_in.stem}_modifiziert.xml"
        
        log(f"-> Starte Abgleich für Playlist '{playlist}'...")
        log(f"-> Ordner: {p_dir.name}")
        
        btn_run.config(state='disabled')
        success, msg = run_logic(playlist, p_in, p_out, p_dir)
        if success:
            log("✅ Abgeschlossen!")
            log(msg)
            messagebox.showinfo("Erfolg!", msg)
        else:
            log("❌ Fehler aufgetreten!")
            log(msg)
            messagebox.showerror("Fehler", msg)
        btn_run.config(state='normal')

    btn_run = ttk.Button(main_frame, text="🚀 Starte Matching & Umbenennung", command=execute)
    btn_run.grid(column=0, row=4, columnspan=3, pady=15)

    # Startup message
    log("Warte auf Benutzereingaben...\nHinweis: Wenn XML-Datei und Musikordner gewählt sind,\nklicke auf 'Starte Matching & Umbenennung'.")

    root.mainloop()

def main():
    # Wenn keine oder nur GUI Argumente (Doppelklick-Start aus Dateiexplorer / Finder)
    if len(sys.argv) == 1:
        run_gui()
        return

    parser = argparse.ArgumentParser(description="Match local files to RB.xml and update.")
    parser.add_argument("-p", "--playlist", required=True, help="Name of the playlist in rekordbox")
    parser.add_argument("-i", "--input", required=True, type=Path, help="Path to input (original) RB.xml")
    parser.add_argument("-o", "--output", required=False, type=Path, help="Path to output (modified) RB.xml (Optional)")
    parser.add_argument("-d", "--dir", required=True, type=Path, help="Path to local folder containing the audio files")
    
    args = parser.parse_args()
    
    out_path = args.output if args.output else args.input.parent / f"{args.input.stem}_modifiziert.xml"
    
    success, msg = run_logic(args.playlist, args.input, out_path, args.dir)
    print(msg)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
