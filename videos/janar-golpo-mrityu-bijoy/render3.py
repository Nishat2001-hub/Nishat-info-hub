import json,math,random,sys,re,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from fontTools.ttLib import TTFont
import arabic
import shape as SM
W,H,S=1296,2304,2; OW,OH=1080,1920; FPS=30; DUR=280.920813
YEL=(255,210,31);ORG=(232,89,12);RED=(211,47,47);BLU=(91,107,122)
BRW=(43,32,24);PAP=(255,244,214);GRN=(31,138,91);CREAM=(250,243,230);GOLD=(255,201,60)
DUSK=(30,28,42);NITE=(10,14,26)
CM={n:set(TTFont(f'fonts/{n}.ttf').getBestCmap()) for n in ['sans7','sans6','lat7','lat6']}
def fonts(sz,w='7'): return (f'sans{w}',sz),(f'lat{w}',sz)
def runs(t,m,fb):
    out=[];cur='';cf=None
    for ch in t:
        o=ord(ch);f=m if (o in CM[m[0]] or o in (0x200c,0x200d)) else fb
        if cf is None: cf=f
        if f is not cf: out.append((cur,cf));cur='';cf=f
        cur+=ch
    if cur: out.append((cur,cf))
    return out
def tw(t,m,fb): return sum(SM.w(k[0],s,k[1]) for s,k in runs(t,m,fb))
def dtext(d,x,y,t,m,fb,fill,anchor='l',stroke=0,sf=None,alpha=None):
    parts=[];w=0
    for s,k in runs(t,m,fb):
        if not s:continue
        im,bl,pw=SM.img(k[0],s,k[1],fill,stroke,sf)
        if alpha is not None: im.putalpha(im.getchannel('A').point(lambda v,a=alpha:int(v*a/255)))
        parts.append((im,bl));w+=pw
    if not parts:return
    if anchor=='m': x-=w/2
    if anchor=='r': x-=w
    d._image.paste(parts[0][0],(int(x),int(y)-parts[0][1]),parts[0][0]);x+=parts[0][0].width
    for im,bl in parts[1:]:
        d._image.paste(im,(int(x),int(y)-bl),im);x+=im.width
class Cv:
    def __init__(s,stops):
        ys=np.linspace(0,1,H*S)[:,None];arr=np.zeros((H*S,1,3))
        for cc in range(3):arr[:,0,cc]=np.interp(ys[:,0],[p for p,_ in stops],[c[cc] for _,c in stops])
        s.im=Image.fromarray(np.repeat(arr,W*S,axis=1).astype('uint8'));s.d=ImageDraw.Draw(s.im)
    def P(s,pts):return [(x*S,y*S) for x,y in pts]
    def rect(s,x0,y0,x1,y1,fill,ol=None,w=6,r=0):
        b=[x0*S,y0*S,x1*S,y1*S]
        if r:s.d.rounded_rectangle(b,r*S,fill=fill,outline=ol,width=w if ol else 0)
        else:s.d.rectangle(b,fill=fill,outline=ol,width=w if ol else 0)
    def ell(s,x0,y0,x1,y1,fill,ol=None,w=6):s.d.ellipse([x0*S,y0*S,x1*S,y1*S],fill=fill,outline=ol,width=w if ol else 0)
    def circ(s,x,y,r,fill,ol=None,w=6):s.ell(x-r,y-r,x+r,y+r,fill,ol,w)
    def poly(s,pts,fill,ol=None,w=6):s.d.polygon(s.P(pts),fill=fill,outline=ol,width=w if ol else 0)
    def line(s,pts,fill,w=6):s.d.line(s.P(pts),fill=fill,width=w*S,joint='curve')
    def stars(s,n,ymax,seed=1):
        r=random.Random(seed)
        for _ in range(n):
            x,y=r.uniform(0,W),r.uniform(0,ymax);z=r.choice([2,2,3,4]);c=tuple(int(v*r.uniform(.5,1)) for v in (250,246,230))
            s.circ(x,y,z,c)
    def crescent(s,x,y,r,col=(255,232,170)):
        px=s.im.getpixel((int(min(x+r*1.3,W-1))*S),) if False else None
        px=s.im.getpixel((int(min(x+r*1.3,W-1))*S,int((y-r*.2)*S)));s.circ(x,y,r,col);s.circ(x+r*.42,y-r*.18,r*.86,px)
    def mosque(s,cx,by,k,col):
        s.rect(cx-300*k,by-230*k,cx+300*k,by+40,col)
        s.ell(cx-190*k,by-230*k-190*k,cx+190*k,by-230*k+190*k,col)
        s.rect(cx-6*k,by-230*k-250*k,cx+6*k,by-230*k-170*k,col);s.circ(cx,by-230*k-262*k,12*k,col)
        for sx in (-1,1):
            mx=cx+sx*390*k
            s.rect(mx-26*k,by-560*k,mx+26*k,by+40,col);s.rect(mx-42*k,by-520*k,mx+42*k,by-496*k,col)
            s.poly([(mx-30*k,by-560*k),(mx+30*k,by-560*k),(mx,by-680*k)],col);s.rect(mx-3*k,by-720*k,mx+3*k,by-680*k,col)
    def out(s):return s.im.resize((W,H),Image.LANCZOS)
def radial(r):
    y,x=np.mgrid[-r:r,-r:r];d=np.sqrt(x*x+y*y)/r;a=np.clip(1-d,0,1)**2
    return Image.fromarray((a*255).astype('uint8'),'L')
GL={}
def glow(im,x,y,r,col,k=1.0):
    if r not in GL:GL[r]=radial(r)
    m=GL[r].point(lambda v:int(v*min(k,1)));im.paste(Image.new('RGB',(2*r,2*r),col),(int(x-r),int(y-r)),m)
def sm(x,a,b):return min(1,max(0,(x-a)/(b-a)))
def flick(t,s=0):return .78+.22*math.sin(t*7+s)*math.sin(t*3.1+1)
def zoom(im,z,px=0,py=0):
    cw,ch=W/z,H/z;x0=(W-cw)/2+px*(W-cw)/2;y0=(H-ch)/2+py*(H-ch)/2
    return im.resize((OW,OH),Image.BILINEAR,box=(x0,y0,x0+cw,y0+ch))
RAIN={}
def streaks(seed,n=60):
    if seed not in RAIN:
        r=random.Random(seed);RAIN[seed]=[(r.uniform(0,W),r.uniform(-300,H),r.uniform(300,640),r.uniform(.5,1.0)) for _ in range(n)]
    return RAIN[seed]
def rain(im,t,seed,n=60,col=(120,140,168)):
    d=ImageDraw.Draw(im)
    for x,y,ln,k in streaks(seed)[:n]:
        yy=int((y+t*900*k)%2800)-300
        d.line([(x,yy),(x-34,yy+ln*0.55)],fill=col,width=max(1,int(2*k)))
def motes(im,t,c=(255,226,170)):
    d=ImageDraw.Draw(im)
    for i in range(24):
        x=random.Random(i).uniform(0,W);y=random.Random(i+99).uniform(900,2200);s=random.Random(i+5).uniform(.4,1)
        yy=(y-t*16*s)%1300+900;xx=x+math.sin(t*.6+s*9)*22
        d.ellipse([xx-2,yy-2,xx+2,yy+2],fill=c)
def citybokeh(c,seed,ymax=1100):
    r=random.Random(seed)
    for _ in range(16):
        x,y=r.uniform(60,W-60),r.uniform(ymax-500,ymax);Z=r.uniform(.45,1)
        glow(c.im,x,y,int(26*Z),(255,206,120),.5*Z)
