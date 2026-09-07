import os,sys,random,shutil,subprocess,threading
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from pathlib import Path
APP_NAME='MasterRender PRO by AfroxSTD (ADIAN)'
MAX_VIDEOS=60; MAX_SONGS=20

def get_ffmpeg():
    roots=[]
    if getattr(sys,'frozen',False): roots=[Path(getattr(sys,'_MEIPASS',Path(sys.executable).parent)),Path(sys.executable).parent]
    else: roots=[Path(__file__).resolve().parent]
    for r in roots:
        p=r/'ffmpeg.exe'
        if p.is_file(): return str(p)
    return shutil.which('ffmpeg') or ''

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title(APP_NAME); self.geometry('1400x850'); self.minsize(1050,680); self.configure(bg='#0b0d17')
        self.videos=[]; self.songs=[]; self.ff=get_ffmpeg(); self.stop_event=threading.Event(); self.proc=None
        self.n=tk.IntVar(value=9); self.quality=tk.StringVar(value='Mengikuti Master'); self.variations=tk.IntVar(value=1); self.out=tk.StringVar(value=str(Path.cwd()/'output')); self.shuffle_each=tk.BooleanVar(value=True)
        self.styles(); self.make_ui(); self.log('READY','Aplikasi siap digunakan.'); self.log('INFO',f'FFmpeg: {self.ff}' if self.ff else 'FFmpeg tidak ditemukan.')
    def styles(self):
        s=ttk.Style(self); s.theme_use('clam'); s.configure('.',background='#111426',foreground='#e8eaff',fieldbackground='#171a2d'); s.configure('TNotebook',background='#0b0d17',borderwidth=0); s.configure('TNotebook.Tab',background='#15182a',foreground='#aeb4d8',padding=(22,10),font=('Segoe UI',10,'bold')); s.map('TNotebook.Tab',background=[('selected','#24204b')],foreground=[('selected','#c9bfff')]); s.configure('TButton',background='#171a2d',foreground='#dfe2f5',padding=(11,8),font=('Segoe UI',9,'bold')); s.map('TButton',background=[('active','#282d4a')]); s.configure('TCheckbutton',background='#111426',foreground='#cfd2ee'); s.configure('TProgressbar',troughcolor='#15182a',background='#8b6cff',borderwidth=0)
    def card(self,p): return tk.Frame(p,bg='#111426',highlightbackground='#252943',highlightthickness=1,bd=0)
    def lab(self,p,t,z=10,b=0): return tk.Label(p,text=t,bg=p.cget('bg'),fg='#eef0ff',font=('Segoe UI',z,'bold' if b else 'normal'))
    def make_ui(self):
        top=tk.Frame(self,bg='#0b0d17'); top.pack(fill='x',padx=22,pady=(18,8)); tk.Label(top,text='MASTERRENDER PRO',bg='#0b0d17',fg='#f2f0ff',font=('Segoe UI',22,'bold')).pack(side='left'); tk.Label(top,text='  by AfroxSTD  •  ADIAN',bg='#0b0d17',fg='#9e8cff',font=('Segoe UI',11,'bold')).pack(side='left',pady=(8,0)); tk.Label(top,text='● READY',bg='#171a2d',fg='#9b8cff',font=('Segoe UI',9,'bold'),padx=14,pady=7).pack(side='right')
        body=tk.Frame(self,bg='#0b0d17'); body.pack(fill='both',expand=True,padx=22,pady=8); side=tk.Frame(body,bg='#101323',width=210); side.pack(side='left',fill='y',padx=(0,14)); side.pack_propagate(False); tk.Label(side,text='WORKSPACE',bg='#101323',fg='#777eaa',font=('Segoe UI',9,'bold')).pack(anchor='w',padx=18,pady=(20,12))
        for x in ['Dashboard','Input Media','Render & Variasi','Live Streaming','Settings']:
            a=x=='Render & Variasi'; tk.Label(side,text=('◆  ' if a else '   ')+x,bg='#24204b' if a else '#101323',fg='#c9bfff' if a else '#9298bd',anchor='w',padx=16,pady=11,font=('Segoe UI',10,'bold' if a else 'normal')).pack(fill='x',padx=9,pady=2)
        main=tk.Frame(body,bg='#0b0d17'); main.pack(side='left',fill='both',expand=True); nb=ttk.Notebook(main); nb.pack(fill='both',expand=True); self.it=tk.Frame(nb,bg='#0b0d17'); self.rt=tk.Frame(nb,bg='#0b0d17'); self.lt=tk.Frame(nb,bg='#0b0d17'); nb.add(self.it,text='  Input  '); nb.add(self.rt,text='  Render & Variasi  '); nb.add(self.lt,text='  Live Streaming  '); self.input_ui(); self.render_ui(); self.live_ui()
        bot=tk.Frame(self,bg='#0b0d17'); bot.pack(fill='x',padx=22,pady=(4,18)); self.pb=ttk.Progressbar(bot,mode='determinate',maximum=100); self.pb.pack(fill='x',pady=(0,8)); self.pt=tk.Label(bot,text='Siap merender hingga 60 video',bg='#0b0d17',fg='#858caf',font=('Segoe UI',9)); self.pt.pack(side='left'); b=tk.Frame(bot,bg='#0b0d17'); b.pack(side='right'); ttk.Button(b,text='OPEN OUTPUT',command=self.open_output).pack(side='left',padx=4); ttk.Button(b,text='BERSIHKAN LOG',command=self.clear_log).pack(side='left',padx=4); ttk.Button(b,text='STOP',command=self.stop).pack(side='left',padx=4); tk.Button(b,text='START RENDER',command=self.start,bg='#7d5cff',fg='white',activebackground='#9a7fff',relief='flat',bd=0,font=('Segoe UI',10,'bold'),padx=24,pady=11).pack(side='left',padx=(8,0))
    def input_ui(self):
        l=self.card(self.it); l.pack(side='left',fill='both',expand=True,padx=(0,8),pady=12); r=self.card(self.it); r.pack(side='left',fill='both',expand=True,padx=(8,0),pady=12); self.lab(l,'VIDEO INPUT',11,1).pack(anchor='w',padx=18,pady=(18,5)); tk.Label(l,text='Tambahkan maksimal 60 video untuk batch rendering.',bg='#111426',fg='#858caf',font=('Segoe UI',9)).pack(anchor='w',padx=18); q=tk.Frame(l,bg='#111426'); q.pack(fill='x',padx=18,pady=14); ttk.Button(q,text='+ TAMBAH VIDEO',command=self.add_videos).pack(side='left'); ttk.Button(q,text='HAPUS SEMUA',command=self.clear_videos).pack(side='left',padx=8); self.vc=tk.Label(q,text='0 / 60',bg='#111426',fg='#b8aaff',font=('Segoe UI',10,'bold')); self.vc.pack(side='right'); self.vlist=tk.Listbox(l,bg='#0d1020',fg='#cfd2ee',selectbackground='#30285e',selectforeground='white',relief='flat',bd=0,font=('Segoe UI',9)); self.vlist.pack(fill='both',expand=True,padx=18,pady=(0,18))
        self.lab(r,'AUDIO TRACKS',11,1).pack(anchor='w',padx=18,pady=(18,5)); tk.Label(r,text='Masukkan maksimal 20 lagu. Setiap video mendapat playlist acak sendiri.',bg='#111426',fg='#858caf',font=('Segoe UI',9)).pack(anchor='w',padx=18); q=tk.Frame(r,bg='#111426'); q.pack(fill='x',padx=18,pady=14); ttk.Button(q,text='+ TAMBAH AUDIO',command=self.add_audio).pack(side='left'); ttk.Button(q,text='HAPUS SEMUA',command=self.clear_audio).pack(side='left',padx=8); self.ac=tk.Label(q,text='0 / 20 lagu',bg='#111426',fg='#b8aaff',font=('Segoe UI',10,'bold')); self.ac.pack(side='right'); self.alist=tk.Listbox(r,bg='#0d1020',fg='#cfd2ee',selectbackground='#30285e',selectforeground='white',relief='flat',bd=0,font=('Segoe UI',9)); self.alist.pack(fill='both',expand=True,padx=18,pady=(0,18))
    def render_ui(self):
        l=self.card(self.rt); l.pack(side='left',fill='both',expand=True,padx=(0,8),pady=12); r=self.card(self.rt); r.pack(side='left',fill='both',expand=True,padx=(8,0),pady=12); self.lab(l,'RENDER SETTINGS',11,1).pack(anchor='w',padx=18,pady=(18,15)); g=tk.Frame(l,bg='#111426'); g.pack(fill='x',padx=18); tk.Label(g,text='Total lagu yang akan diacak',bg='#111426',fg='#eef0ff',font=('Segoe UI',10,'bold')).grid(row=0,column=0,sticky='w',pady=8); ttk.Spinbox(g,from_=1,to=20,textvariable=self.n,width=27).grid(row=0,column=1,sticky='e',padx=(25,0),pady=8); tk.Label(g,text='(maks. 20)',bg='#111426',fg='#858caf',font=('Segoe UI',9)).grid(row=0,column=2,sticky='w',padx=8); self.row(g,1,'Quality',ttk.Combobox(g,textvariable=self.quality,values=['Mengikuti Master','Cepat','Kualitas Tinggi'],state='readonly',width=25)); self.row(g,2,'Variasi per video',ttk.Spinbox(g,from_=1,to=100,textvariable=self.variations,width=27)); ttk.Checkbutton(g,text='Acak ulang playlist untuk setiap video',variable=self.shuffle_each).grid(row=3,column=0,columnspan=3,sticky='w',pady=10); self.lab(l,'OUTPUT FOLDER',10,1).pack(anchor='w',padx=18,pady=(22,8)); q=tk.Frame(l,bg='#111426'); q.pack(fill='x',padx=18); tk.Entry(q,textvariable=self.out,bg='#0d1020',fg='#cfd2ee',insertbackground='white',relief='flat',font=('Segoe UI',9)).pack(side='left',fill='x',expand=True,ipady=8); ttk.Button(q,text='...',command=self.choose).pack(side='left',padx=(7,0)); tk.Label(l,text='Durasi output = total durasi seluruh lagu yang dipilih. Video di-loop sampai playlist benar-benar selesai.',bg='#111426',fg='#858caf',wraplength=500,justify='left',font=('Segoe UI',9)).pack(anchor='w',padx=18,pady=18); self.lab(r,'RENDER LOG',11,1).pack(anchor='w',padx=18,pady=(18,10)); self.logbox=tk.Text(r,bg='#0a0d18',fg='#bfc5e8',insertbackground='white',relief='flat',bd=0,font=('Consolas',9),wrap='word'); self.logbox.pack(fill='both',expand=True,padx=18,pady=(0,18));
    def row(self,p,r,t,w): tk.Label(p,text=t,bg='#111426',fg='#858caf',font=('Segoe UI',9)).grid(row=r,column=0,sticky='w',pady=6); w.grid(row=r,column=1,columnspan=2,sticky='e',padx=(35,0),pady=6); p.grid_columnconfigure(1,weight=1)
    def live_ui(self):
        f=self.card(self.lt); f.pack(fill='both',expand=True,padx=12,pady=12); self.lab(f,'LIVE STREAMING',14,1).pack(anchor='w',padx=22,pady=(22,8)); tk.Label(f,text='Panel streaming RTMP disiapkan untuk versi berikutnya.',bg='#111426',fg='#858caf',font=('Segoe UI',10)).pack(anchor='w',padx=22)
    def add_videos(self):
        fs=filedialog.askopenfilenames(title='Pilih video',filetypes=[('Video','*.mp4 *.mov *.mkv *.avi *.webm *.m4v'),('Semua file','*.*')]);
        for f in fs[:MAX_VIDEOS-len(self.videos)]:
            if f not in self.videos:self.videos.append(f)
        self.refresh_v()
    def refresh_v(self): self.vlist.delete(0,'end'); [self.vlist.insert('end',f'{i:02d}. {Path(x).name}') for i,x in enumerate(self.videos,1)]; self.vc.config(text=f'{len(self.videos)} / {MAX_VIDEOS}')
    def add_audio(self):
        fs=filedialog.askopenfilenames(title='Pilih lagu',filetypes=[('Audio','*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.opus'),('Semua file','*.*')]);
        for f in fs[:MAX_SONGS-len(self.songs)]:
            if f not in self.songs:self.songs.append(f)
        self.refresh_a()
    def refresh_a(self): self.alist.delete(0,'end'); [self.alist.insert('end',f'{i:02d}. {Path(x).name}') for i,x in enumerate(self.songs,1)]; self.ac.config(text=f'{len(self.songs)} / {MAX_SONGS} lagu')
    def clear_videos(self): self.videos.clear(); self.refresh_v()
    def clear_audio(self): self.songs.clear(); self.refresh_a()
    def choose(self):
        d=filedialog.askdirectory(title='Pilih folder output');
        if d:self.out.set(d)
    def open_output(self): os.makedirs(self.out.get(),exist_ok=True); os.startfile(self.out.get())
    def clear_log(self): self.logbox.delete('1.0','end')
    def log(self,tag,msg): self.after(0,lambda:self._log(tag,msg))
    def _log(self,tag,msg): self.logbox.insert('end',f'[{tag}] {msg}\n'); self.logbox.see('end')
    def start(self):
        if self.render_thread_alive(): return
        if not self.videos:return messagebox.showwarning(APP_NAME,'Tambahkan minimal 1 video.')
        if not self.songs:return messagebox.showwarning(APP_NAME,'Tambahkan minimal 1 lagu.')
        try:n=int(self.n.get())
        except:n=1
        if n<1 or n>20:return messagebox.showwarning(APP_NAME,'Total lagu harus 1 sampai 20.')
        if n>len(self.songs):return messagebox.showwarning(APP_NAME,f'Diminta {n} lagu, tetapi hanya ada {len(self.songs)} lagu.')
        if not self.ff:return messagebox.showerror(APP_NAME,'FFmpeg tidak ditemukan.')
        os.makedirs(self.out.get(),exist_ok=True); self.stop_event.clear(); self.pb['value']=0; self.pt.config(text=f'Mulai 0/{len(self.videos)}'); self.log('INFO',f'Mulai: {len(self.videos)} video × {n} lagu per playlist.'); self.render_thread=threading.Thread(target=self.worker,args=(n,),daemon=True); self.render_thread.start()
    def render_thread_alive(self): return hasattr(self,'render_thread') and self.render_thread.is_alive()
    def stop(self):
        self.stop_event.set(); p=self.proc
        if p and p.poll() is None:
            try:p.terminate()
            except:pass
        self.log('WARN','STOP diminta. Output yang belum selesai akan dibuang.')
    def worker(self,n):
        total=len(self.videos)
        try:
            for i,v in enumerate(self.videos,1):
                if self.stop_event.is_set():break
                pl=list(self.songs); random.shuffle(pl); pl=pl[:n]
                self.log('RENDER',f'Video {i}/{total}: {Path(v).name}')
                self.log('INFO','Playlist: '+' | '.join(Path(x).name for x in pl))
                for var in range(1,max(1,int(self.variations.get()))+1):
                    if self.stop_event.is_set():break
                    try:
                        out=self.render_one(v,pl,i,var)
                        if out:self.log('INFO',f'SELESAI: {Path(out).name}')
                    except Exception as e:self.log('ERROR',str(e))
                self.after(0,lambda p=i/total*100:self.pb.configure(value=p)); self.after(0,lambda i=i,t=total:self.pt.config(text=f'Video {i}/{t} selesai'))
        finally:
            self.proc=None
            self.log('READY','Render selesai.' if not self.stop_event.is_set() else 'Render dihentikan.')
    def render_one(self,video,playlist,index,var):
        base=Path(self.out.get()); out=self.unique(base/f'{Path(video).stem}_MasterRender_V{var}.mp4'); preset,crf=self.vsettings(); inputs=[]
        for song in playlist: inputs += ['-i',song]
        parts=[]
        for j in range(len(playlist)): parts.append(f'[{j}:a:0]aresample=48000,asetpts=N/SR/TB[a{j}]')
        concat=''.join(f'[a{j}]' for j in range(len(playlist)))+f'concat=n={len(playlist)}:v=0:a=1[playlist]'
        fc=';'.join(parts+[concat])
        cmd=[self.ff,'-hide_banner','-nostdin','-y','-stream_loop','-1','-i',video]+inputs+['-filter_complex',fc,'-map','0:v:0','-map','[playlist]','-vf','scale=trunc(iw/2)*2:ih,format=yuv420p','-c:v','libx264','-preset',preset,'-crf',crf,'-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',str(out)]
        rc=self.run(cmd)
        if rc==0:return str(out)
        try:out.unlink()
        except:pass
        if rc==-2: return ''
        raise RuntimeError('Render gagal. Lihat baris [FFMPEG] di log.')
    def vsettings(self):
        q=self.quality.get(); return ('veryfast','23') if q=='Cepat' else ('slow','18') if q=='Kualitas Tinggi' else ('medium','20')
    def run(self,cmd):
        try:
            self.proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,text=True,encoding='utf-8',errors='replace',bufsize=1)
            for line in self.proc.stdout:
                line=line.rstrip(); low=line.lower()
                if any(k in low for k in ('error','invalid','failed','unable','no such','conversion failed','duration:')):self.log('FFMPEG',line)
                if self.stop_event.is_set() and self.proc.poll() is None:
                    try:self.proc.terminate()
                    except:pass
            rc=self.proc.wait(); self.proc=None
            return -2 if self.stop_event.is_set() else rc
        except Exception as e:self.proc=None; self.log('ERROR',f'FFmpeg exception: {e}'); return -1
    def unique(self,p):
        if not p.exists():return p
        i=2
        while (q:=p.with_name(f'{p.stem}_{i}{p.suffix}')).exists():i+=1
        return q

if __name__=='__main__': App().mainloop()
