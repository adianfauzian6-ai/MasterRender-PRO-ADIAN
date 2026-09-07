import os
import sys
import random
import shutil
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_NAME = "MasterRender PRO by AfroxSTD (ADIAN)"
MAX_VIDEOS = 60
MAX_SONGS = 20
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}

def app_root():
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent

def ffmpeg_path():
    p = app_root() / "ffmpeg.exe"
    return str(p) if p.is_file() else (shutil.which("ffmpeg") or "")

def run_hidden(cmd):
    startup = None
    flags = 0
    if os.name == "nt":
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        flags = subprocess.CREATE_NO_WINDOW
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, startupinfo=startup,
                            creationflags=flags, text=True, encoding="utf-8",
                            errors="replace", bufsize=1)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1400x850")
        self.minsize(1100, 700)
        self.configure(bg="#0b0b12")
        self.videos, self.songs = [], []
        self.proc = None
        self.stop_event = threading.Event()
        self.transition = tk.StringVar(value="Fade")
        self.engine = tk.StringVar(value="Otomatis Maksimal")
        self.quality = tk.StringVar(value="Mengikuti Master")
        self.output_size = tk.StringVar(value="Mengikuti Master")
        self.variations = tk.IntVar(value=1)
        self.song_count = tk.IntVar(value=9)
        self.album_repeat = tk.IntVar(value=1)
        self.shuffle = tk.BooleanVar(value=True)
        self.normalize = tk.BooleanVar(value=False)
        self.timestamp = tk.BooleanVar(value=False)
        self.make_variations = tk.BooleanVar(value=False)
        self.output_dir = tk.StringVar(value=str(Path.cwd() / "output"))
        self.output_name = tk.StringVar(value="masterrender")
        self.styles(); self.build_ui()
        self.log("READY", "Aplikasi siap digunakan.")
        self.log("INFO", f"FFmpeg: {ffmpeg_path()}" if ffmpeg_path() else "FFmpeg tidak ditemukan.")

    def styles(self):
        s = ttk.Style(self); s.theme_use("clam")
        s.configure(".", background="#12121c", foreground="#e9e7f5", fieldbackground="#181824", font=("Segoe UI", 9))
        s.configure("TNotebook", background="#0b0b12", borderwidth=0)
        s.configure("TNotebook.Tab", background="#151521", foreground="#aaa6c5", padding=(24,10), font=("Segoe UI",10,"bold"))
        s.map("TNotebook.Tab", background=[("selected","#282044")], foreground=[("selected","#c9b7ff")])
        s.configure("TButton", background="#191923", foreground="#e6e3f3", padding=(12,8), font=("Segoe UI",9,"bold"))
        s.map("TButton", background=[("active","#302852")])
        s.configure("TCombobox", fieldbackground="#181824", background="#181824", foreground="#e6e3f3", arrowcolor="#a98aff")
        s.configure("TSpinbox", fieldbackground="#181824", background="#181824", foreground="#e6e3f3", arrowcolor="#a98aff")
        s.configure("TProgressbar", troughcolor="#171720", background="#8b5cf6", borderwidth=0)

    def card(self, p): return tk.Frame(p, bg="#12121c", highlightbackground="#29293a", highlightthickness=1, bd=0)
    def lab(self, p, t, z=9, b=False, c="#eceaf5"):
        return tk.Label(p, text=t, bg=p.cget("bg"), fg=c, font=("Segoe UI",z,"bold" if b else "normal"))

    def build_ui(self):
        h=tk.Frame(self,bg="#0b0b12"); h.pack(fill="x",padx=24,pady=(18,8))
        tk.Label(h,text="MASTERRENDER PRO",bg="#0b0b12",fg="#f3f1fa",font=("Segoe UI",23,"bold")).pack(side="left")
        tk.Label(h,text="  by AfroxSTD  •  ADIAN",bg="#0b0b12",fg="#a78bfa",font=("Segoe UI",11,"bold")).pack(side="left",pady=(8,0))
        self.status=tk.Label(h,text="● READY",bg="#171722",fg="#a78bfa",padx=14,pady=7,font=("Segoe UI",9,"bold")); self.status.pack(side="right")
        body=tk.Frame(self,bg="#0b0b12"); body.pack(fill="both",expand=True,padx=24,pady=6)
        side=tk.Frame(body,bg="#11111b",width=205); side.pack(side="left",fill="y",padx=(0,14)); side.pack_propagate(False)
        tk.Label(side,text="WORKSPACE",bg="#11111b",fg="#77738e",font=("Segoe UI",9,"bold")).pack(anchor="w",padx=18,pady=(20,12))
        for name in ["Dashboard","Input Media","Render & Variasi","Live Streaming","Settings"]:
            a=name=="Render & Variasi"
            tk.Label(side,text=("◆  " if a else "   ")+name,bg="#282044" if a else "#11111b",fg="#c9b7ff" if a else "#9b98b2",anchor="w",padx=16,pady=11,font=("Segoe UI",10,"bold" if a else "normal")).pack(fill="x",padx=9,pady=2)
        main=tk.Frame(body,bg="#0b0b12"); main.pack(side="left",fill="both",expand=True)
        self.nb=ttk.Notebook(main); self.nb.pack(fill="both",expand=True)
        self.input_tab=tk.Frame(self.nb,bg="#0b0b12"); self.render_tab=tk.Frame(self.nb,bg="#0b0b12"); self.live_tab=tk.Frame(self.nb,bg="#0b0b12")
        self.nb.add(self.input_tab,text="  Input  "); self.nb.add(self.render_tab,text="  Render & Variasi  "); self.nb.add(self.live_tab,text="  Live Streaming  ")
        self.input_ui(); self.render_ui(); self.live_ui()
        btm=tk.Frame(self,bg="#0b0b12"); btm.pack(fill="x",padx=24,pady=(4,18))
        self.pb=ttk.Progressbar(btm,maximum=100,mode="determinate"); self.pb.pack(fill="x",pady=(0,8))
        self.pt=tk.Label(btm,text="Siap merender hingga 60 video",bg="#0b0b12",fg="#858198",font=("Segoe UI",9)); self.pt.pack(side="left")
        acts=tk.Frame(btm,bg="#0b0b12"); acts.pack(side="right")
        ttk.Button(acts,text="OPEN OUTPUT",command=self.open_output).pack(side="left",padx=4); ttk.Button(acts,text="BERSIHKAN LOG",command=self.clear_log).pack(side="left",padx=4); ttk.Button(acts,text="STOP",command=self.stop).pack(side="left",padx=4)
        tk.Button(acts,text="START RENDER",command=self.start,bg="#7c5cff",fg="white",activebackground="#967dff",relief="flat",bd=0,font=("Segoe UI",10,"bold"),padx=25,pady=11).pack(side="left",padx=(8,0))

    def input_ui(self):
        l=self.card(self.input_tab); l.pack(side="left",fill="both",expand=True,padx=(10,7),pady=12); r=self.card(self.input_tab); r.pack(side="left",fill="both",expand=True,padx=(7,10),pady=12)
        self.lab(l,"VIDEO MASTER",11,True).pack(anchor="w",padx=18,pady=(18,4)); self.lab(l,"Tambahkan sampai 60 video untuk diproses dalam satu batch.",9,False,"#858198").pack(anchor="w",padx=18)
        q=tk.Frame(l,bg="#12121c"); q.pack(fill="x",padx=18,pady=13); ttk.Button(q,text="+ TAMBAH VIDEO",command=self.add_videos).pack(side="left"); ttk.Button(q,text="HAPUS TERPILIH",command=self.remove_video).pack(side="left",padx=6); ttk.Button(q,text="HAPUS SEMUA",command=self.clear_videos).pack(side="left"); self.vc=tk.Label(q,text="0 / 60",bg="#12121c",fg="#b9a6ff",font=("Segoe UI",10,"bold")); self.vc.pack(side="right")
        self.vlist=tk.Listbox(l,bg="#0d0d15",fg="#d5d1e6",selectbackground="#302650",selectforeground="white",relief="flat",bd=0,font=("Segoe UI",9)); self.vlist.pack(fill="both",expand=True,padx=18,pady=(0,18))
        self.lab(r,"LAGU / AUDIO",11,True).pack(anchor="w",padx=18,pady=(18,4)); self.lab(r,"Maksimal 20 lagu. Setiap video mendapatkan playlist sendiri.",9,False,"#858198").pack(anchor="w",padx=18)
        q=tk.Frame(r,bg="#12121c"); q.pack(fill="x",padx=18,pady=13); ttk.Button(q,text="+ TAMBAH LAGU",command=self.add_audio).pack(side="left"); ttk.Button(q,text="SCAN FOLDER",command=self.scan_audio).pack(side="left",padx=6); ttk.Button(q,text="HAPUS SEMUA",command=self.clear_audio).pack(side="left"); self.ac=tk.Label(q,text="0 / 20",bg="#12121c",fg="#b9a6ff",font=("Segoe UI",10,"bold")); self.ac.pack(side="right")
        self.alist=tk.Listbox(r,bg="#0d0d15",fg="#d5d1e6",selectbackground="#302650",selectforeground="white",relief="flat",bd=0,font=("Segoe UI",9)); self.alist.pack(fill="both",expand=True,padx=18,pady=(0,18))
        o=self.card(self.input_tab); o.pack(fill="x",padx=10,pady=(0,12)); row=tk.Frame(o,bg="#12121c"); row.pack(fill="x",padx=18,pady=10); self.lab(row,"Folder Output",9,True).pack(side="left"); tk.Entry(row,textvariable=self.output_dir,bg="#0d0d15",fg="#d5d1e6",insertbackground="white",relief="flat").pack(side="left",fill="x",expand=True,padx=15,ipady=7); ttk.Button(row,text="PILIH",command=self.choose_output).pack(side="right")
        row=tk.Frame(o,bg="#12121c"); row.pack(fill="x",padx=18,pady=(0,12)); self.lab(row,"Nama Output",9,True).pack(side="left"); tk.Entry(row,textvariable=self.output_name,bg="#0d0d15",fg="#d5d1e6",insertbackground="white",relief="flat").pack(side="left",fill="x",expand=True,padx=15,ipady=7)

    def render_ui(self):
        l=self.card(self.render_tab); l.pack(side="left",fill="both",expand=True,padx=(10,7),pady=12); r=self.card(self.render_tab); r.pack(side="left",fill="both",expand=True,padx=(7,10),pady=12)
        self.lab(l,"RENDER SETTINGS",11,True).pack(anchor="w",padx=18,pady=(18,12)); g=tk.Frame(l,bg="#12121c"); g.pack(fill="x",padx=18)
        self.option(g,0,"Transisi Loop",self.transition,["Memudar (Fade)","Potong (Cut)"]); self.option(g,1,"Mesin Render",self.engine,["Otomatis Maksimal","1 Proses"]); self.option(g,2,"Kualitas",self.quality,["Mengikuti Master","Cepat","Kualitas Tinggi"]); self.option(g,3,"Ukuran Output",self.output_size,["Mengikuti Master","1080p","720p"])
        c=tk.Frame(l,bg="#12121c"); c.pack(fill="x",padx=18,pady=10); ttk.Checkbutton(c,text="Acak urutan lagu",variable=self.shuffle).grid(row=0,column=0,sticky="w",padx=(0,30),pady=5); ttk.Checkbutton(c,text="Ratakan volume lagu",variable=self.normalize).grid(row=0,column=1,sticky="w",pady=5); ttk.Checkbutton(c,text="Buat timestamp .txt",variable=self.timestamp).grid(row=1,column=0,sticky="w",padx=(0,30),pady=5); ttk.Checkbutton(c,text="Buat beberapa variasi",variable=self.make_variations).grid(row=1,column=1,sticky="w",pady=5)
        self.spin(g,4,"Jumlah variasi",self.variations,1,100); self.spin(g,5,"Total lagu yang akan diacak",self.song_count,1,20); self.spin(g,6,"Ulang album",self.album_repeat,1,20)
        self.lab(l,"INFO",10,True).pack(anchor="w",padx=18,pady=(18,5)); tk.Label(l,text="Playlist dibuat per video. Jika tersedia 20 lagu dan dipilih 9, sistem mengambil 9 lagu secara acak. Video di-loop sampai seluruh playlist selesai.",bg="#12121c",fg="#858198",justify="left",wraplength=560,font=("Segoe UI",9)).pack(anchor="w",padx=18,pady=(0,18))
        self.lab(r,"RENDER LOG",11,True).pack(anchor="w",padx=18,pady=(18,10)); self.logbox=tk.Text(r,bg="#08090f",fg="#c9c7d8",insertbackground="white",relief="flat",bd=0,font=("Consolas",9),wrap="word"); self.logbox.pack(fill="both",expand=True,padx=18,pady=(0,18))

    def option(self,p,row,text,var,vals):
        tk.Label(p,text=text,bg="#12121c",fg="#858198",font=("Segoe UI",9)).grid(row=row,column=0,sticky="w",pady=6); ttk.Combobox(p,textvariable=var,values=vals,state="readonly",width=25).grid(row=row,column=1,sticky="e",pady=6); p.grid_columnconfigure(1,weight=1)
    def spin(self,p,row,text,var,lo,hi):
        tk.Label(p,text=text,bg="#12121c",fg="#eceaf5",font=("Segoe UI",9,"bold" if "Total" in text else "normal")).grid(row=row,column=0,sticky="w",pady=6); ttk.Spinbox(p,from_=lo,to=hi,textvariable=var,width=25).grid(row=row,column=1,sticky="e",pady=6)
        if "Total lagu" in text: tk.Label(p,text="(maks. 20)",bg="#12121c",fg="#858198",font=("Segoe UI",8)).grid(row=row,column=2,sticky="w",padx=8)
    def live_ui(self):
        p=self.card(self.live_tab); p.pack(fill="both",expand=True,padx=10,pady=12); self.lab(p,"LIVE STREAMING",13,True).pack(anchor="w",padx=22,pady=(22,6)); self.lab(p,"Panel RTMP/Live Streaming disiapkan untuk pengembangan berikutnya.",9,False,"#858198").pack(anchor="w",padx=22)

    def add_videos(self):
        fs=filedialog.askopenfilenames(title="Pilih video",filetypes=[("Video","*.mp4 *.mov *.mkv *.avi *.webm *.m4v"),("Semua file","*.*")]); self.videos.extend([x for x in fs if x not in self.videos][:MAX_VIDEOS-len(self.videos)]); self.refresh_v()
    def remove_video(self):
        for i in reversed(self.vlist.curselection()): self.videos.pop(i)
        self.refresh_v()
    def clear_videos(self): self.videos.clear(); self.refresh_v()
    def refresh_v(self):
        self.vlist.delete(0,"end"); [self.vlist.insert("end",f"{i:02d}. {Path(x).name}") for i,x in enumerate(self.videos,1)]; self.vc.config(text=f"{len(self.videos)} / {MAX_VIDEOS}")
    def add_audio(self):
        fs=filedialog.askopenfilenames(title="Pilih lagu",filetypes=[("Audio","*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.opus"),("Semua file","*.*")]); self.songs.extend([x for x in fs if x not in self.songs][:MAX_SONGS-len(self.songs)]); self.refresh_a()
    def scan_audio(self):
        d=filedialog.askdirectory(title="Pilih folder lagu")
        if not d:return
        found=[str(p) for p in Path(d).iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXT]; found.sort(key=lambda x:Path(x).name.lower()); self.songs.extend([x for x in found if x not in self.songs][:MAX_SONGS-len(self.songs)]); self.refresh_a()
    def clear_audio(self): self.songs.clear(); self.refresh_a()
    def refresh_a(self):
        self.alist.delete(0,"end"); [self.alist.insert("end",f"{i:02d}. {Path(x).name}") for i,x in enumerate(self.songs,1)]; self.ac.config(text=f"{len(self.songs)} / {MAX_SONGS}")
    def choose_output(self):
        d=filedialog.askdirectory(title="Pilih folder output")
        if d:self.output_dir.set(d)
    def open_output(self):
        d=Path(self.output_dir.get()); d.mkdir(parents=True,exist_ok=True); os.startfile(str(d)) if os.name=="nt" else subprocess.Popen(["xdg-open",str(d)])
    def clear_log(self): self.logbox.delete("1.0","end")
    def log(self,tag,msg): self.after(0,lambda:self._log(tag,msg))
    def _log(self,tag,msg): self.logbox.insert("end",f"[{tag}] {msg}\n"); self.logbox.see("end")

    def start(self):
        if getattr(self,"render_thread",None) and self.render_thread.is_alive(): return
        if not self.videos:return messagebox.showwarning(APP_NAME,"Tambahkan minimal 1 video.")
        if not self.songs:return messagebox.showwarning(APP_NAME,"Tambahkan minimal 1 lagu.")
        try:n=max(1,min(20,int(self.song_count.get())))
        except Exception:n=1
        if n>len(self.songs):return messagebox.showwarning(APP_NAME,f"Total lagu diminta {n}, tetapi lagu yang tersedia hanya {len(self.songs)}.")
        if not ffmpeg_path():return messagebox.showerror(APP_NAME,"FFmpeg tidak ditemukan. Pastikan ffmpeg.exe ikut dalam EXE.")
        Path(self.output_dir.get()).mkdir(parents=True,exist_ok=True); self.stop_event.clear(); self.pb["value"]=0; self.status.config(text="● RENDERING",fg="#a78bfa"); self.pt.config(text=f"Mulai 0/{len(self.videos)}"); self.log("START",f"{len(self.videos)} video • {n} lagu per playlist")
        self.render_thread=threading.Thread(target=self.worker,args=(n,),daemon=True); self.render_thread.start()
    def stop(self):
        self.stop_event.set(); p=self.proc
        if p and p.poll() is None:
            try:p.terminate()
            except Exception:pass
        self.log("WARN","STOP diminta. Proses aktif dihentikan dan output parsial dihapus.")

    def worker(self,n):
        total=len(self.videos); done=0
        try:
            for i,video in enumerate(list(self.videos),1):
                if self.stop_event.is_set():break
                playlist=list(self.songs)
                if self.shuffle.get():random.shuffle(playlist)
                else:playlist.sort(key=lambda x:Path(x).name.lower())
                playlist=playlist[:n]
                self.log("VIDEO",f"{i}/{total} • {Path(video).name}"); self.log("PLAYLIST"," → ".join(Path(x).name for x in playlist))
                count=max(1,min(100,int(self.variations.get()))) if self.make_variations.get() else 1
                for v in range(1,count+1):
                    if self.stop_event.is_set():break
                    pl=list(playlist)
                    if v>1 and self.shuffle.get():random.shuffle(pl)
                    out=self.render_video(video,pl,i,v,count)
                    if out:done+=1; self.log("DONE",Path(out).name)
                pct=i/total*100; self.after(0,lambda p=pct,j=i:(self.pb.configure(value=p),self.pt.config(text=f"Video {j}/{total} selesai")))
            if self.stop_event.is_set():self.log("READY","Render dihentikan."); self.after(0,lambda:self.status.config(text="● STOPPED",fg="#f59e9e"))
            else:self.log("READY",f"Semua render selesai. File berhasil: {done}"); self.after(0,lambda:self.status.config(text="● READY",fg="#a78bfa")); self.after(0,lambda:self.pt.config(text=f"Selesai • {done} file output"))
        except Exception as e:self.log("ERROR",f"Worker: {e}"); self.after(0,lambda:self.status.config(text="● ERROR",fg="#f87171"))

    def render_video(self,video,playlist,index,variation,total_variations):
        ff=ffmpeg_path(); base=Path(video).stem; suffix=f"_v{variation}" if total_variations>1 else ""; out=Path(self.output_dir.get())/self.unique_name(f"{self.output_name.get()}_{base}{suffix}",".mp4"); temp=Path(self.output_dir.get())/f".mr_playlist_{os.getpid()}_{threading.get_ident()}_{index}_{variation}.m4a"
        try:
            self.log("PROCESS",f"Menggabungkan {len(playlist)} lagu menjadi satu playlist...")
            inputs=[]; filters=[]
            for i,song in enumerate(playlist):
                inputs += ["-i",song]
                af=f"[{i}:a]aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[a{i}]"
                if self.normalize.get(): af=f"[{i}:a]aresample=48000,loudnorm=I=-16:TP=-1.5:LRA=11,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[a{i}]"
                filters.append(af)
            labels="".join(f"[a{i}]" for i in range(len(playlist))); filters.append(f"{labels}concat=n={len(playlist)}:v=0:a=1[playlist]")
            p=run_hidden([ff,"-hide_banner","-loglevel","warning","-nostdin","-y"]+inputs+["-filter_complex",";".join(filters),"-map","[playlist]","-c:a","aac","-b:a","192k","-ar","48000","-ac","2",str(temp)]); self.proc=p; lines=[]
            for line in p.stdout:
                line=line.rstrip()
                if line:
                    lines.append(line)
                    if any(k in line.lower() for k in ("error","invalid","failed","unable")):self.log("FFMPEG",line)
            rc=p.wait(); self.proc=None
            if self.stop_event.is_set():return None
            if rc!=0 or not temp.exists() or temp.stat().st_size<1024:raise RuntimeError("Gagal menggabungkan playlist audio. "+" | ".join(lines[-5:]))
            q=self.quality.get(); codec=["-c:v","libx264","-preset","veryfast","-crf","23"] if q=="Cepat" else (["-c:v","libx264","-preset","slow","-crf","18"] if q=="Kualitas Tinggi" else ["-c:v","libx264","-preset","medium","-crf","20"])
            vf="scale=-2:1080,format=yuv420p" if self.output_size.get()=="1080p" else ("scale=-2:720,format=yuv420p" if self.output_size.get()=="720p" else "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p")
            self.log("PROCESS","Video di-loop sampai seluruh playlist selesai...")
            p=run_hidden([ff,"-hide_banner","-loglevel","warning","-nostdin","-y","-stream_loop","-1","-i",str(video),"-i",str(temp),"-map","0:v:0","-map","1:a:0","-vf",vf]+codec+["-c:a","aac","-b:a","192k","-ar","48000","-ac","2","-shortest","-movflags","+faststart",str(out)]); self.proc=p; lines=[]
            for line in p.stdout:
                line=line.rstrip()
                if line:
                    lines.append(line)
                    if any(k in line.lower() for k in ("error","invalid","failed","unable")):self.log("FFMPEG",line)
            rc=p.wait(); self.proc=None
            if self.stop_event.is_set():out.unlink(missing_ok=True);return None
            if rc!=0 or not out.exists() or out.stat().st_size<1024:out.unlink(missing_ok=True);raise RuntimeError("Render gagal. "+" | ".join(lines[-5:]))
            if self.timestamp.get():out.with_suffix(".txt").write_text("MasterRender PRO by AfroxSTD (ADIAN)\nVideo: "+Path(video).name+"\nPlaylist:\n"+"\n".join(f"{i}. {Path(s).name}" for i,s in enumerate(playlist,1)),encoding="utf-8")
            return str(out)
        finally:
            self.proc=None
            try:temp.unlink(missing_ok=True)
            except Exception:pass

    def unique_name(self,stem,ext):
        base=Path(stem).name; p=Path(self.output_dir.get())/(base+ext)
        if not p.exists():return p.name
        i=2
        while (Path(self.output_dir.get())/f"{base}_{i}{ext}").exists():i+=1
        return f"{base}_{i}{ext}"

if __name__=="__main__":App().mainloop()