def windows(c,seed,):
    r=random.Random(seed);x=0
    while x<W:
        w=r.randint(90,180);h=r.randint(340,760)
        c.rect(x,H-h-140,x+w,H-140,(9,12,22))
        for yy in range(H-h-110,H-180,70):
            for xx in range(x+14,x+w-30,36):
                if r.random()<.3:c.rect(xx,yy,xx+14,yy+24,(255,196,90))
        x+=w+6
def clockface(c,cx,cy,r):
    c.circ(cx,cy,r+26,(120,78,44),BRW,6);c.circ(cx,cy,r,PAP,BRW,6)
    for i in range(12):
        a=i*math.pi/6;l=r*.14 if i%3 else r*.22
        c.line([(cx+math.sin(a)*(r*.9-l),cy-math.cos(a)*(r*.9-l)),(cx+math.sin(a)*r*.9,cy-math.cos(a)*r*.9)],BRW,7 if i%3==0 else 4)
    c.rect(cx-330,cy-r-30,cx+330,cy-r+10,(60,44,30));c.rect(cx-56,cy+r+16,cx+56,cy+r+52,(60,44,30))
def clockhands(im,lt,t,sec=True):
    d=ImageDraw.Draw(im);cx,cy=648,1120
    hs=(lt*6)%360;ms=(lt*.6)%360
    for ang,L,w,col in [(hs,330,16,BRW),(ms,210,22,BRW)]:
        a=math.radians(ang);d.line([(cx,cy),(cx+math.sin(a)*L,cy-math.cos(a)*L)],fill=col,width=w)
    if sec:
        sa=(t*210)%360;a=math.radians(sa)
        d.line([(cx-math.sin(a)*70,cy+math.cos(a)*70),(cx+math.sin(a)*430,cy-math.cos(a)*430)],fill=RED,width=9)
    d.ellipse([cx-18,cy-18,cx+18,cy+18],fill=GOLD,outline=BRW,width=6)
# ---------- backgrounds (static, design space 1296x2304 -> out 1296x2304) ----------
def bg_pwin():
    c=Cv([(0,(8,12,24)),(.5,(16,22,40)),(.72,(24,30,52)),(1,(7,9,18))]);c.stars(60,700,51)
    cx,cy=648,760
    glow(c.im,cx,cy,560,(90,110,150),.35)
    r=random.Random(53)
    for _ in range(3):
        x=r.uniform(120,1160);y=r.uniform(1600,2100)
        c.poly([(x,y),(x+90,y-200),(x+150,y-200),(x+60,y)],(12,16,26))
    cx2,cy2=260,980
    c.rect(cx2-300,cy2-700,cx2+300,cy2+560,(14,20,36),BRW,10,r=16)
    sc=Image.new('RGB',(600*S,1260*S),(10,15,30));sd=ImageDraw.Draw(sc)
    sd.rectangle([0,0,600*S,600*S],fill=(26,38,66))
    rr=random.Random(17)
    for _ in range(3):
        x=rr.uniform(30,540);y=rr.uniform(430,560)
        sd.ellipse([x*S,y*S,(x+80)*S,(y+26)*S],fill=(13,20,38))
        sd.ellipse([x*S,(y+18)*S,(x+80)*S,(y+44)*S],fill=(13,20,38))
    c.im.paste(sc,(cx2*S-300,(cy2-700)*S))
    windows(c,19)
    c.rect(0,2060,W,H,(16,12,10));c.rect(0,2040,W,2064,(30,20,14))
    return c.out()
def bg_bed():
    c=Cv([(0,(9,13,26)),(.55,(17,23,42)),(1,(8,10,20))]);c.stars(50,900,52);c.crescent(1060,300,56)
    c.rect(150,300,760,1050,(20,30,54),BRW,12,r=14)
    sk=Image.new('RGB',(610*S,750*S),(15,24,46));skd=ImageDraw.Draw(sk);rr=random.Random(23)
    skd.ellipse([420*S,90*S,560*S,230*S],fill=(255,232,170));skd.ellipse([465*S,120*S,590*S,245*S],fill=(15,24,46))
    for _ in range(14):x,y=rr.uniform(20,500),rr.uniform(30,600);skd.ellipse([x*S,y*S,(x+4)*S,(y+4)*S],fill=(230,235,255))
    c.im.paste(sk,(150*S,300*S));c.line([(455,300),(455,1050)],BRW,12);c.line([(150,675),(760,675)],BRW,12);c.rect(150,300,760,1050,None,BRW,12,r=14)
    c.rect(60,1180,1236,1420,(34,22,16),BRW,8,r=18)
    c.rect(100,1140,1196,1210,(15,10,8),None,0,0)
    c.ell(120,1400,600,1660,(40,26,20));c.ell(560,1370,1120,1600,(30,60,110));c.rect(560,1520,1120,1610,(26,44,80))
    c.rect(60,1600,1236,1730,(26,16,12));c.rect(160,1730,260,2060,(20,12,10),None,0,0);c.rect(1030,1730,1130,2060,(20,12,10),None,0,0)
    c.rect(0,2040,W,H,(12,8,7))
    return c.out()
def bg_street():
    c=Cv([(0,(9,13,26)),(.5,(17,24,42)),(1,(10,13,22))])
    windows(c,29)
    c.rect(0,1900,W,H,(14,16,24))
    c.poly([(430,1900),(470,1080),(860,1080),(900,1900)],(11,13,20))
    lx=648
    c.rect(lx-14,930,lx+14,1120,(22,26,38));c.ell(lx-90,820,lx+90,960,(22,26,38))
    c.circ(lx,900,34,(255,220,140));glow(c.im,lx,900,300,(255,200,110),.75*flick(1.0,2))
    c.poly([(0,2304),(240,1900),(470,1900),(360,2304)],(20,22,30))
    return c.out()
def bg_wall():
    c=Cv([(0,(28,22,18)),(.5,(44,33,26)),(1,(24,17,13))])
    glow(c.im,1050,560,420,(255,190,110),.5)
    c.rect(0,0,90,H,(22,16,12));c.rect(W-90,0,W,H,(22,16,12));c.rect(0,0,W,70,(22,16,12))
    c.rect(0,1980,W,H,(30,22,17))
    clockface(c,648,1120,430)
    c.rect(614,520,682,560,(70,50,32),None,0,0)
    return c.out()
def bg_mosque():
    c=Cv([(0,(8,14,32)),(.55,(20,32,58)),(1,(9,15,26))]);c.stars(90,1000,54);c.crescent(230,250,58)
    c.rect(0,1960,W,H,(10,14,22));c.mosque(648,1950,1.05,(12,20,34))
    for wx in (560,648,736):c.rect(wx-16,1660,wx+16,1810,(255,214,130))
    return c.out()
def bg_fort():
    c=Cv([(0,(24,20,40)),(.45,(52,40,64)),(1,(16,13,22))]);c.stars(60,800,55);c.crescent(1050,280,64)
    c.poly([(150,1600),(240,700),(320,700),(360,1600)],(14,11,22));c.poly([(950,1600),(1030,780),(1100,780),(1180,1600)],(14,11,22))
    c.rect(120,1600,1180,1760,(17,13,26))
    c.rect(470,900,830,1760,(20,15,30),BRW,0,0)
    c.rect(560,1080,740,1760,(34,24,18),None,0,0)
    c.rect(598,1130,702,1660,(46,32,22),None,0,0)
    c.rect(640,1130,648,1660,(12,9,7),None,0,0)
    c.rect(0,1740,W,H,(12,10,16))
    return c.out()
