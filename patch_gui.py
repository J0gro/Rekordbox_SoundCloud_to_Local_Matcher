import sys
with open("rekordbox_soundcloud_matcher.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add tkinter and sys imports at the top
import_str = """import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
"""
content = content.replace("import os\n", import_str, 1)

# Split out the logic and add the new main() including the GUI
logic_and_gui = """
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
        log_text.insert(tk.END, msg + "\\n")
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
    log("Warte auf Benutzereingaben...\\nHinweis: Wenn XML-Datei und Musikordner gewählt sind,\\nklicke auf 'Starte Matching & Umbenennung'.")

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
"""

# Replace old main logic
content = content.split("def main():")[0]
content += logic_and_gui

with open("rekordbox_soundcloud_matcher.py", "w", encoding="utf-8") as f:
    f.write(content)
