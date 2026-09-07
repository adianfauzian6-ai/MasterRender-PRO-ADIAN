import os
import sys
import random
import subprocess
import threading
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

APP_NAME = "MasterRender PRO by AfroxSTD (ADIAN)"
MAX_VIDEOS = 60
MAX_SONGS = 20
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}


def find_ffmpeg():
    candidates = []
    if getattr(sys, "frozen", False):
        meipass = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        candidates += [meipass / "ffmpeg.exe", Path(sys.executable).resolve().parent / "ffmpeg.exe"]
    else:
        here = Path(__file__).resolve().parent
        candidates += [here / "ffmpeg.exe", here.parent / "bin" / "ffmpeg.exe"]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return shutil.which("ffmpeg") or ""


class MasterRender(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1400x850")
        self.minsize(1100, 700)
        self.configure(bg="#0b0d17")
        self.videos = []
        self.audio_files = []
        self.stop_flag = threading.Event()
        self.render_thread = None
        self.ffmpeg = find_ffmpeg()
        self.song_count = tk.IntVar(value=10)
        self.random_audio = tk.BooleanVar(value=True)
        self.quality = tk.StringVar(value="Mengikuti Master")
        self.output_dir = tk.StringVar(value=str(Path.cwd() / "output"))
        self.variation_count = tk.IntVar(value=1)
        self._setup_style()
        self._build_ui()
        self.log("READY", "Aplikasi siap digunakan.")
        if self.ffmpeg:
            self.log("INFO", f"FFmpeg terdeteksi: {self.ffmpeg}")
        else:
            self.log("WARN", "FFmpeg belum ditemukan. Letakkan ffmpeg.exe di folder aplikasi.")

    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background="#111426", foreground="#e8eaff", fieldbackground="#171a2d")
        style.configure("TNotebook", background="#0b0d17", borderwidth=0)
        style.configure("TNotebook.Tab", background="#15182a", foreground="#aeb4d8", padding=(22, 10), font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#24204b")], foreground=[("selected", "#c9bfff")])
        style.configure("TButton", background="#171a2d", foreground="#dfe2f5", padding=(11, 8), font=("Segoe UI", 9, "bold"))
        style.map("TButton", background=[("active", "#282d4a")])
        style.configure("TCheckbutton", background="#111426", foreground="#cfd2ee")
        style.configure("TProgressbar", troughcolor="#15182a", background="#8b6cff", borderwidth=0)

    def _label(self, parent, text, size=10, bold=False):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg="#eef0ff", font=("Segoe UI", size, "bold" if bold else "normal"))

    def _card(self, parent):
        return tk.Frame(parent, bg="#111426", highlightbackground="#252943", highlightthickness=1, bd=0)

    def _build_ui(self):
        top = tk.Frame(self, bg="#0b0d17")
        top.pack(fill="x", padx=22, pady=(18, 8))
        tk.Label(top, text="MASTERRENDER PRO", bg="#0b0d17", fg="#f2f0ff", font=("Segoe UI", 22, "bold")).pack(side="left")
        tk.Label(top, text="  by AfroxSTD  •  ADIAN", bg="#0b0d17", fg="#9e8cff", font=("Segoe UI", 11, "bold")).pack(side="left", pady=(8, 0))
        self.status_badge = tk.Label(top, text="● READY", bg="#171a2d", fg="#9b8cff", font=("Segoe UI", 9, "bold"), padx=14, pady=7)
        self.status_badge.pack(side="right")
        body = tk.Frame(self, bg="#0b0d17")
        body.pack(fill="both", expand=True, padx=22, pady=8)
        side = tk.Frame(body, bg="#101323", width=210)
        side.pack(side="left", fill="y", padx=(0, 14))
        side.pack_propagate(False)
        tk.Label(side, text="WORKSPACE", bg="#101323", fg="#777eaa", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=18, pady=(20, 12))
        for txt in ["Dashboard", "Input Media", "Render & Variasi", "Live Streaming", "Settings"]:
            active = txt == "Render & Variasi"
            tk.Label(side, text=("◆  " if active else "   ") + txt, bg="#24204b" if active else "#101323", fg="#c9bfff" if active else "#9298bd", anchor="w", padx=16, pady=11, font=("Segoe UI", 10, "bold" if active else "normal")).pack(fill="x", padx=9, pady=2)
        main = tk.Frame(body, bg="#0b0d17")
        main.pack(side="left", fill="both", expand=True)
        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill="both", expand=True)
        self.input_tab = tk.Frame(self.notebook, bg="#0b0d17")
        self.render_tab = tk.Frame(self.notebook, bg="#0b0d17")
        self.live_tab = tk.Frame(self.notebook, bg="#0b0d17")
        self.notebook.add(self.input_tab, text="  Input  ")
        self.notebook.add(self.render_tab, text="  Render & Variasi  ")
        self.notebook.add(self.live_tab, text="  Live Streaming  ")
        self._build_input()
        self._build_render()
        self._build_live()
        bottom = tk.Frame(self, bg="#0b0d17")
        bottom.pack(fill="x", padx=22, pady=(4, 18))
        self.progress = ttk.Progressbar(bottom, mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(0, 8))
        self.progress_text = tk.Label(bottom, text="Siap merender hingga 60 video", bg="#0b0d17", fg="#858caf", font=("Segoe UI", 9))
        self.progress_text.pack(side="left")
        btns = tk.Frame(bottom, bg="#0b0d17")
        btns.pack(side="right")
        ttk.Button(btns, text="OPEN OUTPUT", command=self.open_output).pack(side="left", padx=4)
        ttk.Button(btns, text="BERSIHKAN LOG", command=self.clear_log).pack(side="left", padx=4)
        self.stop_btn = ttk.Button(btns, text="STOP", command=self.stop_render)
        self.stop_btn.pack(side="left", padx=4)
        tk.Button(btns, text="START RENDER", command=self.start_render, bg="#7d5cff", fg="white", activebackground="#9a7fff", activeforeground="white", relief="flat", bd=0, font=("Segoe UI", 10, "bold"), padx=24, pady=11).pack(side="left", padx=(8, 0))

    def _build_input(self):
        left = self._card(self.input_tab); left.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=12)
        right = self._card(self.input_tab); right.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=12)
        self._label(left, "VIDEO INPUT", 11, True).pack(anchor="w", padx=18, pady=(18, 5))
        tk.Label(left, text="Tambahkan maksimal 60 video untuk batch rendering.", bg="#111426", fg="#858caf", font=("Segoe UI", 9)).pack(anchor="w", padx=18)
        row = tk.Frame(left, bg="#111426"); row.pack(fill="x", padx=18, pady=14)
        ttk.Button(row, text="+ TAMBAH VIDEO", command=self.add_videos).pack(side="left")
        ttk.Button(row, text="HAPUS SEMUA", command=self.clear_videos).pack(side="left", padx=8)
        self.video_count = tk.Label(row, text="0 / 60", bg="#111426", fg="#b8aaff", font=("Segoe UI", 10, "bold")); self.video_count.pack(side="right")
        self.video_list = tk.Listbox(left, bg="#0d1020", fg="#cfd2ee", selectbackground="#30285e", selectforeground="white", relief="flat", bd=0, font=("Segoe UI", 9))
        self.video_list.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        self._label(right, "AUDIO TRACKS", 11, True).pack(anchor="w", padx=18, pady=(18, 5))
        tk.Label(right, text="Masukkan maksimal 20 lagu. Jumlah yang dipakai dapat diatur saat render.", bg="#111426", fg="#858caf", font=("Segoe UI", 9)).pack(anchor="w", padx=18)
        row2 = tk.Frame(right, bg="#111426"); row2.pack(fill="x", padx=18, pady=14)
        ttk.Button(row2, text="+ TAMBAH AUDIO", command=self.add_audio).pack(side="left")
        ttk.Button(row2, text="HAPUS SEMUA", command=self.clear_audio).pack(side="left", padx=8)
        self.audio_count_label = tk.Label(row2, text="0 / 20 lagu", bg="#111426", fg="#b8aaff", font=("Segoe UI", 10, "bold")); self.audio_count_label.pack(side="right")
        self.audio_list = tk.Listbox(right, bg="#0d1020", fg="#cfd2ee", selectbackground="#30285e", selectforeground="white", relief="flat", bd=0, font=("Segoe UI", 9))
        self.audio_list.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    def _build_render(self):
        settings = self._card(self.render_tab); settings.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=12)
        logcard = self._card(self.render_tab); logcard.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=12)
        self._label(settings, "RENDER SETTINGS", 11, True).pack(anchor="w", padx=18, pady=(18, 15))
        grid = tk.Frame(settings, bg="#111426"); grid.pack(fill="x", padx=18)
        tk.Label(grid, text="Total lagu yang akan diacak", bg="#111426", fg="#eef0ff", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=8)
        ttk.Spinbox(grid, from_=1, to=20, textvariable=self.song_count, width=27).grid(row=0, column=1, sticky="e", padx=(25, 0), pady=8)
        tk.Label(grid, text="(maks. 20)", bg="#111426", fg="#858caf", font=("Segoe UI", 9)).grid(row=0, column=2, sticky="w", padx=8)
        self._row(grid, 1, "Quality", ttk.Combobox(grid, textvariable=self.quality, values=["Mengikuti Master", "Cepat", "Kualitas Tinggi"], state="readonly", width=25))
        self._row(grid, 2, "Variasi per video", ttk.Spinbox(grid, from_=1, to=100, textvariable=self.variation_count, width=27))
        ttk.Checkbutton(grid, text="Acak ulang playlist untuk setiap video", variable=self.random_audio).grid(row=3, column=0, columnspan=3, sticky="w", pady=10)
        self._label(settings, "OUTPUT FOLDER", 10, True).pack(anchor="w", padx=18, pady=(22, 8))
        outrow = tk.Frame(settings, bg="#111426"); outrow.pack(fill="x", padx=18)
        tk.Entry(outrow, textvariable=self.output_dir, bg="#0d1020", fg="#cfd2ee", insertbackground="white", relief="flat", font=("Segoe UI", 9)).pack(side="left", fill="x", expand=True, ipady=8)
        ttk.Button(outrow, text="...", command=self.choose_output).pack(side="left", padx=(7, 0))
        tk.Label(settings, text="Durasi output otomatis = total durasi lagu yang dipilih. Video akan di-loop sampai playlist selesai.", bg="#111426", fg="#858caf", wraplength=500, justify="left", font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=18)
        self._label(logcard, "RENDER LOG", 11, True).pack(anchor="w", padx=18, pady=(18, 10))
        self.logbox = tk.Text(logcard, bg="#0a0d18", fg="#bfc5e8", insertbackground="white", relief="flat", bd=0, font=("Consolas", 9), wrap="word")
        self.logbox.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        for tag, color in [("READY", "#9b8cff"), ("INFO", "#8fa8ff"), ("RENDER", "#d4b3ff"), ("ERROR", "#ff7d96"), ("WARN", "#ffca7a"), ("FFMPEG", "#8ee6d4")]: self.logbox.tag_config(tag, foreground=color)

    def _row(self, parent, r, label, widget):
        tk.Label(parent, text=label, bg="#111426", fg="#858caf", font=("Segoe UI", 9)).grid(row=r, column=0, sticky="w", pady=6)
        widget.grid(row=r, column=1, columnspan=2, sticky="e", padx=(35, 0), pady=6)
        parent.grid_columnconfigure(1, weight=1)

    def _build_live(self):
        frame = self._card(self.live_tab); frame.pack(fill="both", expand=True, padx=12, pady=12)
        self._label(frame, "LIVE STREAMING", 14, True).pack(anchor="w", padx=22, pady=(22, 8))
        tk.Label(frame, text="Panel streaming disiapkan untuk integrasi RTMP pada versi berikutnya.", bg="#111426", fg="#858caf", font=("Segoe UI", 10)).pack(anchor="w", padx=22)

    def add_videos(self):
        files = filedialog.askopenfilenames(title="Pilih video", filetypes=[("Video", "*.mp4 *.mov *.mkv *.avi *.webm *.m4v"), ("Semua file", "*.*")])
        remaining = MAX_VIDEOS - len(self.videos)
        for f in files[:max(0, remaining)]:
            if f not in self.videos: self.videos.append(f)
        self._refresh_video_list()

    def _refresh_video_list(self):
        self.video_list.delete(0, "end")
        for i, f in enumerate(self.videos, 1): self.video_list.insert("end", f"{i:02d}. {Path(f).name}")
        self.video_count.config(text=f"{len(self.videos)} / {MAX_VIDEOS}")

    def add_audio(self):
        files = filedialog.askopenfilenames(title="Pilih lagu", filetypes=[("Audio", "*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.opus"), ("Semua file", "*.*")])
        remaining = MAX_SONGS - len(self.audio_files)
        for f in files[:max(0, remaining)]:
            if f not in self.audio_files: self.audio_files.append(f)
        self._refresh_audio_list()

    def _refresh_audio_list(self):
        self.audio_list.delete(0, "end")
        for i, f in enumerate(self.audio_files, 1): self.audio_list.insert("end", f"{i:02d}. {Path(f).name}")
        self.audio_count_label.config(text=f"{len(self.audio_files)} / {MAX_SONGS} lagu")

    def clear_videos(self): self.videos.clear(); self._refresh_video_list()
    def clear_audio(self): self.audio_files.clear(); self._refresh_audio_list()
    def choose_output(self):
        d = filedialog.askdirectory(title="Pilih folder output")
        if d: self.output_dir.set(d)
    def open_output(self):
        os.makedirs(self.output_dir.get(), exist_ok=True)
        os.startfile(self.output_dir.get())
    def clear_log(self): self.logbox.delete("1.0", "end")
    def log(self, tag, text):
        def write():
            self.logbox.insert("end", f"[{tag}] {text}\n", tag if tag in ("READY","INFO","RENDER","ERROR","WARN","FFMPEG") else None)
            self.logbox.see("end")
        self.after(0, write)

    def start_render(self):
        if self.render_thread and self.render_thread.is_alive(): return
        if not self.videos: messagebox.showwarning(APP_NAME, "Tambahkan minimal 1 video."); return
        if not self.audio_files: messagebox.showwarning(APP_NAME, "Tambahkan minimal 1 lagu."); return
        try: n = int(self.song_count.get())
        except Exception: n = 1
        if not 1 <= n <= MAX_SONGS: messagebox.showwarning(APP_NAME, "Total lagu harus 1 sampai 20."); return
        if n > len(self.audio_files): messagebox.showwarning(APP_NAME, f"Diminta {n} lagu, tetapi hanya ada {len(self.audio_files)} lagu."); return
        if not self.ffmpeg:
            messagebox.showerror(APP_NAME, "FFmpeg tidak ditemukan. Letakkan ffmpeg.exe di folder aplikasi."); return
        os.makedirs(self.output_dir.get(), exist_ok=True)
        self.stop_flag.clear(); self.progress["value"] = 0
        self.log("INFO", f"Mulai: {len(self.videos)} video, {n} lagu dipilih per video.")
        self.render_thread = threading.Thread(target=self.render_worker, args=(n,), daemon=True)
        self.render_thread.start()

    def stop_render(self):
        self.stop_flag.set(); self.log("WARN", "STOP diminta. Proses aktif akan dihentikan.")

    def render_worker(self, n):
        total = len(self.videos)
        for idx, video in enumerate(self.videos, 1):
            if self.stop_flag.is_set(): break
            playlist = list(self.audio_files)
            random.shuffle(playlist)
            playlist = playlist[:n]
            self.log("RENDER", f"Video {idx}/{total}: {Path(video).name}")
            self.log("INFO", "Urutan acak: " + " | ".join(Path(x).name for x in playlist))
            for var in range(1, max(1, int(self.variation_count.get())) + 1):
                if self.stop_flag.is_set(): break
                try:
                    out = self.render_one(video, playlist, idx, var)
                    self.log("INFO", f"SELESAI: {Path(out).name}")
                except Exception as e:
                    self.log("ERROR", str(e))
            self.after(0, lambda p=idx/total*100: self.progress.configure(value=p))
            self.after(0, lambda i=idx,t=total: self.progress_text.config(text=f"Video {i}/{t} selesai"))
        self.log("READY", "Render selesai." if not self.stop_flag.is_set() else "Render dihentikan.")

    def render_one(self, video, playlist, index, variation):
        base = Path(self.output_dir.get())
        stem = Path(video).stem
        listfile = base / f".playlist_{os.getpid()}_{index}_{variation}.txt"
        audiofile = base / f".playlist_{os.getpid()}_{index}_{variation}.m4a"
        outfile = self.unique_output(base / f"{stem}_MasterRender_V{variation}.mp4")
        try:
            with open(listfile, "w", encoding="utf-8") as f:
                for song in playlist:
                    p = str(Path(song).resolve()).replace("\\", "/").replace("'", "'\\''")
                    f.write(f"file '{p}'\n")
            # First make one continuous AAC playlist. This guarantees all selected songs
            # play fully and consecutively, regardless of their individual durations.
            cmd_audio = [self.ffmpeg, "-hide_banner", "-nostdin", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile), "-vn", "-c:a", "aac", "-b:a", "192k", str(audiofile)]
            if self.run_ffmpeg(cmd_audio) != 0: raise RuntimeError("Gagal menggabungkan playlist audio. Lihat log FFmpeg.")
            preset, crf = self.video_settings()
            # Infinite video loop + complete audio playlist. -shortest makes the video
            # stop exactly when the combined playlist ends, not when the first song ends.
            cmd_video = [self.ffmpeg, "-hide_banner", "-nostdin", "-y", "-stream_loop", "-1", "-i", str(video), "-i", str(audiofile), "-map", "0:v:0", "-map", "1:a:0", "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p", "-c:v", "libx264", "-preset", preset, "-crf", crf, "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(outfile)]
            if self.run_ffmpeg(cmd_video) != 0: raise RuntimeError("Render video gagal. Lihat log FFmpeg.")
            return str(outfile)
        finally:
            for p in (listfile, audiofile):
                try: Path(p).unlink()
                except OSError: pass

    def video_settings(self):
        q = self.quality.get()
        if q == "Cepat": return "veryfast", "23"
        if q == "Kualitas Tinggi": return "slow", "18"
        return "medium", "20"

    def run_ffmpeg(self, cmd):
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace", bufsize=1)
            for line in p.stdout:
                line = line.rstrip()
                low = line.lower()
                if any(x in low for x in ("error", "invalid", "failed", "unable", "no such", "conversion failed")):
                    self.log("FFMPEG", line)
            return p.wait()
        except Exception as e:
            self.log("ERROR", f"FFmpeg exception: {e}")
            return -1

    def unique_output(self, path):
        path = Path(path)
        if not path.exists(): return path
        i = 2
        while True:
            candidate = path.with_name(f"{path.stem}_{i}{path.suffix}")
            if not candidate.exists(): return candidate
            i += 1


if __name__ == "__main__":
    MasterRender().mainloop()