def bg_desk():
    c=Cv([(0,(24,18,14)),(.5,(40,29,22)),(1,(18,13,10))])
    glow(c.im,1010,640,430,(255,196,116),.55)
    c.rect(930,480,1090,1120,(60,42,28),BRW,8,r=20);c.rect(960,520,1060,560,(220,180,110),None,0,0)
    c.ell(930,480,1090,640,(80,56,34),BRW,8)
    glow(c.im,1010,700,300,(255,206,130),.4)
    c.rect(0,1680,W,H,(16,12,9))
    c.poly([(150,1880),(1146,1880),(1230,2140),(70,2140)],(56,40,26),BRW,6)
    c.poly([(240,1960),(1060,1960),(1105,2100),(195,2100)],(66,48,32),None,5)
    return c.out()
def bg_teacups():
    c=bg_desk if False else Cv([(0,(22,17,14)),(.5,(38,28,21)),(1,(16,12,9))])
    glow(c.im,1040,600,400,(255,196,116),.5)
    c.rect(0,1700,W,H,(16,12,9))
    c.poly([(120,1930),(1180,1930),(1240,2180),(60,2180)],(56,40,26),BRW,6)
    for cx,cy,k,cold in ((470,1880,1.0,False),(810,1930,.82,True)):
        c.ell(cx-95*k,cy-70*k,cx+95*k,cy+60*k,(250,246,236),BRW,7);c.ell(cx-80*k,cy-56*k,cx+80*k,cy+46*k,(184,108,52))
        c.ell(cx+95*k,cy-38*k,cx+150*k,cy+22*k,None,BRW,9);c.ell(cx+103*k,cy-28*k,cx+142*k,cy+12*k,(184,108,52))
        c.rect(cx-110*k,cy+56*k,cx+110*k,cy+70*k,(200,196,184),BRW,4)
        if cold:glow(c.im,cx,cy-10*k,150,(70,40,90),.25)
    return c.out()
def bg_chair():
    c=Cv([(0,(10,13,24)),(.55,(18,24,42)),(1,(9,11,20))]);c.stars(40,700,56)
    c.rect(640,260,1200,1150,(15,22,40),BRW,10,r=12)
    win=Image.new('RGB',(560*S,890*S),(20,29,52));wd=ImageDraw.Draw(win);rr=random.Random(29)
    for _ in range(3):
        x=rr.uniform(40,440);y=rr.uniform(430,520)
        wd.ellipse([x*S,y*S,(x+70)*S,(y+150)*S],fill=(13,20,38))
    c.im.paste(win,(640*S,260*S));c.rect(640,260,1200,1150,None,BRW,10,r=12);c.line([(640,700),(1200,700)],BRW,10)
    c.rect(90,1200,1190,1300,(30,20,15),BRW,8,r=10);c.rect(0,1960,W,H,(12,9,8))
    return c.out()
def bg_hour():
    c=Cv([(0,(20,16,26)),(.5,(33,26,38)),(1,(13,10,18))])
    glow(c.im,648,900,480,(255,196,116),.4)
    c.rect(0,1900,W,H,(15,11,16))
    c.poly([(500,1980),(796,1980),(770,2140),(540,2140)],(56,40,26),BRW,6)
    c.rect(516,1988,780,2004,(80,56,34))
    return c.out()
def bg_door():
    c=Cv([(0,(20,16,26)),(.55,(34,27,36)),(1,(12,10,16))])
    glow(c.im,648,620,420,(255,208,130),.4)
    c.rect(280,480,1016,2060,(44,20,12),BRW,0,0)
    for y in range(1500,2040,90):c.line([(300,y),(996,y)],(38,17,10),8)
    c.rect(560,1130,736,2060,(30,14,8),BRW,0,0)
    for yy in (1290,1690):
        c.circ(700,yy,18,(255,201,60));glow(c.im,700,yy,60,(255,201,60),.5)
    c.rect(640,2060,656,2100,(70,40,20))
    c.rect(0,2060,W,H,(10,8,12))
    return c.out()
def bg_stars():
    c=Cv([(0,(8,11,24)),(.5,(14,20,38)),(1,(7,9,18))]);c.stars(120,1700,57)
    glow(c.im,648,980,520,(40,60,100),.3)
    return c.out()
def bg_road():
    c=Cv([(0,(8,12,24)),(.5,(16,22,38)),(1,(10,13,22))]);c.stars(70,800,58);c.crescent(280,300,54)
    c.poly([(500,820),(796,820),(1060,2000),(240,2000)],(14,17,28))
    c.poly([(560,820),(736,820),(900,2000),(400,2000)],(22,27,42))
    c.rect(980,1000,1050,1720,(12,14,22));c.ell(960,900,1070,1010,(12,14,22))
    c.circ(1015,920,26,(255,214,130))
    c.line([(589,1520),(707,1520)],(60,66,86),16)
    c.rect(0,1980,W,H,(9,12,18))
    return c.out()
def bg_gate():
    c=Cv([(0,(14,11,22)),(.55,(27,21,34)),(1,(10,8,15))])
    c.rect(240,700,1056,1980,(26,14,10),BRW,0,0)
    c.ell(240,560,1056,900,(26,14,10));c.rect(220,530,1076,600,(20,11,8))
    c.rect(516,760,780,1980,(14,8,6))
    glow(c.im,648,900,220,(255,170,90),.28)
    for yy in range(860,1900,190):c.rect(516,yy,780,yy+16,(20,11,8))
    c.rect(0,1960,W,H,(8,7,12))
    return c.out()
def bg_dawn():
    c=Cv([(0,(36,28,56)),(.45,(122,74,88)),(.72,(236,138,88)),(1,(252,196,120))])
    c.circ(648,1560,130,(255,224,150));glow(c.im,648,1560,380,(255,190,100),.8)
    c.poly([(0,1900),(360,1660),(820,1800),(1296,1640),(1296,2304),(0,2304)],(40,22,26))
    c.poly([(0,2060),(500,1880),(900,2000),(1296,1880),(1296,2304),(0,2304)],(26,14,17))
    return c.out()
