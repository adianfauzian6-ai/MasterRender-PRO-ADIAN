import os, sys, random, shutil, subprocess, threading, re, time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_NAME = 'MasterRender PRO by AfroxSTD (ADIAN)'
MAX_VIDEOS, MAX_SONGS = 60, 20
AUDIO_EXT = {'.mp3','.wav','.m4a','.aac','.flac','.ogg','.opus'}
VIDEO_EXT = {'.mp4','.mov','.mkv','.avi','.webm','.m4v'}
BG='#0b0b12'; PANEL='#12121c'; INPUT='#0d0d15'; PURPLE='#8b5cf6'; TEXT='#eceaf5'; MUTED='#858198'

def root_dir():
    return Path(getattr(sys,'_MEIPASS',Path(sys.executable).parent)) if getattr(sys,'frozen',False) else Path(__file__).resolve().parent

def ffmpeg_path():
    p=root_dir()/'ffmpeg.exe'
    return str(p) if p.exists() else (shutil.which('ffmpeg') or '')

def hidden_kwargs():
    if os.name!='nt': return {}
    si=subprocess.STARTUPINFO(); si.dwFlags |= subprocess.STARTF_USESHOWWINDOW; si.wShowWindow=0
    return {'startupinfo':si,'creationflags':subprocess.CREATE_NO_WINDOW}

