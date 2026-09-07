import os,sys,random,shutil,subprocess,threading
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from pathlib import Path
APP_NAME='MasterRender PRO by AfroxSTD (ADIAN)'
MAX_VIDEOS=60; MAX_SONGS=20

def get_ffmpeg():
    roots=[Path(getattr(sys,'_MEIPASS',Path(sys.executable).parent)),Path(sys.executable).parent] if getattr(sys,'frozen',False) else [Path(__file__).parent]
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
        s=ttk.Style(self); s.theme_use('clam'); s.configure('.',background='#111426',foreground='#e8eaff',fieldbackground='#171a2d'); s.configure('TNotebook',background='#0b0d17'); s.configure('TNotebook.Tab',background='#15182a',foreground='#aeb4d8',padding=(22,10),font=('Segoe UI',10,'bold')); s.map('TNotebook.Tab',background=[('selected','#24204b')],foreground=[('selected','#c9bfff')]); s.configure('TButton',background='#171a2d',foreground='#dfe2f5',padding=(11,8)); s.configure('TCheckbutton',background='#111426',foreground='#cfd2ee'); s.configure('TProgressbar',troughcolor='#15182a',background='#8b6cff')
    def card(self,p): return tk.Frame(p,bg='#111426',highlightbackground='#252943',highlightthickness=1)
    def title(self,p,t,n=11): tk.Label(p,text=t,bg=p.cget('bg'),fg='#eef0ff',font=('Segoe UI',n,'bold')).pack(anchor='w',padx=18,pady=(18,8))
    def make_ui(self):
        h=tk.Frame(self,bg='#0b0d17'); h.pack(fill='x',padx=22,pady=(18,8)); tk.Label(h,text='MASTERRENDER PRO',bg='#0b0d17',fg='#f2f0ff',font=('Segoe UI',22,'bold')).pack(side='left'); tk.Label(h,text='  by AfroxSTD • ADIAN',bg='#0b0d17',fg='#9e8cff',font=('Segoe UI',11,'bold')).pack(side='left',pady=(8,0)); tk.Label(h,text='● READY',bg='#171a2d',fg='#9b8cff',padx=14,pady=7).pack(side='right')
        body=tk.Frame(self,bg='#0b0d17'); body.pack(fill='both',expand=True,padx=22,pady=8); side=tk.Frame(body,bg='#101323',width=210); side.pack(side='left',fill='y',padx=(0,14)); side.pack_propagate(False); tk.Label(side,text='WORKSPACE',bg='#101323',fg='#777eaa').pack(anchor='w',padx=18,pady=(20,12))
        for x in ['Dashboard','Input Media','Render & Variasi','Live Streaming','Settings']:
            a=x=='Render & Variasi'; tk.Label(side,text=('◆  ' if a else '   ')+x,bg='#24204b' if a else '#101323',fg='#c9bfff' if a else '#9298bd',anchor='w',padx=16,pady=11).pack(fill='x',padx=9,pady=2)
        main=tk.Frame(body,bg='#0b0d17'); main.pack(side='left',fill='both',expand=True); nb=ttk.Notebook(main); nb.pack(fill='both',expand=True); inp=tk.Frame(nb,bg='#0b0d17'); ren=tk.Frame(nb,bg='#0b0d17'); live=tk.Frame(nb,bg='#0b0d17'); nb.add(inp,text='  Input  '); nb.add(ren,text='  Render & Variasi  '); nb.add(live,text='  Live Streaming  '); self.input_ui(inp); self.render_ui(ren); self.live_ui(live)
        b=tk.Frame(self,bg='#0b0d17'); b.pack(fill='x',padx=22,pady=(4,18)); self.pb=ttk.Progressbar(b,maximum=100); self.pb.pack(fill='x',pady=(0,8)); self.pt=tk.Label(b,text='Siap merender hingga 60 video',bg='#0b0d17',fg='#858caf'); self.pt.pack(side='left'); r=tk.Frame(b,bg='#0b0d17'); r.pack(side='right'); ttk.Button(r,text='OPEN OUTPUT',command=self.open_output).pack(side='left',padx=4); ttk.Button(r,text='BERSIHKAN LOG',command=lambda:self.logbox.delete('1.0','end')).pack(side='left',padx=4); ttk.Button(r,text='STOP',command=self.stop).pack(side='left',padx=4); tk.Button(r,text='START RENDER',command=self.start,bg='#7d5cff',fg='white',relief='flat',font=('Segoe UI',10,'bold'),padx=24,pady=11).pack(side='left',padx=(8,0))
    def input_ui(self,p):
        a=self.card(p); a.pack(side='left',fill='both',expand=True,padx=(0,8),pady=12); c=self.card(p); c.pack(side='left',fill='both',expand=True,padx=(8,0),pady=12); self.title(a,'VIDEO INPUT'); tk.Label(a,text='Maksimal 60 video.',bg='#111426',fg='#858caf').pack(anchor='w',padx=18); q=tk.Frame(a,bg='#111426'); q.pack(fill='x',padx=18,pady=14); ttk.Button(q,text='+ TAMBAH VIDEO',command=self.add_video).pack(side='left'); ttk.Button(q,text='HAPUS SEMUA',command=self.clear_video).pack(side='left',padx=8); self.vc=tk.Label(q,text='0 / 60',bg='#111426',fg='#b8aaff'); self.vc.pack(side='right'); self.vlist=tk.Listbox(a,bg='#0d1020',fg='#cfd2ee',selectbackground='#30285e',relief='flat',bd=0); self.vlist.pack(fill='both',expand=True,padx=18,pady=(0,18)); self.title(c,'AUDIO TRACKS'); tk.Label(c,text='Maksimal 20 lagu.',bg='#111426',fg='#858caf').pack(anchor='w',padx=18); q=tk.Frame(c,bg='#111426'); q.pack(fill='x',padx=18,pady=14); ttk.Button(q,text='+ TAMBAH AUDIO',command=self.add_song).pack(side='left'); ttk.Button(q,text='HAPUS SEMUA',command=self.clear_song).pack(side='left',padx=8); self.sc=tk.Label(q,text='0 / 20 lagu',bg='#111426',fg='#b8aaff'); self.sc.pack(side='right'); self.slist=tk.Listbox(c,bg='#0d1020',fg='#cfd2ee',selectbackground='#30285e',relief='flat',bd=0); self.slist.pack(fill='both',expand=True,padx=18,pady=(0,18))
    def render_ui(self,p):
        a=self.card(p); a.pack(side='left',fill='both',expand=True,padx=(0,8),pady=12); c=self.card(p); c.pack(side='left',fill='both',expand=True,padx=(8,0),pady=12); self.title(a,'RENDER SETTINGS'); g=tk.Frame(a,bg='#111426'); g.pack(fill='x',padx=18); tk.Label(g,text='Total lagu yang akan diacak',bg='#111426',fg='#eef0ff',font=('Segoe UI',10,'bold')).grid(row=0,column=0,sticky='w',pady=8); ttk.Spinbox(g,from_=1,to=20,textvariable=self.n,width=27).grid(row=0,column=1,padx=25); tk.Label(g,text='(maks. 20)',bg='#111426',fg='#858caf').grid(row=0,column=2); tk.Label(g,text='Quality',bg='#111426',fg='#858caf').grid(row=1,column=0,sticky='w',pady=6); ttk.Combobox(g,textvariable=self.quality,values=['Mengikuti Master','Cepat','Kualitas Tinggi'],state='readonly',width=25).grid(row=1,column=1,columnspan=2,sticky='e'); tk.Label(g,text='Variasi per video',bg='#111426',fg='#858caf').grid(row=2,column=0,sticky='w',pady=6); ttk.Spinbox(g,from_=1,to=100,textvariable=self.variations,width=27).grid(row=2,column=1,columnspan=2,sticky='e'); ttk.Checkbutton(g,text='Acak ulang playlist untuk setiap video',variable=self.shuffle_each).grid(row=3,column=0,columnspan=3,sticky='w',pady=10); self.title(a,'OUTPUT FOLDER',10); q=tk.Frame(a,bg='#111426'); q.pack(fill='x',padx=18); tk.Entry(q,textvariable=self.out,bg='#0d1020',fg='#cfd2ee',relief='flat').pack(side='left',fill='x',expand=True,ipady=8); ttk.Button(q,text='...',command=self.choose_output).pack(side='left',padx=7); tk.Label(a,text='Durasi output = total durasi semua lagu terpilih. Video di-loop sampai playlist selesai.',bg='#111426',fg='#858caf',wraplength=500,justify='left').pack(anchor='w',padx=18,pady=18); self.title(c,'RENDER LOG'); self.logbox=tk.Text(c,bg='#0a0d18',fg='#bfc5e8',relief='flat',bd=0,font=('Consolas',9),wrap='word'); self.logbox.pack(fill='both',expand=True,padx=18,pady=(0,18))
    def live_ui(self,p):
        a=self.card(p); a.pack(fill='both',expand=True,padx=12,pady=12); self.title(a,'LIVE STREAMING',14); tk.Label(a,text='Panel RTMP disiapkan untuk versi berikutnya.',bg='#111426',fg='#858caf').pack(anchor='w',padx=22)
    def add_video(self):
        fs=filedialog.askopenfilenames(title='Pilih video',filetypes=[('Video','*.mp4 *.mov *.mkv *.avi *.webm *.m4v'),('Semua','*.*')]); self.videos += [x for x in fs if x not in self.videos][:MAX_VIDEOS-len(self.videos)]; self.refresh_video()
    def add_song(self):
        fs=filedialog.askopenfilenames(title='Pilih lagu',filetypes=[('Audio','*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.opus'),('Semua','*.*')]); self.songs += [x for x in fs if x not in self.songs][:MAX_SONGS-len(self.songs)]; self.refresh_song()
    def refresh_video(self): self.vlist.delete(0,'end'); [self.vlist.insert('end',f'{i:02d}. {Path(x).name}') for i,x in enumerate(self.videos,1)]; self.vc.config(text=f'{len(self.videos)} / 60')
    def refresh_song(self): self.slist.delete(0,'end'); [self.slist.insert('end',f'{i:02d}. {Path(x).name}') for i,x in enumerate(self.songs,1)]; self.sc.config(text=f'{len(self.songs)} / 20 lagu')
    def clear_video(self): self.videos=[]; self.refresh_video()
    def clear_song(self): self.songs=[]; self.refresh_song()
    def choose_output(self):
        d=filedialog.askdirectory(title='Pilih folder output');
        if d:self.out.set(d)
    def open_output(self): os.makedirs(self.out.get(),exist_ok=True); os.startfile(self.out.get())
    def log(self,t,x):
        if hasattr(self,'logbox'): self.after(0,lambda:self.logbox.insert('end',f'[{t}] {x}\n'))
    def start(self):
        if not self.videos:return messagebox.showwarning(APP_NAME,'Tambahkan minimal 1 video.')
        if not self.songs:return messagebox.showwarning(APP_NAME,'Tambahkan minimal 1 lagu.')
        try:n=int(self.n.get()); v=int(self.variations.get())
        except: n=1; v=1
        if n<1 or n>20 or n>len(self.songs): return messagebox.showwarning(APP_NAME,f'Total lagu harus 1-{min(20,len(self.songs))}.')
        if not self.ff:return messagebox.showerror(APP_NAME,'FFmpeg tidak ditemukan.')
        os.makedirs(self.out.get(),exist_ok=True); self.stop_event.clear(); self.pb['value']=0; threading.Thread(target=self.worker,args=(n,v),daemon=True).start()
    def stop(self):
        self.stop_event.set(); p=self.proc
        if p and p.poll() is None:
            try:p.terminate()
            except:pass
        self.log('WARN','STOP diminta.')
    def worker(self,n,v):
        total=len(self.videos)
        for vi,video in enumerate(self.videos,1):
            if self.stop_event.is_set():break
            order=list(self.songs); random.shuffle(order); order=order[:n]; self.log('RENDER',f'Video {vi}/{total}: {Path(video).name}'); self.log('INFO','Playlist: '+' | '.join(Path(x).name for x in order))
            for k in range(1,v+1):
                if self.stop_event.is_set():break
                out=self.render(video,order,vi,k)
                if out:self.log('INFO',f'SELESAI: {Path(out).name}')
            self.after(0,lambda p=vi/total*100:self.pb.configure(value=p)); self.after(0,lambda i=vi,t=total:self.pt.configure(text=f'Video {i}/{t} selesai'))
        self.log('READY','Render selesai.' if not self.stop_event.is_set() else 'Render dihentikan.'); self.proc=None
    def render(self,video,songs,vi,k):
        out=self.unique(Path(self.out.get())/f'{Path(video).stem}_MasterRender_V{k}.mp4'); preset='veryfast' if self.quality.get()=='Cepat' else 'slow' if self.quality.get()=='Kualitas Tinggi' else 'medium'; crf='23' if preset=='veryfast' else '18' if preset=='slow' else '20'; cmd=[self.ff,'-hide_banner','-nostdin','-y','-stream_loop','-1','-i',video]; parts=[]
        for i,s in enumerate(songs,1): cmd += ['-i',s]; parts.append(f'[{i}:a]aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[a{i}]')
        parts.append(''.join(f'[a{i}]' for i in range(1,len(songs)+1))+f'concat=n={len(songs)}:v=0:a=1[playlist]'); filt=';'.join(parts); cmd += ['-filter_complex',filt,'-map','0:v:0','-map','[playlist]','-vf','scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p','-c:v','libx264','-preset',preset,'-crf',crf,'-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',str(out)]; return self.run(cmd,out)
    def run(self,cmd,out):
        try:
            self.proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,text=True,encoding='utf-8',errors='replace',bufsize=1); tail=[]
            for line in self.proc.stdout:
                line=line.rstrip(); tail.append(line); tail=tail[-8:]; low=line.lower()
                if any(x in low for x in ['error','invalid','failed','unable','no such','conversion failed']): self.log('FFMPEG',line)
                if self.stop_event.is_set():
                    try:self.proc.terminate()
                    except:pass
            rc=self.proc.wait(); self.proc=None
            if rc!=0:
                for x in tail:self.log('FFMPEG',x)
            return str(out) if rc==0 and out.exists() else None
        except Exception as e: self.proc=None; self.log('ERROR',str(e)); return None
    def unique(self,p):
        if not p.exists():return p
        i=2
        while True:
            q=p.with_name(f'{p.stem}_{i}{p.suffix}')
            if not q.exists():return q
            i+=1

if __name__=='__main__': App().mainloop()
