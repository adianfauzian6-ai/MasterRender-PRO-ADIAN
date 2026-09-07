import os
import sys
import random
import subprocess
import threading
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

APP_NAME = "MasterRender PRO by Scratchones (ADIAN)"
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1500x900")
        self.minsize(1100, 700)

        self.bg = "#172033"
        self.panel = "#202b42"
        self.panel2 = "#263550"
        self.input_bg = "#f3f6fb"
        self.text = "#eaf0f8"
        self.accent = "#4f8cff"
        self.accent2 = "#65c7ff"
        self.danger = "#e85b6f"
        self.border = "#405171"

        self.configure(bg=self.bg)
        self.video_path = tk.StringVar()
        self.audio_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.output_name = tk.StringVar(value="hasil_render")
        self.transition = tk.StringVar(value="Fade")
        self.quality = tk.StringVar(value="Mengikuti Master")
        self.variations = tk.IntVar(value=1)
        self.loop_count = tk.IntVar(value=1)
        self.random_audio = tk.BooleanVar(value=False)
        self.create_txt = tk.BooleanVar(value=True)
        self.random_volume = tk.BooleanVar(value=False)
        self.use_all_audio = tk.BooleanVar(value=True)
        self.stop_flag = False

        self.style_ui()
        self.build()

        self.log("[READY] Aplikasi siap digunakan.")
        ff = self.ffmpeg_path()
        if ff:
            self.log(f"[INFO] FFmpeg terdeteksi: {ff}")
        else:
            self.log("[WARN] FFmpeg internal tidak ditemukan.")

    def style_ui(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", font=("Segoe UI", 10))
        s.configure("TNotebook", background=self.panel, borderwidth=0)
        s.configure("TNotebook.Tab", padding=(28, 10), background="#dce9f7",
                    foreground="#16375e", font=("Segoe UI", 10, "bold"))
        s.map("TNotebook.Tab", background=[("selected", "#ffffff")])
        s.configure("TButton", padding=(12, 8), background="#e8f2fb",
                    foreground="#17395f", font=("Segoe UI", 10, "bold"))
        s.map("TButton", background=[("active", "#ffffff")])
        s.configure("Accent.TButton", background=self.accent, foreground="white")
        s.map("Accent.TButton", background=[("active", "#6a9dff")])
        s.configure("Danger.TButton", background=self.danger, foreground="white")
        s.map("Danger.TButton", background=[("active", "#f07787")])
        s.configure("TCheckbutton", background=self.panel2, foreground=self.text)
        s.configure("TLabelframe", background=self.panel2, foreground=self.text)
        s.configure("TLabelframe.Label", background=self.panel2, foreground=self.text,
                    font=("Segoe UI", 10, "bold"))
        s.configure("TLabel", background=self.panel2, foreground=self.text)

    def build(self):
        top = tk.Frame(self, bg=self.accent, height=46)
        top.pack(fill="x")
        tk.Label(top, text=APP_NAME, bg=self.accent, fg="white",
                 font=("Segoe UI", 13, "bold")).pack(side="left", padx=18, pady=10)

        body = tk.Frame(self, bg=self.bg)
        body.pack(fill="both", expand=True, padx=10, pady=10)

        left = tk.Frame(body, bg=self.panel, highlightbackground=self.border, highlightthickness=1)
        left.pack(side="left", fill="both", expand=True, padx=(0, 7))
        right = tk.Frame(body, bg=self.panel, width=300, highlightbackground=self.border, highlightthickness=1)
        right.pack(side="right", fill="y", padx=(7, 0))
        right.pack_propagate(False)

        self.log_frame(right)

        self.nb = ttk.Notebook(left)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)

        self.input_tab = tk.Frame(self.nb, bg=self.panel2)
        self.render_tab = tk.Frame(self.nb, bg=self.panel2)
        self.stream_tab = tk.Frame(self.nb, bg=self.panel2)
        self.nb.add(self.input_tab, text="Input")
        self.nb.add(self.render_tab, text="Render & Variasi")
        self.nb.add(self.stream_tab, text="Live Streaming")

        self.build_input()
        self.build_render()
        self.build_stream()

        bottom = tk.Frame(left, bg=self.panel)
        bottom.pack(fill="x", padx=10, pady=(0, 10))
        self.start_btn = ttk.Button(bottom, text="START RENDER", style="Accent.TButton",
                                    command=self.start_render)
        self.start_btn.grid(row=0, column=0, sticky="ew", padx=(0,5))
        ttk.Button(bottom, text="STOP", style="Danger.TButton",
                   command=self.stop_render).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(bottom, text="OPEN OUTPUT", command=self.open_output).grid(row=0, column=2, sticky="ew", padx=(5,0))
        bottom.columnconfigure(0, weight=1); bottom.columnconfigure(1, weight=1); bottom.columnconfigure(2, weight=1)

        self.progress = ttk.Progressbar(left, mode="determinate", maximum=100)
        self.progress.pack(fill="x", padx=10)
        self.status = tk.Label(left, text="Siap digunakan.", bg=self.panel, fg="#c9d7e8",
                               anchor="w", font=("Segoe UI", 9))
        self.status.pack(fill="x", padx=10, pady=(5, 10))

    def log_frame(self, parent):
        tk.Label(parent, text="Log", bg=self.panel, fg=self.text,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(12,5))
        self.log_box = tk.Text(parent, bg="#111827", fg="#bfe2ff", insertbackground="white",
                               font=("Consolas", 9), relief="flat", wrap="none")
        self.log_box.pack(fill="both", expand=True, padx=8, pady=4)
        ttk.Button(parent, text="Bersihkan", command=lambda: self.log_box.delete("1.0","end")).pack(
            fill="x", padx=8, pady=(4,8))

    def log(self, msg):
        def write():
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
        self.after(0, write)

    def labeled_entry(self, parent, row, label, variable, buttons=None):
        tk.Label(parent, text=label, bg=self.panel2, fg=self.text).grid(row=row, column=0, sticky="w", padx=10, pady=8)
        e = tk.Entry(parent, textvariable=variable, bg=self.input_bg, fg="#18324d",
                     relief="flat", font=("Segoe UI", 10))
        e.grid(row=row, column=1, sticky="ew", padx=8, pady=8, ipady=4)
        if buttons:
            for i, (txt, cmd) in enumerate(buttons):
                ttk.Button(parent, text=txt, command=cmd).grid(row=row, column=2+i, padx=4, pady=6)
        return e

    def build_input(self):
        p = self.input_tab
        p.columnconfigure(1, weight=1)
        self.labeled_entry(p, 0, "Video Master", self.video_path, [("Pilih", self.pick_video), ("Hapus", lambda: self.video_path.set(""))])
        self.labeled_entry(p, 1, "Folder Lagu", self.audio_folder, [("Pilih", self.pick_audio_folder), ("Hapus", lambda: self.audio_folder.set(""))])
        self.labeled_entry(p, 2, "Folder Output", self.output_folder, [("Pilih", self.pick_output_folder), ("Hapus", lambda: self.output_folder.set(""))])
        self.labeled_entry(p, 3, "Nama Output", self.output_name, [("Scan", self.scan_audio), ("Hapus Input", self.clear_input)])

        tk.Label(p, text="Daftar ini adalah lagu yang masuk album. Pilih lagu lalu hapus jika tidak ingin dipakai.",
                 bg=self.panel2, fg="#d7e4f2", anchor="w").grid(row=4, column=0, columnspan=4, sticky="ew", padx=10, pady=(8,3))

        btnrow = tk.Frame(p, bg=self.panel2)
        btnrow.grid(row=5, column=0, columnspan=4, sticky="ew", padx=10)
        for i in range(3): btnrow.columnconfigure(i, weight=1)
        ttk.Button(btnrow, text="Hapus Lagu Terpilih", command=self.remove_selected).grid(row=0,column=0,sticky="ew",padx=4,pady=5)
        ttk.Button(btnrow, text="Pilih Semua", command=self.select_all).grid(row=0,column=1,sticky="ew",padx=4,pady=5)
        ttk.Button(btnrow, text="Scan Ulang", command=self.scan_audio).grid(row=0,column=2,sticky="ew",padx=4,pady=5)

        lf = ttk.LabelFrame(p, text="Daftar Lagu Album")
        lf.grid(row=6, column=0, columnspan=4, sticky="nsew", padx=10, pady=6)
        p.rowconfigure(6, weight=1)
        self.audio_list = tk.Listbox(lf, selectmode="extended", bg=self.input_bg, fg="#18324d",
                                     font=("Segoe UI", 10), relief="flat")
        sb = ttk.Scrollbar(lf, command=self.audio_list.yview)
        self.audio_list.configure(yscrollcommand=sb.set)
        self.audio_list.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        sb.pack(side="right", fill="y", pady=5)

    def build_render(self):
        p = self.render_tab
        p.columnconfigure(1, weight=1)
        box = ttk.LabelFrame(p, text="Mode Render & Variasi")
        box.pack(fill="x", padx=10, pady=10)
        box.columnconfigure(1, weight=1)

        self.combo(box, 0, "Transisi Loop", self.transition, ["Fade", "Hard Cut"])
        self.combo(box, 1, "Kualitas", self.quality, ["Mengikuti Master", "Cepat", "Kualitas Tinggi"])

        opts = tk.Frame(box, bg=self.panel2)
        opts.grid(row=2, column=0, columnspan=3, sticky="w", padx=10, pady=8)
        ttk.Checkbutton(opts, text="Acak urutan lagu", variable=self.random_audio).grid(row=0,column=0,sticky="w",padx=(0,20))
        ttk.Checkbutton(opts, text="Ratakkan volume lagu", variable=self.random_volume).grid(row=0,column=1,sticky="w")
        ttk.Checkbutton(opts, text="Buat .txt", variable=self.create_txt).grid(row=1,column=0,sticky="w",padx=(0,20))
        ttk.Checkbutton(opts, text="Buat beberapa variasi", variable=self.use_all_audio).grid(row=1,column=1,sticky="w")

        self.spin(box, 3, "Jumlah variasi", self.variations, 1, 100)
        self.spin(box, 4, "Loop video", self.loop_count, 1, 9999)
        self.spin(box, 5, "Total lagu yang dipakai", self.use_all_audio, 1, 9999, boolvar=True)

        tk.Label(p, text="Contoh: video 20 detik + lagu 3 menit → video di-loop sampai durasi lagu, lalu audio dipasang.",
                 bg=self.panel2, fg="#d7e4f2", anchor="w").pack(fill="x", padx=10, pady=4)
        tk.Label(p, text="Rekomendasi: Fade + Mengikuti Master untuk hasil aman dan cepat.",
                 bg=self.panel2, fg="#9fc9ef", anchor="w").pack(fill="x", padx=10)

    def combo(self, parent, row, label, variable, values):
        tk.Label(parent, text=label, bg=self.panel2, fg=self.text).grid(row=row,column=0,sticky="w",padx=10,pady=7)
        ttk.Combobox(parent, textvariable=variable, values=values, state="readonly", width=25).grid(row=row,column=1,sticky="w",padx=8,pady=7)

    def spin(self, parent, row, label, variable, mn, mx, boolvar=False):
        tk.Label(parent, text=label, bg=self.panel2, fg=self.text).grid(row=row,column=0,sticky="w",padx=10,pady=7)
        if boolvar:
            # Keep a numeric value separate because a Checkbutton is not suitable here.
            if not hasattr(self, "audio_count"):
                self.audio_count = tk.IntVar(value=1)
            var = self.audio_count
        else:
            var = variable
        tk.Spinbox(parent, from_=mn, to=mx, textvariable=var, width=10, bg=self.input_bg,
                   fg="#18324d", relief="flat").grid(row=row,column=1,sticky="w",padx=8,pady=7)

    def build_stream(self):
        p = self.stream_tab
        tk.Label(p, text="Live Streaming", bg=self.panel2, fg=self.text,
                 font=("Segoe UI", 16, "bold")).pack(pady=(60,10))
        tk.Label(p, text="Panel streaming siap dikembangkan untuk RTMP/YouTube/TikTok.\n"
                         "Versi ini fokus pada looping video + penambahan lagu + export MP4.",
                 bg=self.panel2, fg="#d7e4f2", justify="center").pack()

    def ffmpeg_path(self):
        # In the final EXE, ffmpeg.exe is unpacked by PyInstaller to a
        # temporary _MEIPASS folder. Fall back to the executable folder.
        candidates = []
        if getattr(sys, "frozen", False):
            meipass = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
            candidates.append(meipass / "ffmpeg.exe")
            candidates.append(Path(sys.executable).resolve().parent / "ffmpeg.exe")
        else:
            candidates.append(Path(__file__).resolve().parent / "ffmpeg.exe")
            candidates.append(Path(__file__).resolve().parent.parent / "bin" / "ffmpeg.exe")
        for p in candidates:
            if p.is_file():
                return str(p)
        return shutil.which("ffmpeg")

    def pick_video(self):
        f = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mov *.mkv *.avi *.webm"), ("Semua file", "*.*")])
        if f:
            self.video_path.set(f); self.log(f"[INFO] Video: {f}")

    def pick_audio_folder(self):
        d = filedialog.askdirectory()
        if d:
            self.audio_folder.set(d); self.scan_audio()

    def pick_output_folder(self):
        d = filedialog.askdirectory()
        if d:
            self.output_folder.set(d)

    def clear_input(self):
        self.video_path.set(""); self.audio_folder.set(""); self.audio_list.delete(0,"end")

    def scan_audio(self):
        self.audio_list.delete(0, "end")
        folder = self.audio_folder.get().strip()
        if not folder or not os.path.isdir(folder):
            self.log("[WARN] Folder lagu belum dipilih.")
            return
        files = sorted([str(x) for x in Path(folder).iterdir() if x.is_file() and x.suffix.lower() in AUDIO_EXTS])
        for f in files:
            self.audio_list.insert("end", f)
        self.log(f"[INFO] {len(files)} lagu ditemukan.")
        if files:
            self.audio_list.selection_set(0, "end")

    def remove_selected(self):
        sel = list(self.audio_list.curselection())[::-1]
        for i in sel: self.audio_list.delete(i)

    def select_all(self):
        self.audio_list.selection_set(0, "end")

    def stop_render(self):
        self.stop_flag = True
        self.log("[INFO] Stop diminta. Proses FFmpeg akan dihentikan pada langkah aman berikutnya.")
        self.status.config(text="Menghentikan...")

    def open_output(self):
        folder = self.output_folder.get().strip()
        if not folder:
            folder = str(Path.cwd())
        os.makedirs(folder, exist_ok=True)
        try:
            os.startfile(folder)
        except Exception:
            subprocess.Popen(["xdg-open", folder])

    def start_render(self):
        if not self.ffmpeg_path():
            messagebox.showerror("FFmpeg internal tidak ditemukan",
                                 "Build aplikasi tidak lengkap. Silakan build ulang.")
            return
        video = self.video_path.get().strip()
        if not video or not os.path.isfile(video):
            messagebox.showwarning("Input belum lengkap", "Pilih Video Master terlebih dahulu.")
            return
        audios = [self.audio_list.get(i) for i in self.audio_list.curselection()]
        if not audios:
            audios = [self.audio_list.get(i) for i in range(self.audio_list.size())]
        if not audios:
            messagebox.showwarning("Lagu belum ada", "Pilih folder lagu lalu Scan.")
            return
        out = self.output_folder.get().strip() or str(Path(video).parent / "output")
        os.makedirs(out, exist_ok=True)
        try:
            variations = max(1, int(self.variations.get()))
            loops = max(1, int(self.loop_count.get()))
            count = max(1, int(self.audio_count.get()))
        except Exception:
            messagebox.showerror("Pengaturan salah", "Jumlah variasi/loop/lagu harus berupa angka.")
            return
        self.stop_flag = False
        self.start_btn.config(state="disabled")
        threading.Thread(target=self.render_worker,
                         args=(video, audios, out, variations, loops, count), daemon=True).start()

    def render_worker(self, video, audios, out, variations, loops, count):
        try:
            pool = audios[:]
            if self.random_audio.get():
                random.shuffle(pool)
            pool = pool[:count] if count < len(pool) else pool

            total = max(1, variations * len(pool))
            done = 0
            self.log(f"[INFO] Mulai render: {variations} variasi x {len(pool)} lagu.")
            for v in range(1, variations + 1):
                if self.stop_flag: break
                current = pool[:]
                if self.random_audio.get(): random.shuffle(current)
                for idx, audio in enumerate(current, 1):
                    if self.stop_flag: break
                    stem = f"{self.output_name.get().strip() or 'hasil_render'}_v{v:02d}_{idx:02d}"
                    outfile = os.path.join(out, stem + ".mp4")
                    self.log(f"[RENDER] {Path(audio).name} -> {outfile}")
                    ok = self.render_one(video, audio, outfile, loops)
                    done += 1
                    self.after(0, lambda p=done/total*100: self.progress.config(value=p))
                    if ok:
                        self.log("[OK] Render selesai.")
                        if self.create_txt.get():
                            try:
                                with open(os.path.splitext(outfile)[0] + ".txt", "w", encoding="utf-8") as f:
                                    f.write(f"Video: {video}\nAudio: {audio}\n")
                            except Exception as e:
                                self.log(f"[WARN] TXT gagal: {e}")
                    else:
                        self.log("[ERROR] Render gagal.")
            self.after(0, lambda: self.status.config(text="Dihentikan." if self.stop_flag else "Render selesai."))
        finally:
            self.after(0, lambda: self.start_btn.config(state="normal"))

    def render_one(self, video, audio, outfile, loops):
        # Loop video indefinitely, then stop when audio ends. Short input videos repeat seamlessly.
        vf = f"scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p"
        if self.quality.get() == "Cepat":
            vcodec = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23"]
        elif self.quality.get() == "Kualitas Tinggi":
            vcodec = ["-c:v", "libx264", "-preset", "slow", "-crf", "18"]
        else:
            vcodec = ["-c:v", "libx264", "-preset", "medium", "-crf", "20"]

        cmd = [
            self.ffmpeg_path(), "-y",
            "-stream_loop", "-1", "-i", video,
            "-i", audio,
            "-map", "0:v:0", "-map", "1:a:0",
            "-vf", vf,
            *vcodec,
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            outfile
        ]
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                 encoding="utf-8", errors="replace")
            while True:
                line = p.stdout.readline()
                if line:
                    if "time=" in line:
                        self.after(0, lambda s=line[-90:].strip(): self.status.config(text="Rendering... " + s))
                elif p.poll() is not None:
                    break
                if self.stop_flag:
                    p.terminate()
                    try: p.wait(timeout=2)
                    except subprocess.TimeoutExpired: p.kill()
                    return False
            return p.returncode == 0
        except Exception as e:
            self.log(f"[ERROR] {e}")
            return False

if __name__ == "__main__":
    App().mainloop()
