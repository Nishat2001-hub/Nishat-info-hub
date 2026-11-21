import re,subprocess,unicodedata,json,numpy as np
import glob as _g
A=_g.glob('audio.mp3')[0]
out=subprocess.run(['ffmpeg','-i',A,'-af','silencedetect=noise=-32dB:d=0.12','-f','null','-'],capture_output=True,text=True).stderr
st=[float(x) for x in re.findall(r'silence_start: ([\d.]+)',out)]; en=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',out)]
dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',A]))
if len(st)>len(en): en.append(dur)
P=[(s,e) for s,e in zip(st,en) if s>0.05 and e<dur-0.05]
import sys,glob
SRT=sys.argv[1] if len(sys.argv)>1 else glob.glob('user.srt')[0]
raw=open(SRT,encoding='utf-8-sig').read()
raw=re.sub(r'\[span_\d+\]\((?:start|end)_span\)','',raw)
cues=[]
for blk in re.split(r'\n\s*\n',raw.strip()):
    L=[l for l in blk.strip().split('\n')]
    if len(L)>=3 and '-->' in L[1]: cues.append(' '.join(x.strip() for x in L[2:]))
    elif len(L)>=2 and '-->' in L[0]: cues.append(' '.join(x.strip() for x in L[1:]))
def fix(s):
    s=unicodedata.normalize('NFC',s)
    return s.replace('\u09af\u09bc','\u09df').replace('\u09a1\u09bc','\u09dc').replace('\u09a2\u09bc','\u09dd')
cues=[fix(c) for c in cues]
print('cue count',len(cues))
w=[len(re.findall(r'[\u0980-\u09ff]',c))-len(re.findall(r'[\u09be-\u09cd\u09d7]',c))*0.5 for c in cues]
n=len(cues); M=len(P)
def sp(i,j):
    a=0.0 if i==0 else P[i-1][1]; b=dur if j==M+1 else P[j-1][0]
    t=b-a
    for q in range(i+1,j): t-=P[q-1][1]-P[q-1][0]
    return t
spk=dur-sum(e-s for s,e in P); k=spk/sum(w)
INF=1e18
D=np.full((n+1,M+2),INF); B={}
D[0][0]=0
for c in range(1,n+1):
    for j in range(1,M+2):
        if c<n and j==M+1: continue
        if c==n and j!=M+1: continue
        for i in range(0,j):
            if D[c-1][i]>=INF: continue
            t=sp(i,j)
            if t<=0.2: continue
            pl=0 if j==M+1 else P[j-1][1]-P[j-1][0]
            cost=D[c-1][i]+(t-k*w[c-1])**2/(k*w[c-1])-4*pl
            if cost<D[c][j]: D[c][j]=cost;B[(c,j)]=i
j=M+1;path=[]
for c in range(n,0,-1):
    i=B[(c,j)];path.append((i,j));j=i
path=path[::-1]
def ts(t):
    h=int(t//3600);m=int(t%3600//60);s=t%60;return f'{h:02d}:{m:02d}:{int(s):02d},{int(round((s-int(s))*1000)):03d}'
res=[]
for c,(i,j) in enumerate(path):
    a=0.3 if i==0 else P[i-1][1]-0.03; b=dur-0.05 if j==M+1 else P[j-1][0]+0.12
    res.append((a,b,cues[c]))
    print(c+1,round(a,2),round(b,2),round(b-a,2),round(k*w[c],2),cues[c][:18])
open('subs.srt','w',encoding='utf-8').write('\n'.join(f'{i+1}\n{ts(a)} --> {ts(b)}\n{t}\n' for i,(a,b,t) in enumerate(res)))
json.dump(res,open('cues.json','w'),ensure_ascii=False); print(dur,len(P))