def bg_divan():
    c=Cv([(0,(12,14,26)),(.5,(20,24,42)),(1,(9,11,20))])
    c.rect(0,0,W,H//2,(24,30,54));c.rect(0,H//2,W,H,(15,18,32))
    c.rect(0,H//2-14,W,H//2+14,(9,11,20))
    return c.out()
def bg_candle():
    c=Cv([(0,(18,14,22)),(.55,(30,24,32)),(1,(11,9,15))])
    c.rect(0,1960,W,H,(13,10,13))
    return c.out()
def bg_moon():
    c=Cv([(0,(8,12,28)),(.5,(17,26,50)),(1,(8,11,22))]);c.stars(110,1400,59)
    c.crescent(648,560,120);glow(c.im,648,560,360,(255,232,170),.5)
    c.mosque(648,2260,1.35,(9,14,26))
    return c.out()
BG_FN={'pwin':bg_pwin,'bed':bg_bed,'street':bg_street,'wall':bg_wall,'mosque':bg_mosque,'fort':bg_fort,'desk':bg_desk,'tea':bg_teacups,'chair':bg_chair,'hour':bg_hour,'door':bg_door,'stars':bg_stars,'road':bg_road,'gate':bg_gate,'dawn':bg_dawn,'divan':bg_divan,'candle':bg_candle,'moon':bg_moon}
B={}
def gb(n):
    if n not in B:B[n]=BG_FN[n]()
    return B[n]
def anim(im,n,lt,t):
    d=ImageDraw.Draw(im)
    if n in ('pwin','street','chair','road'):
        rain(im,t,{"pwin":31,"street":32,"chair":33,"road":34}.get(n,35))
        if n=='road':glow(im,1015,920,240,(255,206,120),.5+.2*flick(t,3))
        if n=='pwin':motes(im,t,(160,180,215))
        if n=='street':glow(im,648,900,300,(255,200,110),.6+.25*flick(t,2))
    if n=='mosque' and lt<3:motes(im,t,(200,215,240))
    if n=='candle':glow(im,648,1500,300,(255,176,86),.55+.25*flick(t,7))
# ---------- cues ----------
cues=json.load(open('cues.json'))
def split_long():
    out=[]
    for a,b,t in cues:
        ws=t.split(' ')
        if len(ws)<=11 and len(t)<=75: out.append([a,b,t]);continue
        mid=len(t)/2;best=None;pos=0
        for k,w in enumerate(ws[:-1]):
            pos+=len(w)+1;sc=abs(pos-mid)-(8 if w[-1] in ',,—।' else 0)
            if best is None or sc<best[0]: best=(sc,k)
        k=best[1];t1,t2=' '.join(ws[:k+1]),' '.join(ws[k+1:]);s=a+(b-a)*len(t1)/len(t)
        out+=[[a,s-0.05,t1],[s+0.05,b,t2]]
    cues[:]=out
ORIG = [(a, b) for a, b, _ in cues]
split_long()
def ts(t):
    h=int(t//3600);m=int(t%3600//60);s=t%60
    return f'{h:02d}:{m:02d}:{int(s):02d},{int(round((s-int(s))*1000)):03d}'
open('final.srt','w',encoding='utf-8').write('\n'.join(f'{i+1}\n{ts(a)} --> {ts(b)}\n{t}\n' for i,(a,b,t) in enumerate(cues)))
HLW={'মৃত্যু','প্রস্তুত','শেষ','নিশ্চয়তা','সত্য','কুরআনে','না','তওবা','সুস্থতা','অবসর','অবহেলা','উত্তম','দরজা','পথিক','হাসান','সহিহ','স্মরণ','সময়','শেয়ার','সাবস্ক্রাইব','জানার',
'গল্প','আমল','প্রস্তুতি','প্রতারিত','গুনাহ','মাফ','ইমান','বিপদ','ফিরিয়ে','ক্ষমা','নামাজ','ভয়','স্বাদ','গ্রহণ','আল্লাহ','আজ'} 
def hlcore(w): return re.sub(r"[^\u0980-\u09FF A-Za-z0-9]","",w)
def ishl(w):
    c=hlcore(w)
    if c in HLW:return True
    if c and all(0x09E6<=ord(ch)<=0x09EF for ch in c) and len(c)<=5:return True
    return False
def shape_line(text,sz,col,stroke=0,sf=None):
    m,fb=fonts(sz,CPW);parts=[];wid=0
    for s_,k in runs(text,m,fb):
        if not s_:continue
        p,bl,pw=SM.img(k[0],s_,k[1],col,stroke,sf);parts.append((p,bl,pw));wid+=pw
    if not parts:return Image.new('RGBA',(2,2)),0
    asc=max(p.height-b for p,b,pw in parts);desc=max(b for p,b,pw in parts)
    im=Image.new('RGBA',(int(wid)+8,int(asc+desc)+8),(0,0,0,0));x=4
    for p,bl,pw in parts:im.alpha_composite(p,(x,4+asc-bl));x+=p.width
    return im,im.width
def short(t,n=88):return t if len(t)<=n else t[:n-1].rsplit(' ',1)[0]+'…'
# ---------- motion captions ----------
def build_caps(cbase=None):
    CP=[];sp=SM.w('sans7',' ',58)
    for a,b,t in cues:
        words=t.split(' ');lis=[];cur=[];cw=0
        for w in words:
            ww=tw(w,('sans7',58),('lat7',58))
            if cur and cw+sp+ww>920:lis.append(cur);cur=[];cw=0
            cur.append(w);cw+=ww+(sp if len(cur)>1 else 0)
        if cur:lis.append(cur)
        lh=86;wmax=0;wlis=[]
        for l in lis:wmax=max(wmax,sum(tw(w,('sans7',58),('lat7',58)) for w in l)+sp*(len(l)-1))
        Hh=len(lis)*lh;y0=int((cbase[len(CP)] if cbase else 1235)-Hh/2)
        for li,l in enumerate(lis):
            tot=sum(tw(w,('sans7',58),('lat7',58)) for w in l)+sp*(len(l)-1);x=(OW-tot)/2
            for w in l:
                col=YEL if ishl(w) else (255,255,255)
                im,_,_=SM.img('sans7',w,58,col,4,(16,16,20))
                wlis.append((im,int(x),int(y0+li*lh)))
                x+=tw(w,('sans7',58),('lat7',58))+sp
        CP.append({'words':wlis,'pill':((OW-wmax)/2-40,y0-34,(OW+wmax)/2+40,y0+Hh+16)})
    return CP
# ---------- overlay builders ----------
def canvas():return Image.new('RGBA',(OW,OH),(0,0,0,0))
def ov_big(main,sub='',col=YEL,szh=210):
    im=canvas()
    bi,bw=shape_line(main,szh,col,18,'2' if False else BRW)
    im.alpha_composite(bi,((OW-bi.width)//2,740-bi.height//2 if sub else 780-bi.height//2))
    if sub:
        si,sw=shape_line(sub,54,CREAM,5,'2' if False else BRW)
        im.alpha_composite(si,((OW-si.width)//2,740+bi.height//2+44))
    return ('pop',im,0,-16)
def ov_note(lines):
    szh=140+len(lines)*104;pw=880
    shad=Image.new('RGBA',(pw+76,szh+56),(0,0,0,0))
    sd=ImageDraw.Draw(shad);sd.rounded_rectangle([46,40,30+pw+16,20+szh+16],10,fill=(8,7,10,170))
    paper=Image.new('RGBA',(pw+60,szh+40),(0,0,0,0));pd=ImageDraw.Draw(paper)
    pd.rounded_rectangle([30,20,30+pw,20+szh],10,fill=PAP+(255,),outline=(150,110,60,255),width=3)
    for yy in range(20+128,20+szh-30,104):pd.line([(52,yy),(30+pw-22,yy)],fill=(110,150,180,110),width=2)
    pd.line([(30+int(pw*.15),20),(30+int(pw*.15),20+szh)],fill=(211,47,47,230),width=5)
    pimg=shad.copy();pimg.alpha_composite(paper,(8,8));pimg=pimg.rotate(3,expand=True,resample=Image.BICUBIC)
    im=canvas();px,py=(OW-pimg.width)//2,int(640-pimg.height/2)
    im.alpha_composite(pimg,(px,py))
    wlis=[];sp=SM.w('sans7',' ',54)
    for li,l in enumerate(lines):
        wds=l.split(' ');ws=[tw(w,('sans7',54),('lat7',54)) for w in wds]
        tl=sum(ws)+sp*(len(wds)-1);x=(OW-tl)/2-6
        for w in wds:
            tim,tmw=shape_line(w,54,BRW,2,None)
            wlis.append((tim,int(x),int(py+40+22+li*104)))
            x+=tw(w,('sans7',54),('lat7',54))+sp
    return ('words',wlis,None)
def ov_bub(text,red=None):
    sp=SM.w('sans7',' ',58);wds=text.split(' ');lis=[];cur=[];cw=0
    for w in wds:
        ww=tw(w,('sans7',58),('lat7',58))
        if cur and cw+sp+ww>720:lis.append(cur);cur=[];cw=0
        cur.append(w);cw+=ww+(sp if len(cur)>1 else 0)
    if cur:lis.append(cur)
    lh=92;Wb=int(max(tw(' '.join(l),('sans7',58),('lat7',58)) for l in lis)+120);Hb=len(lis)*lh+64
    bub=Image.new('RGBA',(Wb,Hb+52),(0,0,0,0));d=ImageDraw.Draw(bub)
    d.rounded_rectangle([6,6,Wb-6,Hb-6],26,fill=(255,255,255,238))
    d.polygon([(Wb/2-30,Hb-10),(Wb/2+30,Hb-10),(Wb/2,Hb+46)],fill=(255,255,255,238))
    y=40
    for l in lis:
        tot=tw(' '.join(l),('sans7',58),('lat7',58));x=(Wb-tot)/2
        for w in l:
            col=RED if red and hlcore(w)==red else (30,30,34)
            tim,tmw=shape_line(w,58,col,3,None)
            bub.alpha_composite(tim,(int(x),y));x+=tw(w,('sans7',58),('lat7',58))+sp
        y+=lh
    im=canvas();im.alpha_composite(bub,((OW-Wb)//2,700))
    return ('pop',im,0,-16)
def ov_cmp(l,r,sub=None):
    im=canvas();d=ImageDraw.Draw(im)
    d.rounded_rectangle([46,560,516,1150],28,fill=(44,40,58,238),outline=(255,210,31,150),width=6)
    d.rounded_rectangle([OW-516,560,OW-46,1150],28,fill=(24,20,36,232),outline=(255,214,130,110),width=6)
    for x0,x1 in ((520,OW-520),):
        d.polygon([(OW/2-48,470),(OW/2+48,470),(OW/2+130,1180),(OW/2-130,1180)],fill=(60,36,22,255),outline=(255,214,130,210))
        d.line([(OW/2-30,492),(OW/2+30,492)],fill=(255,214,130,240),width=9)
    t1,_=shape_line(l,66,(255,224,120,255),7,BRW)
    im.alpha_composite(t1,(50+(470-t1.width)//2,790-t1.height//2))
    t2,_=shape_line(r,66,(255,255,255,255),7,BRW)
    im.alpha_composite(t2,(int(OW-46-(470+t2.width)//2),790-t2.height//2))
    if sub:
        s2,_=shape_line(short(sub,46),44,(222,214,202,235),4,BRW)
        im.alpha_composite(s2,((OW-s2.width)//2,1250))
    return ('pop',im,0,-16)
def tick(im,x,y):
    d=ImageDraw.Draw(im)
    d.ellipse([x,y,x+62,y+62],fill=GRN+(255,))
    d.line([(x+15,y+32),(x+27,y+45)],fill=(255,255,255,255),width=8)
    d.line([(x+27,y+45),(x+48,y+16)],fill=(255,255,255,255),width=8)
def ov_list(items,title=None):
    im=canvas();rows=[]
    for i,it in enumerate(items):
        rw=920
        row=Image.new('RGBA',(rw,136),(0,0,0,0));d=ImageDraw.Draw(row)
        d.rounded_rectangle([4,6,rw-4,130],26,fill=(18,20,28,226),outline=(96,104,124,120),width=3)
        d.rounded_rectangle([28,34,78,86],12,fill=YEL+(255,))
        nb,_=shape_line(str(i+1),42,(30,30,36,255),3,YEL)
        bn=nb
        d._image.alpha_composite(nb,(30,38))
        tim,tmw=shape_line(it,52,CREAM,4,BRW)
        row.alpha_composite(tim,(112,68-tim.height//2))
        tick(row,rw-96,40)
        rows.append((row,int(500+i*182)))
    if title:
        ti,_=shape_line(title,50,YEL,6,BRW)
        shad=Image.new('RGBA',(ti.width+34,ti.height+26),(0,0,0,0))
        sd=ImageDraw.Draw(shad);sd.rounded_rectangle([6,8,ti.width+26,ti.height+18],16,fill=(16,16,22,200))
        shad.alpha_composite(ti,(14,10))
        im=canvas();im.alpha_composite(shad,((OW-shad.width)//2,330))
        out=canvas();out.alpha_composite(im);rows2=rows
        return ('items',rows,rows2,1)
    return ('items',rows,[r[1] for r in rows],0)
def ov_card(ar,ref,sub,narr=None,chip=None,chipcol=GRN):
    im=canvas();y=300
    if chip:
        ch,cw=shape_line(chip,34,CREAM,3,BRW)
        total=cw+64
        cpill=Image.new('RGBA',(total,64),(0,0,0,0));cd=ImageDraw.Draw(cpill)
        cd.rounded_rectangle([0,0,total,64],32,fill=chipcol+(240,))
        cpill.alpha_composite(ch,(32,(64-ch.height)//2))
        im.alpha_composite(cpill,((OW-total)//2,y));y+=96
    if narr:
        ni,_=shape_line(narr,40,(216,208,194,235),4,BRW)
        im.alpha_composite(ni,((OW-ni.width)//2,y));y+=ni.height+24
    if ar:
        for at in ar:
            ai=arabic.arab_img(at,76,GOLD)
            if ai.width>800:ai=ai.resize((800,int(ai.height*800/ai.width)),Image.LANCZOS)
            im.alpha_composite(ai,((OW-ai.width)//2,y));y+=ai.height+18
        d=ImageDraw.Draw(im);d.line([(OW/2-150,y+6),(OW/2+150,y+6)],fill=(255,201,60,170),width=5);y+=38
    subs=wraplines(sub,48,800)
    for ln in subs:
        si,_=shape_line(ln,46,CREAM,5,BRW)
        im.alpha_composite(si,((OW-si.width)//2,y));y+=si.height+12
    y+=16
    if ref:
        ri,_=shape_line(ref,38,GOLD,4,BRW)
        im.alpha_composite(ri,((OW-ri.width)//2,y));y+=ri.height
    y0=260;y1=min(y+40,1300)
    panel=Image.new('RGBA',(OW,y1-y0),(0,0,0,0));pd=ImageDraw.Draw(panel)
    pd.rounded_rectangle([44,0,OW-44,y1-y0],40,fill=(15,19,33,222),outline=(255,214,130,140),width=6)
    fr=canvas();fr.alpha_composite(panel,(0,y0))
    fr.alpha_composite(im)
    return ('pop',fr,0,-14)
def wraplines(txt,sz,maxw):
    m,fb=fonts(sz,CPW);sp=SM.w('sans7',' ',sz);wds=txt.split(' ');out=[];cur='';cw=0
    for w in wds:
        ww=tw(w,m,fb)
        if cur and cw+sp+ww>maxw:out.append(cur);cur=w;cw=ww
        else:
            if cur:cur+=' '+w;cw+=sp+ww
            else:cur=w;cw=ww
    if cur:out.append(cur)
    return out
def ov_cal(banned,live):
    im=canvas()
    pw=840;ph=740
    page=Image.new('RGBA',(pw+60,ph+60),(0,0,0,0));d=ImageDraw.Draw(page)
    d.rounded_rectangle([20,20,20+pw+20,20+ph+20],18,fill=PAP+(255,),outline=(150,110,60,255),width=4)
    d.rectangle([20,20,20+pw+20,150],fill=(211,47,47,255))
    mn,_=shape_line('জুন',44,PAP,3,BRW)
    page.alpha_composite(mn,((pw+40-mn.width)//2,170-mn.height//2))
    bb,_=shape_line(banned,104,(70,60,52,255),6,PAP)
    page.alpha_composite(bb,((pw+40-bb.width)//2,330))
    d.line([(110,336),(100+bb.width,468)],fill=(211,47,47,255),width=16)
    ll,_=shape_line(live,140,YEL,14,BRW)
    page.alpha_composite(ll,((pw+40-ll.width)//2,560))
    pg=page.rotate(2,expand=True,resample=Image.BICUBIC)
    sh=Image.new('RGBA',(pg.width+40,pg.height+40),(0,0,0,0))
    ImageDraw.Draw(sh).rounded_rectangle([28,28,pg.width+16,pg.height+14],18,fill=(8,7,10,170))
    sh.alpha_composite(pg,(12,10))
    im.alpha_composite(sh,((OW-sh.width)//2,620))
    return ('pop',im,0,-16)
def ov_end():
    im=canvas()
    ti,_=shape_line('জানার গল্প',150,CREAM,14,BRW)
    im.alpha_composite(ti,((OW-ti.width)//2,600))
    si,_=shape_line('ইসলামিক শিক্ষামূলক গল্প',48,(224,216,204,255),4,BRW)
    im.alpha_composite(si,((OW-si.width)//2,830))
    su,_=shape_line('সাবস্ক্রাইব  করুন',60,YEL,7,BRW)
    pw2=su.width+170
    d=ImageDraw.Draw(im)
    d.rounded_rectangle([(OW-pw2)/2,950,(OW+pw2)/2,1046],48,fill=(211,47,47,238),outline=(255,255,255,90),width=3)
    im.alpha_composite(su,((OW-su.width)//2,962))
    el,_=shape_line('ভিডিও ভালো লাগলে শেয়ার করুন',44,(214,206,192,220),4,BRW)
    im.alpha_composite(el,((OW-el.width)//2,1160))
    return ('pop',im,0,-14)
CPW='7'
def ov_note(lines):
    pw=860;szh=182+len(lines)*110
    shad=Image.new('RGBA',(pw+84,szh+70),(0,0,0,0))
    sd=ImageDraw.Draw(shad);sd.rounded_rectangle([62,54,40+pw+22,52+szh+22],12,fill=(8,7,10,170))
    paper=Image.new('RGBA',(pw+60,szh+40),(0,0,0,0));pd=ImageDraw.Draw(paper)
    pd.rounded_rectangle([30,20,30+pw,20+szh],10,fill=PAP+(255,),outline=(150,110,60,255),width=3)
    for yy in range(20+128,20+szh-30,104):pd.line([(52,yy),(30+pw-22,yy)],fill=(110,150,180,110),width=2)
    pd.line([(30+int(pw*.15),20),(30+int(pw*.15),20+szh)],fill=(211,47,47,230),width=5)
    yb=20+72
    for li,l in enumerate(lines):
        tim,_=shape_line(l,52,BRW,2,None)
        paper.alpha_composite(tim,(30+int((pw-tim.width)/2)+6,yb))
        yb+=110
    pimg=shad.copy();pimg.alpha_composite(paper,(8,8));pimg=pimg.rotate(3,expand=True,resample=Image.BICUBIC)
    im=canvas()
    ytop=int(560-pimg.height/2)
    im.alpha_composite(pimg,((OW-pimg.width)//2,ytop))
    return ('wipe',im,ytop,0.7)
def ov_list(items,title=None):
    im=canvas()
    if title:
        ti,_=shape_line(title,50,YEL,6,BRW)
        shd=Image.new('RGBA',(ti.width+40,ti.height+30),(0,0,0,0))
        sd=ImageDraw.Draw(shd);sd.rounded_rectangle([6,10,ti.width+30,ti.height+20],16,fill=(14,15,21,210))
        shd.alpha_composite(ti,(16,12))
        im.alpha_composite(shd,((OW-shd.width)//2,300))
    BD='১২৩৪'
    rows=[]
    for i,it in enumerate(items):
        rw=930
        row=Image.new('RGBA',(rw,140),(0,0,0,0));d=ImageDraw.Draw(row)
        d.rounded_rectangle([4,6,rw-4,132],26,fill=(17,19,27,228),outline=(96,104,124,130),width=3)
        d.rounded_rectangle([30,36,84,90],12,fill=YEL+(255,))
        nb,_=shape_line(BD[i],42,(30,30,36,255),3,YEL)
        row.alpha_composite(nb,((84+30-nb.width)//2,63-nb.height//2))
        tim,_=shape_line(it,50,CREAM,4,BRW)
        row.alpha_composite(tim,(128,69-tim.height//2))
        tick(row,rw-100,42)
        rows.append((row,470+i*184))
    return ('items',im,rows)
def ov_for(kind,kw):
    if kind=='big':return ov_big(kw['main'],kw.get('sub',''),kw.get('col',YEL))
    if kind=='note':return ov_note(kw['lines'])
    if kind=='bub':return ov_bub(kw['text'],kw.get('red'))
    if kind=='cmp':return ov_cmp(kw['l'],kw['r'],kw.get('sub'))
    if kind=='card':return ov_card(kw.get('ar'),kw.get('ref'),kw.get('sub',''),kw.get('narr'),kw.get('chip'),kw.get('chipcol',GRN))
    if kind=='cal':return ov_cal(kw['banned'],kw['live'])
    if kind=='list':return ov_list(kw['items'],kw.get('title'))
    if kind=='end':return ov_end()
    return None
SCENES=[
(0,1,'pwin',None,{}),
(1,2,'stars','big',{'main':'প্রস্তুত?','sub':'প্রশ্ন একটাই'}),
(2,4,'bed','note',{'lines':['আজ রাতে ঘুমাবেন,','কিন্তু সকালে উঠবেন —','এই নিশ্চয়তা কেউ দেয়নি।']}),
(4,5,'street',None,{}),
(5,6,'desk','note',{'lines':['ভয় দেখানোর জন্য নয়,','জাগিয়ে তোলার জন্য।']}),
(6,7,'wall','note',{'lines':['শেষে বলব এমন এক কথা,','যা রাতটাই বদলে দিতে পারে।']}),
(7,8,'moon','bub',{'text':'প্রথমে একটি সত্য শুনুন'}),
(8,10,'mosque','card',{'ar':['كُلُّ نَفْسٍ ذَآئِقَةُ ٱلْمَوْتِ'],'ref':'সূরা আলে ইমরান • ৩:১৮৫','sub':'প্রত্যেক প্রাণীকে মৃত্যুর স্বাদ গ্রহণ করতে হবে','chip':'প্রমাণিত — quran.com'}),
(10,12,'fort','card',{'ar':['أَيْنَ مَا تَكُونُواۖ يُدْرِككُّمُ ٱلْمَوْتُ وَلَوْ كُنتُمْ فِى بُرُوجٍ مُّشَيَّدَةٍ'],'ref':'সূরা নিসা • ৪:৭৮','sub':'যেখানেই থাকো — মৃত্যু পাকড়াও করবে, সুদৃঢ় দুর্গেও','chip':'প্রমাণিত — quran.com'}),
(12,13,'desk','big',{'main':'৪:৭৮','sub':'সুদৃঢ় দুর্গেও মৃত্যু'}),
(13,15,'divan','cmp',{'l':'ধনী','r':'গরিব','sub':'রাজা হোক বা প্রজা — পথ একটাই'}),
(15,16,'door',None,{}),
(16,17,'desk','cal',{'banned':'বয়স','live':'মৃত্যু'}),
(17,18,'tea',None,{}),
(18,19,'chair',None,{}),
(19,20,'stars','big',{'main':'নির্বিঘ্ন কেন?'}),
(20,21,'mosque','card',{'ar':['أَكْثِرُوا ذِكْرَ هَاذِمِ اللَّذَّاتِ'],'ref':'সুনানে তিরমিজি • ২৩০৭','narr':'বর্ণনায় আবু হুরায়রা (রা.)','sub':'স্বাদ নষ্টকারী মৃত্যুকে বেশি বেশি স্মরণ করো','chip':'হাসান (দারুস সালাম)','chipcol':ORG}),
(21,22,'gate','big',{'main':'২৩০৭','sub':'সুনানে তিরমিজি'}),
(22,24,'wall','note',{'lines':['মৃত্যুর স্মরণ মানে হতাশা নয় —','নিজের সময়ের দাম বোঝা শেখা।']}),
(24,25,'candle',None,{}),
(25,26,'divan','cmp',{'l':'সুস্থতা','r':'অবসর','sub':'এই দুটিকেই আমরা সবচেয়ে বেশি অবহেলা করি'}),
(26,27,'hour','card',{'ref':'সহিহ বুখারি • ৬৪১২','narr':'রাসূলুল্লাহ সাল্লাল্লাহু আলাইহি ওয়াসাল্লাম','sub':'দুটি নিয়ামতের ব্যাপারে বহু মানুষ প্রতারিত: সুস্থতা ও অবসর','chip':'সহিহ'}),
(27,29,'desk','note',{'lines':['আজ আপনি সুস্থ, হাতে সময় —','আর এই দুটিই অবহেলিত।']}),
(29,31,'wall','note',{'lines':['পরে করব…','সময় হলে করব…','আর এভাবেই সময় ফুরিয়ে যায়।']}),
(31,32,'bed',None,{}),
(32,34,'hour','bub',{'text':'আরেকটু সময় দাও।','red':'সময়','tag':'কাল্পনিক দৃশ্য'}),
(34,36,'fort','card',{'ar':['وَأَنفِقُوا۟ مِن مَّا رَزَقْنَـٰكُم مِّن قَبْلِ أَن يَأْتِىَ أَحَدَكُمُ ٱلْمَوْتُ'],'ref':'সূরা মুনাফিকুন • ৬৩:১০','sub':'মৃত্যু আসার আগেই আল্লাহ যা দিয়েছেন তার থেকে ব্যয় করো','chip':'প্রমাণিত — quran.com'}),
(36,38,'door','card',{'ar':['رَبِّ لَوْلَا أَخَّرْتَنِىٓ إِلَىٰٓ أَجَلٍ قَرِيبٍ'],'ref':'সূরা মুনাফিকুন • ৬৩:১০','sub':'হে আমার রব! আমাকে আর কিছুকাল সময় দিলে আমি দান করতাম ও নেককারদের অন্তর্ভুক্ত হতাম'}),
(38,39,'stars','big',{'main':'৬৩:১০','sub':'সূরা মুনাফিকুন'}),
(39,41,'hour','card',{'ar':['حَتَّىٰٓ إِذَا جَآءَ أَحَدَهُمُ ٱلْمَوْتُ قَالَ رَبِّ ٱرْجِعُونِ'],'ref':'সূরা মুমিনুন • ২৩:৯৯','sub':'হে আমার রব, আমাকে ফেরত পাঠান — যেন আমি সৎকাজ করতে পারি','chip':'প্রমাণিত — quran.com'}),
(41,42,'gate','big',{'main':'না।','sub':'উত্তর আসবে','col':RED}),
(42,44,'fort','note',{'lines':['“না” — কেবল সে-ই বলেছে;','এখন আর সময় নেই।','— মুমিনুন ২৩:৯৯–১০০']}),
(44,47,'divan','cmp',{'l':'ওই সময়টুকু','r':'অকারণে ফেলে','sub':'ওই মানুষটি সবকিছু দিয়ে দিত'}),
(47,48,'stars','big',{'main':'কী যাবে?','sub':'মৃত্যুর পরে আমাদের সঙ্গে'}),
(48,51,'mosque','card',{'ar':['ٱلَّذِى خَلَقَ ٱلْمَوْتَ وَٱلْحَيَاةَ لِيَبْلُوَكُمْ أَيُّكُمْ أَحْسَنُ عَمَلًا'],'ref':'সূরা মুলক • ৬৭:২','sub':'মৃত্যু ও জীবন সৃষ্টি করেছেন — কে কাজে সবচেয়ে উত্তম','chip':'প্রমাণিত — quran.com'}),
(51,52,'street','big',{'main':'বেশি নয় —','sub':'আল্লাহ বলেননি, কে সবচেয়ে বেশি'}),
(52,53,'stars','big',{'main':'উত্তম','sub':'রাসূল বলেছেন — এই পরীক্ষা'}),
(53,54,'mosque','card',{'ref':'সহিহ বুখারি • ৬৪১৬','narr':'বর্ণনায় ইবনে উমর (রা.)','sub':'মানুষ মারা গেলে তার আমল বন্ধ হয়ে যায় — তিনটি ছাড়া','chip':'সহিহ'}),
(54,58,'candle','list',{'title':'এই তিনটি চলতে থাকে','items':['সদকায়ে জারিয়া','উপকারী ইলম','নেক সন্তানের দোয়া']}),
(58,59,'hour','card',{'ref':'সহিহ মুসলিম • ১৬৩১','sub':'মৃত্যুর পর আমল বন্ধ — সেই তিনটি আমল ছাড়া','chip':'সহিহ'}),
(59,61,'dawn','note',{'lines':['আপনি না থাকলেও ভালো কাজ','আপনার হয়ে কথা বলতে থাকবে।']}),
(61,63,'road',None,{}),
(63,64,'moon','note',{'lines':['বুখারিতে ইবনে উমর (রা.) বর্ণনা করেন,','রাসূল কাঁধ ধরে বললেন:']}),
(64,65,'moon','card',{'ref':'সহিহ বুখারি • ৬৪১৬','narr':'রাসূলুল্লাহ সাল্লাল্লাহু আলাইহি ওয়াসাল্লাম','sub':'“দুনিয়াতে এমনভাবে থাকো — যেন তুমি একজন অপরিচিত অথবা পথচারী।”','chip':'সহিহ'}),
(65,66,'hour','big',{'main':'৬৪১৬','sub':'হাদিস নম্বর'}),
(66,68,'desk','note',{'lines':['“সন্ধ্যা হলে সকালের অপেক্ষা করো না,','সকাল হলে সন্ধ্যার অপেক্ষা করো না।”','— ইবনে উমর (রা.)']}),
(68,70,'door','note',{'lines':['জীবিত অবস্থায়','মৃত্যুর জন্য প্রস্তুতি নাও।']}),
(70,73,'road',None,{}),
(73,80,'candle','list',{'title':'আজ রাতে ৪ করণীয়','items':['তওবা করুন, ক্ষমা চান','হক ফিরিয়ে / ক্ষমা নিন','নামাজ নিয়মিত শুরু করুন','চিরস্থায়ী ভালো কাজ']}),
(80,82,'dawn','big',{'main':'প্রস্তুতি নেওয়ার','sub':'মৃত্যু ভয়ের জিনিস নয় — প্রস্তুতির জিনিস'}),
(82,84,'moon','note',{'lines':['ভিডিওটি শেয়ার করুন,','সাবস্ক্রাইব করুন — জানার গল্প।']}),
(84,87,'moon','list',{'title':'দোয়া করুন','items':['ইমানের সঙ্গে মৃত্যু','সব গুনাহ মাফ','শেষ দিনটি সহজ']}),
(87,88,'moon','end',{}),
]
orig=ORIG
SC=[]
for (i0,i1,bg_,kd,kw) in SCENES:
    t0=orig[i0][0]-0.05;t1=orig[i1-1][1]+0.14
    SC.append([t0,t1,bg_,kd,kw])
SC[0][0]=0.0;SC[-1][1]=DUR
for i in range(len(SC)-1):
    if SC[i][1]>SC[i+1][0]:SC[i][1]=SC[i+1][0]
SC=[(s[0],s[1],s[2],s[3],s[4]) for s in SC]
OV=[ov_for(kd,kw) for _,_,_,kd,kw in SC]
cbase=[]
for a,b,t in cues:
    tm=(a+b)/2;kb=1235
    for (t0,t1,bg_,kd,kw) in SC:
        if tm<t1:kb=1310 if kd=='card' else 1235;break
    cbase.append(kb)
CAP=build_caps(cbase)
FTAG=canvas();tim,_=shape_line('জানার গল্প',40,(245,240,228,225),4,BRW)
FTAG.alpha_composite(tim,((OW-tim.width)//2,52-tim.height//2+18))
RTAG=Image.new('RGBA',(OW,120),(0,0,0,0));rim,_=shape_line('কাল্পনিক দৃশ্য',38,CREAM,4,BRW)
pd=ImageDraw.Draw(RTAG);pw2=rim.width+76
pd.rounded_rectangle([(OW-pw2)/2,18,(OW+pw2)/2,18+62],31,fill=(211,47,47,215))
RTAG.alpha_composite(rim,((OW-rim.width)//2,49-rim.height//2))
_top=np.zeros((240,OW,4),np.uint8);_top[...,:3]=(6,7,10);_top[...,3]=np.clip(np.linspace(150,0,240)[:,None],0,255)
_btm=np.zeros((OH-1560,OW,4),np.uint8);_btm[...,:3]=(6,7,10);_btm[...,3]=np.clip(np.linspace(0,150,OH-1560)[:,None],0,255)
SAFE=Image.new('RGBA',(OW,OH),(0,0,0,0));SAFE.paste(Image.fromarray(_top),(0,0));SAFE.paste(Image.fromarray(_btm),(0,1560))
ZK={'wall':(1.04,0.09,0,-0.02),'desk':(1.05,0.08,0.02,0),'tea':(1.04,0.08,-0.02,0),'hour':(1.05,0.09,0,0.02),
'stars':(1.02,0.05,0,-0.02),'candle':(1.05,0.08,0,0),'pwin':(1.04,0.06,0.03,0),'bed':(1.05,0.07,0,0.02),
'street':(1.05,0.07,0,0),'chair':(1.04,0.06,0.02,0),'mosque':(1.04,0.06,0,-0.02),'fort':(1.05,0.07,0,0.02),
'door':(1.05,0.07,0,0),'gate':(1.04,0.06,0,0),'road':(1.05,0.08,0,-0.02),'divan':(1.05,0.06,0,0),
'dawn':(1.04,0.06,0,0.02),'moon':(1.04,0.06,0,-0.02)}
def ascale(im,a):
    m=im.copy();m.putalpha(m.getchannel('A').point(lambda v:int(v*a)));return m
def put(fr,ov,lt):
    if not ov:return
    ke=sm(lt,0.05,0.42)
    if ov[0]=='pop':
        im=ov[1];sc=1+0.22*(1-ke);dy=int(20*(1-ke))
        nw,nh=max(2,int(im.width*sc)),max(2,int(im.height*sc))
        im2=im.resize((nw,nh),Image.LANCZOS) if abs(sc-1)>0.004 else im
        fr.alpha_composite(ascale(im2,ke),(int((OW-im2.width)/2),int((OH-im2.height)/2)-dy))
    elif ov[0]=='wipe':
        h=int(ov[1].height*sm(lt,0.1,0.1+ov[3]))
        if h>1:fr.alpha_composite(ov[1].crop((0,0,ov[1].width,h)),(0,ov[2]))
    elif ov[0]=='items':
        if ov[1]:fr.alpha_composite(ascale(ov[1],ke),(0,int(24*(1-ke))))
        for j,(rimg,ry) in enumerate(ov[2]):
            rj=sm(lt,0.25+j*0.4,0.7+j*0.4)
            if rj<=0:continue
            dy=int(36*(1-rj))
            fr.alpha_composite(ascale(rimg,rj),(int((OW-rimg.width)/2),ry+dy))
camera={}
def caps_draw(fr,t):
    for i,(a,b,tl) in enumerate(cues):
        if a-0.05<=t<b+0.1:
            ca=sm(t,a,a+0.15)*(1-sm(t,b-0.02,b+0.08))
            if ca<=0:break
            cp=CAP[i];x0,y0,x1,y1=cp['pill']
            pil=Image.new('RGBA',(int(x1-x0)+2,int(y1-y0)+2),(0,0,0,0))
            ImageDraw.Draw(pil).rounded_rectangle([0,0,pil.width-1,pil.height-1],36,fill=(16,16,20,int(230*ca)))
            fr.alpha_composite(pil,(int(x0),int(y0)))
            j=0
            for wim,wx,wy in cp['words']:
                wa=sm(t,a+0.04+j*0.075,a+0.04+j*0.075+0.24)
                if wa>0:
                    sc=1+0.26*(1-wa)
                    nw,nh=max(2,int(wim.width*sc)),max(2,int(wim.height*sc))
                    w2=wim.resize((nw,nh),Image.LANCZOS) if abs(sc-1)>0.004 else wim
                    fr.alpha_composite(w2,(int(wx-(nw-wim.width)/2),int(wy-(nh-wim.height)/2)-(nw-wim.width)//3))
                j+=1
            break
def frame(t):
    i=0
    while i<len(SC)-1 and t>=SC[i][1]:i+=1
    t0,t1,bg_,kd,kw=SC[i];lt=t-t0
    im=gb(bg_).copy();anim(im,bg_,lt,t)
    z0,zk,pxk,pyk=ZK[bg_];z=z0+zk*sm(lt,0,t1-t0)
    fr=zoom(im,z,pxk*sm(lt,0,t1-t0),pyk*sm(lt,0,t1-t0)).convert('RGBA')
    put(fr,OV[i],lt)
    caps_draw(fr,t)
    if kw.get('tag'):
        ra=sm(lt,0.3,0.7);fr.alpha_composite(ascale(RTAG,ra),(0,140))
    fr.alpha_composite(FTAG,(0,0))
    F=Image.alpha_composite(fr,SAFE).convert('RGB')
    f=sm(t,0,0.6)*(1-sm(t,DUR-1.0,DUR))
    if f<1:F=Image.blend(Image.new('RGB',(OW,OH)),F,f)
    return F
if __name__=='__main__':
    if sys.argv[1]=='test':
        for t in map(float,sys.argv[2:]):frame(t).resize((540,960)).save(f't3_{t}.png')
    else:
        a,b=int(sys.argv[2]),int(sys.argv[3])
        p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{OW}x{OH}','-r','30','-i','-','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',f'part{sys.argv[1]}.mp4'],stdin=subprocess.PIPE)
        for fr_i in range(a,b):
            p.stdin.write(frame(fr_i/FPS).tobytes())
            if fr_i%300==0:print(fr_i,flush=True)
        p.stdin.close();p.wait()
