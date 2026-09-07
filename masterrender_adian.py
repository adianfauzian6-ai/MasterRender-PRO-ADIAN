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
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}


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
        top = tk.Frame(self, bg="#0b0d17", height=72)
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
        tab = self.input_tab
        left = self._card(tab); left.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=12)
        right = self._card(tab); right.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=12)

        self._label(left, "VIDEO INPUT", 11, True).pack(anchor="w", padx=18, pady=(18, 5))
        tk.Label(left, text="Tambahkan maksimal 60 video untuk batch rendering.", bg="#111426", fg="#858caf", font=("Segoe UI", 9)).pack(anchor="w", padx=18)
        row = tk.Frame(left, bg="#111426"); row.pack(fill="x", padx=18, pady=14)
        ttk.Button(row, text="+ TAMBAH VIDEO", command=self.add_videos).pack(side="left")
        ttk.Button(row, text="HAPUS SEMUA", command=self.clear_videos).pack(side="left", padx=8)
        self.video_count = tk.Label(row, text="0 / 60", bg="#111426", fg="#b8aaff", font=("Segoe UI", 10, "bold")); self.video_count.pack(side="right")
        self.video_list = tk.Listbox(left, bg="#0d1020", fg="#cfd2ee", selectbackground="#30285e", selectforeground="white", relief="flat", bd=0, font=("Segoe UI", 9))
        self.video_list.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        self._label(right, "AUDIO TRACKS", 11, True).pack(anchor="w", padx=18, pady=(18, 5))
        tk.Label(right, text="Audio dapat dipakai untuk setiap video secara berurutan atau acak.", bg="#111426", fg="#858caf", font=("Segoe UI", 9)).pack(anchor="w", padx=18)
        row2 = tk.Frame(right, bg="#111426"); row2.pack(fill="x", padx=18, pady=14)
        ttk.Button(row2, text="+ TAMBAH AUDIO", command=self.add_audio).pack(side="left")
        ttk.Button(row2, text="HAPUS SEMUA", command=self.clear_audio).pack(side="left", padx=8)
        self.audio_count_label = tk.Label(row2, text="0 lagu", bg="#111426", fg="#b8aaff", font=("Segoe UI", 10, "bold")); self.audio_count_label.pack(side="right")
        self.audio_list = tk.Listbox(right, bg="#0d1020", fg="#cfd2ee", selectbackground="#30285e", selectforeground="white", relief="flat", bd=0, font=("Segoe UI", 9))
        self.audio_list.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    def _build_render(self):
        tab = self.render_tab
        settings = self._card(tab); settings.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=12)
        logcard = self._card(tab); logcard.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=12)
        self._label(settings, "RENDER SETTINGS", 11, True).pack(anchor="w", padx=18, pady=(18, 15))
        grid = tk.Frame(settings, bg="#111426"); grid.pack(fill="x", padx=18)
        self.quality = tk.StringVar(value="Mengikuti Master")
        self.transition = tk.StringVar(value="Fade")
        self.output_dir = tk.StringVar(value=str(Path.cwd() / "output"))
        self.loop_count = tk.IntVar(value=1)
        self.variation_count = tk.IntVar(value=1)
        self.random_audio = tk.BooleanVar(value=True)
        self.normalize = tk.BooleanVar(value=False)
        self.make_txt = tk.BooleanVar(value=False)
        self._row(grid, 0, "Transition", ttk.Combobox(grid, textvariable=self.transition, values=["Fade", "Cut", "None"], state="readonly", width=25))
        self._row(grid, 1, "Quality", ttk.Combobox(grid, textvariable=self.quality, values=["Mengikuti Master", "Cepat", "Kualitas Tinggi"], state="readonly", width=25))
        self._row(grid, 2, "Variasi per video", ttk.Spinbox(grid, from_=1, to=100, textvariable=self.variation_count, width=27))
        self._row(grid, 3, "Loop video", ttk.Spinbox(grid, from_=1, to=100, textvariable=self.loop_count, width=27))
        self._label(settings, "BATCH", 10, True).pack(anchor="w", padx=18, pady=(22, 8))
        checks = tk.Frame(settings, bg="#111426"); checks.pack(fill="x", padx=18)
        ttk.Checkbutton(checks, text="Acak urutan lagu", variable=self.random_audio).pack(anchor="w", pady=4)
        ttk.Checkbutton(checks, text="Ratakkan volume lagu", variable=self.normalize).pack(anchor="w", pady=4)
        ttk.Checkbutton(checks, text="Buat file .txt", variable=self.make_txt).pack(anchor="w", pady=4)
        self._label(settings, "OUTPUT FOLDER", 10, True).pack(anchor="w", padx=18, pady=(22, 8))
        outrow = tk.Frame(settings, bg="#111426"); outrow.pack(fill="x", padx=18)
        tk.Entry(outrow, textvariable=self.output_dir, bg="#0d1020", fg="#cfd2ee", insertbackground="white", relief="flat", font=("Segoe UI", 9)).pack(side="left", fill="x", expand=True, ipady=8)
        ttk.Button(outrow, text="...", command=self.choose_output).pack(side="left", padx=(7, 0))
        self._label(logcard, "RENDER LOG", 11, True).pack(anchor="w", padx=18, pady=(18, 10))
        self.logbox = tk.Text(logcard, bg="#0a0d18", fg="#bfc5e8", insertbackground="white", relief="flat", bd=0, font=("Consolas", 9), wrap="word")
        self.logbox.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        for tag, color in [("READY", "#9b8cff"), ("INFO", "#8fa8ff"), ("RENDER", "#d4b3ff"), ("ERROR", "#ff7d96"), ("WARN", "#ffca7a"), ("FFMPEG", "#8ee6d4")]: self.logbox.tag_config(tag, foreground=color)

    def _row(self, parent, r, label, widget):
        tk.Label(parent, text=label, bg="#111426", fg="#858caf", font=("Segoe UI", 9)).grid(row=r, column=0, sticky="w", pady=6)
        widget.grid(row=r, column=1, sticky="e", padx=(35, 0), pady=6)
        parent.grid_columnconfigure(1, weight=1)

    def _build_live(self):
        frame = self._card(self.live_tab); frame.pack(fill="both", expand=True, padx=12, pady=12)
        self._label(frame, "LIVE STREAMING", 14, True).pack(anchor="w", padx=22, pady=(22, 8))
        tk.Label(frame, text="Panel streaming disiapkan untuk integrasi RTMP pada versi berikutnya.", bg="#111426", fg="#858caf", font=("Segoe UI", 10)).pack(anchor="w", padx=22)

    def add_videos(self):
        files = filedialog.askopenfilenames(title="Pilih video", filetypes=[("Video", "*.mp4 *.mov *.mkv *.avi *.webm"), ("Semua file", "*.*")])
        if not files: return
        remaining = MAX_VIDEOS - len(self.videos)
        if remaining <= 0:
            messagebox.showwarning("Batas 60 video", "Maksimal 60 video sudah tercapai."); return
        if len(files) > remaining:
            messagebox.showwarning("Batas 60 video", f"Hanya {remaining} video yang dapat ditambahkan.")
            files = files[:remaining]
        self.videos.extend(files); self._refresh_video_list()

    def _refresh_video_list(self):
        self.video_list.delete(0, "end")
        for i, f in enumerate(self.videos, 1): self.video_list.insert("end", f"{i:02d}. {Path(f).name}")
        self.video_count.config(text=f"{len(self.videos)} / {MAX_VIDEOS}")

    def clear_videos(self):
        self.videos.clear(); self._refresh_video_list()

    def add_audio(self):
        files = filedialog.askopenfilenames(title="Pilih audio", filetypes=[("Audio", "*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.opus"), ("Semua file", "*.*")])
        if not files: return
        self.audio_files.extend(files)
        self.audio_list.delete(0, "end")
        for i, f in enumerate(self.audio_files, 1): self.audio_list.insert("end", f"{i:02d}. {Path(f).name}")
        self.audio_count_label.config(text=f"{len(self.audio_files)} lagu")

    def clear_audio(self):
        self.audio_files.clear(); self.audio_list.delete(0, "end"); self.audio_count_label.config(text="0 lagu")

    def choose_output(self):
        d = filedialog.askdirectory(title="Pilih folder output")
        if d: self.output_dir.set(d)

    def log(self, tag, text):
        def write():
            self.logbox.insert("end", f"[{tag}] {text}\n", tag if tag in self.logbox.tag_names() else "")
            self.logbox.see("end")
        self.after(0, write)

    def clear_log(self): self.logbox.delete("1.0", "end")

    def set_status(self, text, color="#9b8cff"):
        self.after(0, lambda: self.status_badge.config(text="● " + text, fg=color))

    def open_output(self):
        d = Path(self.output_dir.get()); d.mkdir(parents=True, exist_ok=True)
        try: os.startfile(str(d))
        except Exception: subprocess.Popen(["explorer", str(d)])

    def stop_render(self):
        self.stop_flag.set(); self.log("WARN", "Permintaan STOP diterima. Proses FFmpeg aktif akan dihentikan."); self.set_status("STOPPING", "#ffca7a")

    def start_render(self):
        if self.render_thread and self.render_thread.is_alive(): messagebox.showinfo("Render berjalan", "Render sedang berjalan."); return
        if not self.ffmpeg: messagebox.showerror("FFmpeg tidak ditemukan", "Letakkan ffmpeg.exe di folder aplikasi, lalu jalankan kembali."); return
        if not self.videos: messagebox.showwarning("Video belum dipilih", "Tambahkan minimal 1 video."); return
        if not self.audio_files: messagebox.showwarning("Audio belum dipilih", "Tambahkan minimal 1 audio."); return
        try:
            variations = max(1, min(100, int(self.variation_count.get())))
            loops = max(1, min(100, int(self.loop_count.get())))
        except Exception:
            messagebox.showerror("Pengaturan salah", "Variasi dan loop harus berupa angka."); return
        out = Path(self.output_dir.get()).expanduser(); out.mkdir(parents=True, exist_ok=True)
        self.stop_flag.clear(); self.progress["value"] = 0
        self.render_thread = threading.Thread(target=self.render_worker, args=(variations, loops, out), daemon=True)
        self.render_thread.start()

    def render_worker(self, variations, loops, out):
        total = len(self.videos) * variations
        done = 0
        self.set_status("RENDERING", "#9b8cff")
        self.log("INFO", f"Mulai batch render: {len(self.videos)} video × {variations} variasi = {total} output.")
        for video_index, video in enumerate(self.videos, 1):
            if self.stop_flag.is_set(): break
            pool = list(self.audio_files)
            if self.random_audio.get(): random.shuffle(pool)
            for var in range(1, variations + 1):
                if self.stop_flag.is_set(): break
                audio = pool[(var - 1) % len(pool)]
                stem, astem = Path(video).stem, Path(audio).stem
                outfile = out / f"{stem}_V{var:02d}_{astem}.mp4"
                if outfile.exists():
                    n, base = 2, outfile
                    while outfile.exists(): outfile = base.with_name(f"{base.stem}_{n}{base.suffix}"); n += 1
                self.log("RENDER", f"Video {video_index}/{len(self.videos)} • variasi {var}/{variations}: {Path(video).name}")
                ok = self.render_one(video, audio, str(outfile), loops)
                done += 1
                self.after(0, lambda d=done, t=total, vi=video_index: self._progress(d, t, vi, len(self.videos)))
                if ok:
                    self.log("INFO", f"SELESAI: {outfile.name}")
                    if self.make_txt.get():
                        try: outfile.with_suffix(".txt").write_text(f"Video: {video}\nAudio: {audio}\nVariasi: {var}\n", encoding="utf-8")
                        except Exception as e: self.log("WARN", f"Gagal membuat TXT: {e}")
                else: self.log("ERROR", f"Render gagal: {Path(video).name} + {Path(audio).name}")
        if self.stop_flag.is_set():
            self.set_status("STOPPED", "#ffca7a"); self.log("WARN", f"Batch dihentikan. {done}/{total} tugas selesai.")
        else:
            self.set_status("READY", "#9b8cff"); self.log("READY", f"Batch selesai. {done}/{total} tugas diproses."); self.after(0, lambda: self.progress_text.config(text=f"Selesai • {done}/{total} output"))

    def _progress(self, done, total, vi, maxv):
        pct = done / total * 100 if total else 0
        self.progress["value"] = pct; self.progress_text.config(text=f"Video {vi}/{maxv} • {done}/{total} output • {pct:.0f}%")

    def render_one(self, video, audio, outfile, loops):
        if not Path(video).exists(): self.log("ERROR", f"Video tidak ditemukan: {video}"); return False
        if not Path(audio).exists(): self.log("ERROR", f"Audio tidak ditemukan: {audio}"); return False
        vf = "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p"
        q = self.quality.get()
        if q == "Cepat": vcodec = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23"]
        elif q == "Kualitas Tinggi": vcodec = ["-c:v", "libx264", "-preset", "slow", "-crf", "18"]
        else: vcodec = ["-c:v", "libx264", "-preset", "medium", "-crf", "20"]
        cmd = [self.ffmpeg, "-hide_banner", "-nostdin", "-y", "-stream_loop", str(max(0, loops - 1)), "-i", video, "-i", audio, "-map", "0:v:0", "-map", "1:a:0", "-vf", vf, *vcodec, "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", outfile]
        tail = []
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            while True:
                line = p.stdout.readline()
                if line:
                    line = line.rstrip(); tail.append(line)
                    if len(tail) > 30: tail.pop(0)
                    if "time=" in line: self.after(0, lambda s=line[-100:]: self.progress_text.config(text="Rendering... " + s))
                elif p.poll() is not None: break
                if self.stop_flag.is_set():
                    try: p.terminate(); p.wait(timeout=3)
                    except Exception:
                        try: p.kill()
                        except Exception: pass
                    return False
            if p.returncode != 0:
                self.log("ERROR", f"FFmpeg exit code: {p.returncode}")
                useful = [x for x in tail if any(k in x.lower() for k in ("error", "invalid", "failed", "unknown"))]
                for line in (useful[-8:] if useful else tail[-8:]): self.log("FFMPEG", line)
                return False
            return True
        except Exception as e:
            self.log("ERROR", f"Gagal menjalankan FFmpeg: {e}"); return False


if __name__ == "__main__":
    app = MasterRender()
    app.mainloop()