def run_quiet(cmd):
    try: return subprocess.check_output(cmd,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',**hidden_kwargs())
    except Exception: return ''

def safe_name(s): return re.sub(r'[<>:"/\\|?*]','_',s).strip() or 'output'

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title(APP_NAME); self.geometry('1400x850'); self.minsize(1100,700); self.configure(bg=BG)
        self.videos=[]; self.songs=[]; self.proc=None; self.stop_flag=threading.Event(); self.render_thread=None
        self.transition=tk.StringVar(value='Memudar (Fade)'); self.engine=tk.StringVar(value='Otomatis Maksimal'); self.quality=tk.StringVar(value='Mengikuti Master'); self.output_size=tk.StringVar(value='Mengikuti Master')
        self.variations=tk.IntVar(value=1); self.song_count=tk.IntVar(value=9); self.album_repeat=tk.IntVar(value=1)
        self.shuffle=tk.BooleanVar(value=True); self.normalize=tk.BooleanVar(value=False); self.timestamp=tk.BooleanVar(value=False); self.make_variations=tk.BooleanVar(value=False)
        self.output_dir=tk.StringVar(value=str(Path.cwd()/'output')); self.output_name=tk.StringVar(value='masterrender')
        self.setup_style(); self.build_ui(); self.log('READY','Aplikasi siap digunakan.'); self.log('INFO',f'FFmpeg: {ffmpeg_path() or "tidak ditemukan"}')

    def setup_style(self):
        s=ttk.Style(self); s.theme_use('clam'); s.configure('.',background=PANEL,foreground=TEXT,fieldbackground='#181824',font=('Segoe UI',9)); s.configure('TNotebook',background=BG,borderwidth=0); s.configure('TNotebook.Tab',background='#151521',foreground='#aaa6c5',padding=(24,10),font=('Segoe UI',10,'bold')); s.map('TNotebook.Tab',background=[('selected','#282044')],foreground=[('selected','#c9b7ff')]); s.configure('TButton',background='#191923',foreground=TEXT,padding=(12,8),font=('Segoe UI',9,'bold')); s.map('TButton',background=[('active','#302852')]); s.configure('TCombobox',fieldbackground='#181824',background='#181824',foreground=TEXT,arrowcolor='#a98aff'); s.configure('TSpinbox',fieldbackground='#181824',background='#181824',foreground=TEXT,arrowcolor='#a98aff'); s.configure('TProgressbar',troughcolor='#171720',background=PURPLE,borderwidth=0)
    def card(self,p): return tk.Frame(p,bg=PANEL,highlightbackground='#29293a',highlightthickness=1,bd=0)
    def label(self,p,t,size=9,bold=False,color=TEXT,**kw): return tk.Label(p,text=t,bg=p.cget('bg'),fg=color,font=('Segoe UI',size,'bold' if bold else 'normal'),**kw)

    def build_ui(self):
        h=tk.Frame(self,bg=BG); h.pack(fill='x',padx=24,pady=(18,8)); tk.Label(h,text='MASTERRENDER PRO',bg=BG,fg='#f3f1fa',font=('Segoe UI',23,'bold')).pack(side='left'); tk.Label(h,text='  by AfroxSTD  •  ADIAN',bg=BG,fg='#a78bfa',font=('Segoe UI',11,'bold')).pack(side='left',pady=(8,0)); self.status=tk.Label(h,text='● READY',bg='#171722',fg='#a78bfa',padx=14,pady=7,font=('Segoe UI',9,'bold')); self.status.pack(side='right')
        body=tk.Frame(self,bg=BG); body.pack(fill='both',expand=True,padx=24,pady=6); side=tk.Frame(body,bg='#11111b',width=205); side.pack(side='left',fill='y',padx=(0,14)); side.pack_propagate(False); self.label(side,'WORKSPACE',9,True,'#77738e').pack(anchor='w',padx=18,pady=(20,12))
        for name in ['Dashboard','Input Media','Render & Variasi','Live Streaming','Settings']:
            active=name=='Render & Variasi'; tk.Label(side,text=('◆  ' if active else '   ')+name,bg='#282044' if active else '#11111b',fg='#c9b7ff' if active else '#9b98b2',anchor='w',padx=16,pady=11,font=('Segoe UI',10,'bold' if active else 'normal')).pack(fill='x',padx=9,pady=2)
        main=tk.Frame(body,bg=BG); main.pack(side='left',fill='both',expand=True); self.nb=ttk.Notebook(main); self.nb.pack(fill='both',expand=True); self.input_tab=tk.Frame(self.nb,bg=BG); self.render_tab=tk.Frame(self.nb,bg=BG); self.live_tab=tk.Frame(self.nb,bg=BG); self.nb.add(self.input_tab,text='  Input  '); self.nb.add(self.render_tab,text='  Render & Variasi  '); self.nb.add(self.live_tab,text='  Live Streaming  '); self.input_ui(); self.render_ui(); self.live_ui()
        b=tk.Frame(self,bg=BG); b.pack(fill='x',padx=24,pady=(4,18)); self.progress=ttk.Progressbar(b,maximum=100); self.progress.pack(fill='x',pady=(0,8)); self.progress_text=tk.Label(b,text='Siap merender hingga 60 video',bg=BG,fg=MUTED,font=('Segoe UI',9)); self.progress_text.pack(side='left'); a=tk.Frame(b,bg=BG); a.pack(side='right'); ttk.Button(a,text='OPEN OUTPUT',command=self.open_output).pack(side='left',padx=4); ttk.Button(a,text='BERSIHKAN LOG',command=self.clear_log).pack(side='left',padx=4); ttk.Button(a,text='STOP',command=self.stop_render).pack(side='left',padx=4); tk.Button(a,text='START RENDER',command=self.start_render,bg=PURPLE,fg='white',activebackground='#967dff',relief='flat',bd=0,font=('Segoe UI',10,'bold'),padx=25,pady=11).pack(side='left',padx=(8,0))

    def input_ui(self):
        l=self.card(self.input_tab); l.pack(side='left',fill='both',expand=True,padx=(10,7),pady=12); r=self.card(self.input_tab); r.pack(side='left',fill='both',expand=True,padx=(7,10),pady=12); self.label(l,'VIDEO MASTER',11,True).pack(anchor='w',padx=18,pady=(18,4)); self.label(l,'Tambahkan sampai 60 video untuk diproses dalam satu batch.',9,False,MUTED).pack(anchor='w',padx=18); q=tk.Frame(l,bg=PANEL); q.pack(fill='x',padx=18,pady=13); ttk.Button(q,text='+ TAMBAH VIDEO',command=self.add_videos).pack(side='left'); ttk.Button(q,text='HAPUS TERPILIH',command=self.remove_video).pack(side='left',padx=6); ttk.Button(q,text='HAPUS SEMUA',command=self.clear_videos).pack(side='left'); self.video_count=tk.Label(q,text='0 / 60',bg=PANEL,fg='#b9a6ff',font=('Segoe UI',10,'bold')); self.video_count.pack(side='right'); self.video_list=tk.Listbox(l,bg=INPUT,fg='#d5d1e6',selectbackground='#302650',selectforeground='white',relief='flat',bd=0,font=('Segoe UI',9)); self.video_list.pack(fill='both',expand=True,padx=18,pady=(0,18))
        self.label(r,'LAGU / AUDIO',11,True).pack(anchor='w',padx=18,pady=(18,4)); self.label(r,'Maksimal 20 lagu. Setiap video mendapatkan playlist sendiri.',9,False,MUTED).pack(anchor='w',padx=18); q=tk.Frame(r,bg=PANEL); q.pack(fill='x',padx=18,pady=13); ttk.Button(q,text='+ TAMBAH LAGU',command=self.add_audio).pack(side='left'); ttk.Button(q,text='SCAN FOLDER',command=self.scan_audio).pack(side='left',padx=6); ttk.Button(q,text='HAPUS SEMUA',command=self.clear_audio).pack(side='left'); self.audio_count_label=tk.Label(q,text='0 / 20',bg=PANEL,fg='#b9a6ff',font=('Segoe UI',10,'bold')); self.audio_count_label.pack(side='right'); self.audio_list=tk.Listbox(r,bg=INPUT,fg='#d5d1e6',selectbackground='#302650',selectforeground='white',relief='flat',bd=0,font=('Segoe UI',9)); self.audio_list.pack(fill='both',expand=True,padx=18,pady=(0,18))
        o=self.card(self.input_tab); o.pack(fill='x',padx=10,pady=(0,12)); row=tk.Frame(o,bg=PANEL); row.pack(fill='x',padx=18,pady=10); self.label(row,'Folder Output',9,True).pack(side='left'); tk.Entry(row,textvariable=self.output_dir,bg=INPUT,fg='#d5d1e6',insertbackground='white',relief='flat').pack(side='left',fill='x',expand=True,padx=15,ipady=7); ttk.Button(row,text='PILIH',command=self.choose_output).pack(side='right'); row=tk.Frame(o,bg=PANEL); row.pack(fill='x',padx=18,pady=(0,12)); self.label(row,'Nama Output',9,True).pack(side='left'); tk.Entry(row,textvariable=self.output_name,bg=INPUT,fg='#d5d1e6',insertbackground='white',relief='flat').pack(side='left',fill='x',expand=True,padx=15,ipady=7)

    def render_ui(self):
        l=self.card(self.render_tab); l.pack(side='left',fill='both',expand=True,padx=(10,7),pady=12); r=self.card(self.render_tab); r.pack(side='left',fill='both',expand=True,padx=(7,10),pady=12); self.label(l,'RENDER SETTINGS',11,True).pack(anchor='w',padx=18,pady=(18,12)); g=tk.Frame(l,bg=PANEL); g.pack(fill='x',padx=18)
        self.option(g,0,'Transisi Loop',self.transition,['Memudar (Fade)','Potong (Cut)']); self.option(g,1,'Mesin Render',self.engine,['Otomatis Maksimal','1 Proses']); self.option(g,2,'Kualitas',self.quality,['Mengikuti Master','Cepat','Kualitas Tinggi']); self.option(g,3,'Ukuran Output',self.output_size,['Mengikuti Master','1080p','720p']); self.spin(g,4,'Jumlah variasi',self.variations,1,100); self.spin(g,5,'Total lagu yang akan diacak',self.song_count,1,20,True); self.spin(g,6,'Ulang album',self.album_repeat,1,20)
        c=tk.Frame(l,bg=PANEL); c.pack(fill='x',padx=18,pady=10); ttk.Checkbutton(c,text='Acak urutan lagu',variable=self.shuffle).grid(row=0,column=0,sticky='w',padx=(0,30),pady=5); ttk.Checkbutton(c,text='Ratakan volume lagu',variable=self.normalize).grid(row=0,column=1,sticky='w',pady=5); ttk.Checkbutton(c,text='Buat timestamp .txt',variable=self.timestamp).grid(row=1,column=0,sticky='w',padx=(0,30),pady=5); ttk.Checkbutton(c,text='Buat beberapa variasi',variable=self.make_variations).grid(row=1,column=1,sticky='w',pady=5); self.label(l,'INFO',10,True).pack(anchor='w',padx=18,pady=(18,5)); self.label(l,'Playlist dibuat per video. Setiap video mengacak lagu sendiri, lalu seluruh playlist diputar berurutan. Video di-loop sampai playlist selesai.',9,False,MUTED,justify='left',wraplength=560).pack(anchor='w',padx=18,pady=(0,18)); self.label(r,'RENDER LOG',11,True).pack(anchor='w',padx=18,pady=(18,10)); self.logbox=tk.Text(r,bg='#08090f',fg='#c9c7d8',insertbackground='white',relief='flat',bd=0,font=('Consolas',9),wrap='word'); self.logbox.pack(fill='both',expand=True,padx=18,pady=(0,18))
    def option(self,p,row,text,var,vals): tk.Label(p,text=text,bg=PANEL,fg=MUTED,font=('Segoe UI',9)).grid(row=row,column=0,sticky='w',pady=6); ttk.Combobox(p,textvariable=var,values=vals,state='readonly',width=25).grid(row=row,column=1,sticky='e',pady=6); p.grid_columnconfigure(1,weight=1)
    def spin(self,p,row,text,var,lo,hi,maxmark=False): tk.Label(p,text=text,bg=PANEL,fg=TEXT,font=('Segoe UI',9,'bold' if maxmark else 'normal')).grid(row=row,column=0,sticky='w',pady=6); ttk.Spinbox(p,from_=lo,to=hi,textvariable=var,width=25).grid(row=row,column=1,sticky='e',pady=6); (tk.Label(p,text='(maks. 20)',bg=PANEL,fg=MUTED,font=('Segoe UI',8)).grid(row=row,column=2,sticky='w',padx=8) if maxmark else None)
    def live_ui(self): p=self.card(self.live_tab); p.pack(fill='both',expand=True,padx=10,pady=12); self.label(p,'LIVE STREAMING',13,True).pack(anchor='w',padx=22,pady=(22,6)); self.label(p,'Panel RTMP/Live Streaming siap dikembangkan tanpa mengganggu mesin render.',9,False,MUTED).pack(anchor='w',padx=22)
    def add_videos(self):
        fs=filedialog.askopenfilenames(title='Pilih video',filetypes=[('Video','*.mp4 *.mov *.mkv *.avi *.webm *.m4v'),('Semua file','*.*')]); room=MAX_VIDEOS-len(self.videos); fs=fs[:max(0,room)]
        if fs: self.videos.extend(fs); self.refresh_videos()
    def remove_video(self):
        for i in reversed(self.video_list.curselection()): self.videos.pop(i)
        self.refresh_videos()
    def clear_videos(self): self.videos.clear(); self.refresh_videos()
    def refresh_videos(self): self.video_list.delete(0,'end'); [self.video_list.insert('end',f'{i:02d}. {Path(x).name}') for i,x in enumerate(self.videos,1)]; self.video_count.config(text=f'{len(self.videos)} / {MAX_VIDEOS}')
    def add_audio(self):
        fs=filedialog.askopenfilenames(title='Pilih audio',filetypes=[('Audio','*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.opus'),('Semua file','*.*')]); room=MAX_SONGS-len(self.songs); fs=fs[:max(0,room)]
        if fs: self.songs.extend(fs); self.refresh_audio()
    def scan_audio(self):
        d=filedialog.askdirectory(title='Pilih folder lagu');
        if not d: return
        fs=sorted([str(p) for p in Path(d).iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXT]); room=MAX_SONGS-len(self.songs); self.songs.extend(fs[:max(0,room)]); self.refresh_audio()
    def clear_audio(self): self.songs.clear(); self.refresh_audio()
    def refresh_audio(self): self.audio_list.delete(0,'end'); [self.audio_list.insert('end',f'{i:02d}. {Path(x).name}') for i,x in enumerate(self.songs,1)]; self.audio_count_label.config(text=f'{len(self.songs)} / {MAX_SONGS}')
    def choose_output(self):
        d=filedialog.askdirectory(title='Pilih folder output');
        if d: self.output_dir.set(d)
    def log(self,tag,msg):
        if not hasattr(self,'logbox'): return
        self.after(0,lambda:self._log(tag,msg))
    def _log(self,tag,msg): self.logbox.insert('end',f'[{tag}] {msg}\n'); self.logbox.see('end')
    def clear_log(self): self.logbox.delete('1.0','end')
    def status_set(self,text,color='#a78bfa'): self.after(0,lambda:self.status.config(text='● '+text,fg=color))
    def open_output(self):
        p=Path(self.output_dir.get()); p.mkdir(parents=True,exist_ok=True); os.startfile(str(p)) if os.name=='nt' else subprocess.Popen(['xdg-open',str(p)])
    def stop_render(self):
        self.stop_flag.set(); p=self.proc
        if p and p.poll() is None:
            try: p.terminate()
            except Exception: pass
        self.status_set('STOPPING','#ffca7a'); self.log('WARN','STOP diminta. Proses aktif dihentikan dan output parsial akan dihapus.')
    def start_render(self):
        if self.render_thread and self.render_thread.is_alive(): return messagebox.showinfo('Render berjalan','Render sedang berjalan.')
        ff=ffmpeg_path()
        if not ff: return messagebox.showerror('FFmpeg tidak ditemukan','ffmpeg.exe tidak ditemukan di folder aplikasi.')
        if not self.videos: return messagebox.showwarning('Video belum dipilih','Tambahkan minimal 1 video.')
        if not self.songs: return messagebox.showwarning('Lagu belum dipilih','Tambahkan minimal 1 lagu.')
        try: n=max(1,min(MAX_SONGS,int(self.song_count.get()))); reps=max(1,min(20,int(self.album_repeat.get()))); vars_=max(1,min(100,int(self.variations.get()))) if self.make_variations.get() else 1
        except Exception: return messagebox.showerror('Pengaturan salah','Nilai variasi, total lagu, atau ulang album tidak valid.')
        if n>len(self.songs): return messagebox.showwarning('Lagu kurang',f'Kamu memilih {n} lagu, tetapi hanya ada {len(self.songs)} lagu.')
        out=Path(self.output_dir.get()).expanduser(); out.mkdir(parents=True,exist_ok=True); self.stop_flag.clear(); self.progress['value']=0; self.render_thread=threading.Thread(target=self.worker,args=(out,n,reps,vars_),daemon=True); self.render_thread.start()
    def choose_playlist(self,n,reps):
        pool=list(self.songs); chosen=[]
        for _ in range(reps):
            block=pool[:]
            if self.shuffle.get(): random.shuffle(block)
            chosen.extend(block[:n])
        return chosen
    def encoder(self):
        if self.output_size.get() == 'Mengikuti Master' and self.engine.get() == 'Otomatis Maksimal':
            return ['-c:v','copy'], 'VIDEO COPY (Ultra Fast)'
        enc=run_quiet([ffmpeg_path(),'-hide_banner','-encoders'])
        if self.engine.get()=='Otomatis Maksimal' and 'h264_nvenc' in enc:return ['-c:v','h264_nvenc','-preset','p1','-tune','hq','-rc','vbr','-cq','23','-b:v','0'],'NVIDIA NVENC'
        if self.engine.get()=='Otomatis Maksimal' and 'h264_qsv' in enc:return ['-c:v','h264_qsv','-global_quality','23'],'Intel QSV'
        if self.quality.get()=='Kualitas Tinggi':return ['-c:v','libx264','-preset','fast','-crf','20'],'CPU x264 fast'
        return ['-c:v','libx264','-preset','veryfast','-crf','23'],'CPU x264 veryfast'
    def output_filter(self):
        s=self.output_size.get(); return 'scale=1280:-2,format=yuv420p' if s=='720p' else ('scale=1920:-2,format=yuv420p' if s=='1080p' else 'scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p')
    def render_one(self,video,playlist,outfile,video_no,total_videos):
        args=[ffmpeg_path(),'-hide_banner','-nostdin','-loglevel','info','-progress','pipe:2','-nostats','-y','-stream_loop','-1','-i',video]
        for a in playlist: args += ['-i',a]
        n=len(playlist); labs=[]; parts=[]
        for i in range(n):
            src=f'[{i+1}:a]'; dst=f'[a{i}]'; parts.append(src+'aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo'+dst); labs.append(dst)
        parts.append(''.join(labs)+f'concat=n={n}:v=0:a=1[aout]'); amap='[aout]'
        if self.normalize.get(): parts.append('[aout]loudnorm=I=-16:TP=-1.5:LRA=11[aout2]'); amap='[aout2]'
        enc,name=self.encoder()
        if enc == ['-c:v','copy']:
            args += ['-filter_complex',';'.join(parts),'-map','0:v:0','-map',amap] + enc
        else:
            filt=f'[0:v]{self.output_filter()}[vout];'+';'.join(parts); args += ['-filter_complex',filt,'-map','[vout]','-map',amap] + enc
        args += ['-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',str(outfile)]
        self.log('RENDER',f'Video {video_no}/{total_videos} • {n} lagu • Encoder: {name}'); self.log('PLAYLIST',' → '.join(Path(x).name for x in playlist))
        self.proc=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',**hidden_kwargs())
        duration=0.0; duration_seen=0; last=[]; start=time.time(); last_pct=-1
        while True:
            line=self.proc.stderr.readline()
            if line:
                line=line.strip(); last.append(line); last=last[-30:]
                m=re.search(r'Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)',line)
                if m:
                    duration_seen+=1
                    if duration_seen>1: duration+=int(m.group(1))*3600+int(m.group(2))*60+float(m.group(3))
                m=re.search(r'out_time_ms=(\d+)',line)
                if m and duration>0:
                    sec=int(m.group(1))/1000000; pct=max(0,min(99.9,sec/duration*100))
                    if pct>=last_pct+0.25:
                        last_pct=pct; elapsed=time.time()-start; self.after(0,lambda p=pct,e=elapsed,d=duration:self.update_progress(p,video_no,total_videos,e,d))
                m=re.search(r'speed=([0-9.]+)x',line)
                if m:self.after(0,lambda x=m.group(1):self.progress_text.config(text=f'Rendering • speed {x}x'))
            elif self.proc.poll() is not None: break
            if self.stop_flag.is_set():
                try:self.proc.terminate()
                except Exception:pass
                break
        rc=self.proc.wait(); self.proc=None
        if self.stop_flag.is_set():
            try:Path(outfile).unlink(missing_ok=True)
            except Exception:pass
            return False
        if rc!=0:
            self.log('ERROR',f'FFmpeg exit code {rc}')
            for x in last[-12:]:
                if x:self.log('FFMPEG',x)
            try:Path(outfile).unlink(missing_ok=True)
            except Exception:pass
            return False
        self.after(0,lambda:self.update_progress(100,video_no,total_videos,time.time()-start,duration or 1)); return True
    def update_progress(self,pct,vi,total,elapsed,duration):
        base=(vi-1)/total*100; overall=base+(pct/100)*(100/total); self.progress['value']=overall; self.progress_text.config(text=f'Video {vi}/{total} • {pct:.1f}% • {elapsed:.0f}s')
    def worker(self,out,n,reps,vars_):
        total=len(self.videos)*vars_; done=0; self.status_set('RENDERING'); self.log('INFO',f'Mulai batch: {len(self.videos)} video × {vars_} variasi = {total} output.')
        for vi,video in enumerate(self.videos,1):
            if self.stop_flag.is_set(): break
            for v in range(1,vars_+1):
                if self.stop_flag.is_set(): break
                playlist=self.choose_playlist(n,reps); stem=safe_name(Path(video).stem); name=safe_name(self.output_name.get() or stem); outfile=out/f'{name}_{stem}_V{v:02d}.mp4'; k=2; base=outfile
                while outfile.exists(): outfile=base.with_name(f'{base.stem}_{k}{base.suffix}'); k+=1
                ok=self.render_one(video,playlist,outfile,vi,len(self.videos))
                if ok:
                    done+=1; self.log('DONE',f'{outfile.name} • selesai')
                    if self.timestamp.get():
                        try: outfile.with_suffix('.txt').write_text('Video: '+video+'\n'+'\n'.join(f'{i+1}. {x}' for i,x in enumerate(playlist))+'\n',encoding='utf-8')
                        except Exception as e:self.log('WARN',f'Timestamp gagal: {e}')
                else:self.log('ERROR',f'Render gagal: {Path(video).name}')
        if self.stop_flag.is_set(): self.status_set('STOPPED','#ffca7a'); self.log('WARN',f'Batch dihentikan: {done}/{total} output selesai.')
        else:self.status_set('READY'); self.log('READY',f'Batch selesai: {done}/{total} output.'); self.after(0,lambda:self.progress_text.config(text=f'Selesai • {done}/{total} output'))

if __name__=='__main__': App().mainloop()
