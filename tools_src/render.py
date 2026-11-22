import json,math,random,sys,re,subprocess,unicodedata
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from fontTools.ttLib import TTFont
import arabic
import shape as SM
W,H,S=1296,2304,2; OW,OH=1080,1920; FPS=30
NAVY=(20,33,61);TEAL=(31,111,120);AMB=(244,169,59);GOLD=(255,201,60);CREAM=(255,243,224);TERRA=(217,102,58);BRN=(59,36,24);CORAL=(228,87,46);GREY=(138,143,152);GREEN=(46,158,107)
def F(n,s,**k): return ImageFont.truetype(f'fonts/{n}.ttf',s,**k)
CM={n:set(TTFont(f'fonts/{n}.ttf').getBestCmap()) for n in ['sans7','sans6','lat7','lat6']}
def runs(t,m,fb):
    out=[];cur='';cf=None
    for ch in t:
        o=ord(ch)
        f=m if (o in CM[m[1]] or o in (0x200c,0x200d)) else fb
        if cf is None: cf=f
        if f is not cf: out.append((cur,cf));cur='';cf=f
        cur+=ch
    if cur: out.append((cur,cf))
    return out
def fonts(sz,w='7'): return (F('sans'+w,sz),'sans'+w),(F('lat'+w,sz),'lat'+w)
def tw(t,m,fb):
    return sum(SM.w(k[1],s,k[0].size) for s,k in runs(t,m,fb))
def dtext(d,x,y,t,m,fb,fill,anchor='l',stroke=0,sf=None):
    parts=[];w=0
    for s,k in runs(t,m,fb):
        if not s:continue
        im,bl,pw=SM.img(k[1],s,k[0].size,fill,stroke,sf)
        if len(fill)!=3:im.putalpha(im.getchannel('A').point(lambda v,a=fill[3]:int(v*a/255)))
        parts.append((im,bl));w+=pw
    if not parts:return
    if anchor=='m': x-=w/2
    d._image.paste(parts[0][0],(int(x),int(y)-parts[0][1]),parts[0][0])
    x+=parts[0][0].width
    for im,bl in parts[1:]:
        d._image.paste(im,(int(x),int(y)-bl),im);x+=im.width
class Cv:
    def __init__(s,stops):
        ys=np.linspace(0,1,H*S)[:,None]
        arr=np.zeros((H*S,1,3))
        for c in range(3): arr[:,0,c]=np.interp(ys[:,0],[p for p,_ in stops],[col[c] for _,col in stops])
        s.im=Image.fromarray(np.repeat(arr,W*S,axis=1).astype('uint8'));s.d=ImageDraw.Draw(s.im)
    def P(s,pts): return [(x*S,y*S) for x,y in pts]
    def rect(s,x0,y0,x1,y1,fill,ol=None,w=6,r=0):
        b=[x0*S,y0*S,x1*S,y1*S]
        if r: s.d.rounded_rectangle(b,r*S,fill=fill,outline=ol,width=w)
        else: s.d.rectangle(b,fill=fill,outline=ol,width=w if ol else 0)
    def ell(s,x0,y0,x1,y1,fill,ol=None,w=6): s.d.ellipse([x0*S,y0*S,x1*S,y1*S],fill=fill,outline=ol,width=w if ol else 0)
    def circ(s,x,y,r,fill,ol=None,w=6): s.ell(x-r,y-r,x+r,y+r,fill,ol,w)
    def poly(s,pts,fill,ol=None,w=6): s.d.polygon(s.P(pts),fill=fill,outline=ol,width=w if ol else 0)
    def line(s,pts,fill,w=6): s.d.line(s.P(pts),fill=fill,width=w*S,joint='curve')
    def stars(s,n,ymax,seed=1,col=(255,244,214)):
        r=random.Random(seed)
        for _ in range(n):
            x,y=r.uniform(0,W),r.uniform(0,ymax);z=r.choice([2,2,3,4]);c=tuple(int(v*r.uniform(.5,1)) for v in col)
            s.circ(x,y,z,c)
    def crescent(s,x,y,r,col):
        px=s.im.getpixel((int((x+r*1.3)*S),int((y-r*.2)*S)));s.circ(x,y,r,col);s.circ(x+r*.42,y-r*.18,r*.86,px)
    def mosque(s,cx,by,k,col):
        s.rect(cx-300*k,by-230*k,cx+300*k,by+40,col)
        s.ell(cx-190*k,by-230*k-190*k,cx+190*k,by-230*k+190*k,col)
        s.rect(cx-6*k,by-230*k-250*k,cx+6*k,by-230*k-170*k,col);s.circ(cx,by-230*k-262*k,12*k,col)
        for sx in (-1,1):
            mx=cx+sx*390*k
            s.rect(mx-26*k,by-560*k,mx+26*k,by+40,col);s.rect(mx-42*k,by-520*k,mx+42*k,by-496*k,col)
            s.poly([(mx-30*k,by-560*k),(mx+30*k,by-560*k),(mx,by-680*k)],col);s.rect(mx-3*k,by-720*k,mx+3*k,by-680*k,col)
            s.ell(mx-26*k,by-150*k,mx+26*k,by-100*k,col)
            dx=cx+sx*215*k;s.ell(dx-80*k,by-300*k,dx+80*k,by-140*k,col)
    def out(s): return s.im.resize((W,H),Image.LANCZOS)
def radial(r):
    y,x=np.mgrid[-r:r,-r:r];d=np.sqrt(x*x+y*y)/r;a=np.clip(1-d,0,1)**2
    return Image.fromarray((a*255).astype('uint8'),'L')
GL={}
def glow(im,x,y,r,col,k=1.0):
    if r not in GL: GL[r]=radial(r)
    m=GL[r].point(lambda v:int(v*min(k,1)));im.paste(Image.new('RGB',(2*r,2*r),col),(int(x-r),int(y-r)),m)
def lantern(c,cx,cy,k=1.0):
    c.line([(cx-40*k,cy-150*k),(cx,cy-230*k),(cx+40*k,cy-150*k)],BRN,6)
    c.poly([(cx-60*k,cy-150*k),(cx+60*k,cy-150*k),(cx+78*k,cy-110*k),(cx-78*k,cy-110*k)],(150,90,40),BRN,5)
    c.rect(cx-70*k,cy-110*k,cx+70*k,cy+90*k,(255,214,130),BRN,5,r=22*k)
    c.ell(cx-26*k,cy-40*k,cx+26*k,cy+40*k,(255,150,40))
    c.line([(cx-35*k,cy-110*k),(cx-35*k,cy+90*k)],BRN,3);c.line([(cx+35*k,cy-110*k),(cx+35*k,cy+90*k)],BRN,3)
    c.rect(cx-82*k,cy+90*k,cx+82*k,cy+125*k,(150,90,40),BRN,5,r=10*k)
def clockface(c,cx,cy,r):
    c.circ(cx,cy,r+26,(120,78,44),BRN,6);c.circ(cx,cy,r,CREAM,BRN,6)
    for i in range(12):
        a=i*math.pi/6;l=r*.14 if i%3 else r*.22
        c.line([(cx+math.sin(a)*(r*.9-l),cy-math.cos(a)*(r*.9-l)),(cx+math.sin(a)*r*.9,cy-math.cos(a)*r*.9)],BRN,7 if i%3==0 else 4)
def hand(d,cx,cy,ang,L,w,col):
    a=math.radians(ang);d.line([(cx,cy),(cx+math.sin(a)*L,cy-math.cos(a)*L)],fill=col,width=w)
def rug(c,pts,col,bc=GOLD):
    c.poly(pts,col,bc,8)
def arch(c,cx,top,bot,w,fill,ol,lw=7):
    c.rect(cx-w/2,top+w/2,cx+w/2,bot,fill);c.ell(cx-w/2,top,cx+w/2,top+w,fill)
    c.line([(cx-w/2,bot),(cx-w/2,top+w/2)],ol,lw);c.line([(cx+w/2,bot),(cx+w/2,top+w/2)],ol,lw)
    c.d.arc([(cx-w/2)*S,top*S,(cx+w/2)*S,(top+w)*S],180,360,fill=ol,width=lw*S)
def tasbih(c,x0,y0,n=33):
    for i in range(n):
        t=i/(n-1);x=x0+t*420;y=y0+math.sin(t*math.pi)*-70+t*30
        c.circ(x,y,13,(240,224,190),BRN,3)
    c.circ(x0+420,y0+30,17,GOLD,BRN,3)
def sc1():
    c=Cv([(0,(18,30,56)),(.5,(26,46,78)),(.56,(45,28,20)),(1,(30,18,12))])
    c.rect(300,300,740,880,(12,20,40),BRN,10,r=18)
    win=Image.new('RGB',(440*S,580*S),(30,52,92));wd=ImageDraw.Draw(win)
    r=random.Random(5)
    for _ in range(30): x,y=r.uniform(0,440),r.uniform(0,400);wd.ellipse([x*S-2,y*S-2,x*S+2,y*S+2],fill=(255,244,214))
    wd.ellipse([260*S,70*S,350*S,160*S],fill=(255,236,190));wd.ellipse([285*S,58*S,375*S,148*S],fill=(30,52,92))
    c.im.paste(win,(300*S,300*S));c.rect(300,300,740,880,None,BRN,10,r=18)
    c.line([(520,300),(520,880)],BRN,8);c.line([(300,590),(740,590)],BRN,8)
    clockface(c,1000,520,105)
    c.rect(820,720,1220,1390,(120,70,40),BRN,8,r=12);c.rect(870,780,1170,1340,(104,58,32),BRN,5,r=8);c.circ(1130,1080,16,GOLD,BRN,4)
    c.rect(140,1410,760,1450,(150,96,56),BRN,6,r=8);c.rect(180,1450,214,1790,(110,66,38),BRN,5);c.rect(686,1450,720,1790,(110,66,38),BRN,5)
    c.rect(420,1290,560,1410,CREAM,BRN,6,r=30);c.d.arc([540*S,1310*S,610*S,1380*S],-90,90,fill=BRN,width=7*S);c.ell(420,1270,560,1310,(120,70,40),BRN,6)
    for x in (880,1010):
        c.ell(x,1370,x+110,1470,(190,140,70),BRN,6);c.ell(x+20,1390,x+80,1450,(230,190,120),BRN,4)
    c.rect(0,1470,W,1480,(20,12,8))
    return c.out()
def sc2():
    c=Cv([(0,(12,24,52)),(.5,(22,70,88)),(1,(14,30,44))]);c.stars(80,1000,2)
    r=random.Random(7);x=0
    while x<W:
        w=r.randint(90,170);h=r.randint(320,760);c.rect(x,H-h-120,x+w,H-120,(10,20,32))
        for yy in range(H-h-90,H-160,70):
            for xx in range(x+16,x+w-30,38):
                if r.random()<.35:c.rect(xx,yy,xx+16,yy+26,(255,200,90))
        x+=w+6
    c.rect(0,H-130,W,H,(8,14,22));clockface(c,648,980,360)
    return c.out()
def sc3():
    c=Cv([(0,(10,18,40)),(.6,(24,60,84)),(1,(12,22,36))]);c.stars(90,1100,9);c.crescent(1020,300,70,(255,232,170))
    c.mosque(648,1500,1.0,(10,18,30));c.rect(0,1480,W,H,(10,16,26))
    c.line([(420,2060),(648,1760),(876,2060)],(120,76,44),22);c.line([(876,2060),(648,1760),(420,2060)],(150,96,56),22)
    c.poly([(380,1700),(648,1740),(916,1700),(930,1930),(648,1980),(366,1930)],(250,238,208),BRN,7);c.line([(648,1740),(648,1980)],BRN,6)
    for yy in range(1770,1930,34):
        c.line([(430,yy),(620,yy+8)],(205,180,130),4);c.line([(676,yy+8),(870,yy)],(205,180,130),4)
    c.poly([(366,1930),(648,1980),(930,1930),(930,1960),(648,2010),(366,1960)],(30,110,100),BRN,6)
    return c.out()
def sc4():
    c=Cv([(0,(16,28,60)),(.45,(60,48,80)),(.62,(214,120,70)),(.63,(60,36,34)),(1,(30,18,18))]);c.stars(60,900,4);c.crescent(900,420,95,(255,232,170))
    for i,(col,y0) in enumerate([((74,44,40),1480),((52,32,32),1640),((34,20,22),1820)]):
        pts=[(0,H)]+[(x,y0+math.sin(x/190+i*2)*70+math.sin(x/70+i)*18) for x in range(0,W+60,60)]+[(W,H)];c.poly(pts,col)
    return c.out()
def sc6():
    c=Cv([(0,(8,18,40)),(.45,(20,70,82)),(.7,(12,36,46)),(1,(8,16,22))]);c.stars(50,700,6)
    c.poly([(560,1000),(736,1000),(1296,H),(0,H)],(22,34,40))
    c.poly([(600,1000),(696,1000),(1000,H),(300,H)],(40,56,60))
    r=random.Random(3)
    for sx in (-1,1):
        for i in range(6):
            x=648+sx*(150+i*95+r.randint(-20,20));y=1000+i*60
            c.rect(x-9-i*3,y-380-i*50,x+9+i*3,y+80,(8,14,20))
            for j in range(5):c.poly([(x,y-380-i*50+j*40),(x+sx*(130+i*20),y-420-i*50+j*40),(x+sx*10,y-340-i*50+j*40+30)],(8,14,20))
    lantern(c,648,1620,1.2)
    return c.out()
def sc7():
    c=Cv([(0,(10,18,40)),(.7,(18,44,66)),(1,(10,18,28))]);c.stars(80,1100,12);c.crescent(1030,260,60,(255,232,170));c.mosque(648,1750,1.1,(8,14,24));c.rect(0,1730,W,H,(8,12,20))
    c.rect(120,560,1176,1500,(18,30,56),GOLD,8,r=36)
    d=c.d
    def T(y,t,sz,col,w='6'):
        a,b=fonts(sz,w);dtext(d,648*S,y*S,t,(ImageFont.truetype(f'fonts/sans{w}.ttf',sz*S),'sans'+w),(ImageFont.truetype(f'fonts/lat{w}.ttf',sz*S),'lat'+w),col,'m')
    T(680,'\u09a6\u09cb\u09af\u09bc\u09be \u0995\u09ac\u09c1\u09b2\u09c7\u09b0 \u09a4\u09bf\u09a8 \u09aa\u09a5',64,GOLD,'7');c.line([(310,730),(986,730)],GOLD,4)
    T(830,'\u098f\u0995 \u2014 \u09a6\u09c1\u09a8\u09bf\u09af\u09bc\u09be\u09a4\u09c7\u0987 \u09a6\u09cd\u09b0\u09c1\u09a4 \u0995\u09ac\u09c1\u09b2',54,CREAM)
    T(920,'\u09a6\u09c1\u0987 \u2014 \u0986\u0996\u09bf\u09b0\u09be\u09a4\u09c7\u09b0 \u099c\u09a8\u09cd\u09af \u099c\u09ae\u09be',54,CREAM)
    T(1010,'\u09a4\u09bf\u09a8 \u2014 \u09b8\u09ae\u09be\u09a8 \u09ac\u09bf\u09aa\u09a6 \u09b8\u09b0\u09bf\u09af\u09bc\u09c7 \u09a6\u09c7\u0993\u09af\u09bc\u09be',54,CREAM)
    T(1130,'\u09ac\u09b0\u09cd\u09a3\u09a8\u09be\u09af\u09bc: \u0986\u09ac\u09c1 \u09b8\u09be\u0988\u09a6 \u0996\u09c1\u09a6\u09b0\u09bf \u0993 \u0989\u09ae\u09b0 (\u09b0\u09be.)',44,(210,200,180))
    T(1210,'\u09ae\u09c1\u09b8\u09a8\u09be\u09a6\u09c7 \u0986\u09b9\u09ae\u09be\u09a6 \u2022 \u09b8\u09b9\u09bf\u09b9\u09c1\u09b2 \u09a4\u09be\u09b0\u0997\u09bf\u09ac',50,GREEN)
    T(1290,'\u099c\u09ac\u09be\u09ac\u09c7 \u09a4\u09bf\u09a8\u09bf \u09ac\u09b2\u09b2\u09c7\u09a8: \u0986\u09b2\u09cd\u09b2\u09be\u09b9 \u0986\u09b0\u0993 \u09ac\u09c7\u09b6\u09bf \u09a6\u09c7\u09a8',40,(210,200,180))
    return c.out()
def sc8():
    c=Cv([(0,(14,18,36)),(.55,(30,26,40)),(.56,(48,30,20)),(1,(26,16,12))])
    arch(c,648,360,1000,500,(22,26,50),GOLD,8);c.stars(25,700,8)
    for x in (130,1166):c.rect(x-26,300,x+26,1280,(60,44,40),BRN,6)
    rug(c,[(240,2200),(1056,2200),(930,1360),(366,1360)],(24,92,84))
    c.poly([(300,2140),(996,2140),(900,1420),(396,1420)],None,GOLD,6)
    arch(c,648,1480,1800,260,(18,70,66),GOLD,6);tasbih(c,780,2030)
    lantern(c,1070,1380,0.9)
    return c.out()
def sc9():
    c=Cv([(0,(48,34,34)),(.62,(78,52,40)),(.63,(60,38,26)),(1,(34,22,16))])
    sky=Cv([(0,(40,60,110)),(.5,(236,150,90)),(1,(255,214,140))]).im.resize((W*S//2,H*S//2))
    mask=Image.new('L',(W*S,H*S),0);md=ImageDraw.Draw(mask);md.rectangle([310*S,420*S,986*S,1180*S],fill=255);md.ellipse([310*S,100*S,986*S,740*S],fill=255)
    c.im.paste(sky.resize((W*S,H*S)),(0,0),mask)
    c.d.arc([310*S,100*S,986*S,740*S],180,360,fill=BRN,width=14*S);c.line([(310,420),(310,1180)],BRN,14);c.line([(986,420),(986,1180)],BRN,14);c.line([(310,1180),(986,1180)],BRN,18)
    c.line([(648,100),(648,1180)],BRN,10);c.line([(310,700),(986,700)],BRN,10)
    rug(c,[(300,2200),(996,2200),(900,1500),(396,1500)],(24,92,84));arch(c,648,1570,1900,240,(18,70,66),GOLD,6)
    im=c.out().convert('RGBA');ov=Image.new('RGBA',(W,H),(0,0,0,0));od=ImageDraw.Draw(ov)
    for a,b in [(330,450),(520,640),(700,830)]:
        od.polygon([(a,1180),(b,1180),(b+360,2200),(a-340,2200)],fill=(255,206,130,48))
    return Image.alpha_composite(im,ov).convert('RGB')
def ayahcard():
    c=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(c)
    d.rounded_rectangle([110,420,1186,1120],36,fill=(14,24,48,225),outline=GOLD,width=8)
    a1=arabic.arab_img('\u0648\u064e\u0625\u0650\u0630\u064e\u0627 \u0633\u064e\u0623\u064e\u0644\u064e\u0643\u064e \u0639\u0650\u0628\u064e\u0627\u062f\u0650\u064a \u0639\u064e\u0646\u0651\u0650\u064a \u0641\u064e\u0625\u0650\u0646\u0651\u0650\u064a \u0642\u064e\u0631\u0650\u064a\u0628\u064c',86,GOLD)
    a2=arabic.arab_img('\u0623\u064f\u062c\u0650\u064a\u0628\u064f \u062f\u064e\u0639\u0652\u0648\u064e\u0629\u064e \u0671\u0644\u062f\u0651\u064e\u0627\u0639\u0650 \u0625\u0650\u0630\u064e\u0627 \u062f\u064e\u0639\u064e\u0627\u0646\u0650',96,(255,224,130))
    if a1.width>960: a1=a1.resize((960,int(a1.height*960/a1.width)),Image.LANCZOS)
    if a2.width>960: a2=a2.resize((960,int(a2.height*960/a2.width)),Image.LANCZOS)
    c.alpha_composite(a1,(648-a1.width//2,540-a1.height//2))
    c.alpha_composite(a2,(648-a2.width//2,730-a2.height//2))
    m,fb=fonts(52,'6');dtext(d,648,920,'\u09b8\u09c2\u09b0\u09be \u0986\u09b2-\u09ac\u09be\u0995\u09be\u09b0\u09be \u09e8:\u09e7\u09ee\u09ec',m,fb,CREAM,'m')
    m,fb=fonts(38,'6');dtext(d,648,1010,'\u0986\u09ae\u09bf \u0995\u09be\u099b\u09c7\u0987 \u0986\u099b\u09bf, \u09a1\u09be\u0995\u09b2\u09c7 \u09b8\u09be\u09a1\u09bc\u09be \u09a6\u09bf\u0987',m,fb,(210,200,180),'m')
    return c
DUR=53.786
cues=json.load(open('cues.json'))
def split_long():
    out=[]
    for a,b,t in cues:
        ws=t.split(' ')
        if len(ws)<=11 and len(t)<=75: out.append([a,b,t]);continue
        mid=len(t)/2;best=None;pos=0
        for k,w in enumerate(ws[:-1]):
            pos+=len(w)+1;sc=abs(pos-mid)-(8 if w[-1] in ',,\u0964\u2014' else 0)
            if best is None or sc<best[0]: best=(sc,k)
        k=best[1];t1,t2=' '.join(ws[:k+1]),' '.join(ws[k+1:]);s=a+(b-a)*len(t1)/len(t)
        out+=[[a,s-0.05,t1],[s+0.05,b,t2]]
    cues[:]=out
split_long()
def ts(t):
    h=int(t//3600);m=int(t%3600//60);s=t%60;return f'{h:02d}:{m:02d}:{int(s):02d},{int(round((s-int(s))*1000)):03d}'
open('final.srt','w',encoding='utf-8').write('\n'.join(f'{i+1}\n{ts(a)} --> {ts(b)}\n{t}\n' for i,(a,b,t) in enumerate(cues)))
HL={'\u09a6\u09cb\u09af\u09bc\u09be','\u0995\u09ac\u09c1\u09b2','\u09a4\u09bf\u09a8','\u09ad\u09be\u09ac\u09c7','\u0995\u09b0\u09c7\u0993','\u09ac\u09a6\u09b2\u09be\u09af\u09bc\u09a8\u09bf','\u0995\u09ac\u09c1\u09b2\u0987','\u09b9\u09af\u09bc\u09a8\u09bf','\u09b0\u09be\u09b8\u09c2\u09b2\u09c1\u09b2\u09cd\u09b2\u09be\u09b9','\u09ac\u09b2\u09c7\u099b\u09c7\u09a8','\u09ae\u09c1\u09b8\u09b2\u09bf\u09ae','\u0997\u09c1\u09a8\u09be\u09b9','\u0986\u09a4\u09cd\u09ae\u09c0\u09af\u09bc\u09a4\u09be','\u099b\u09bf\u09a8\u09cd\u09a8','\u0986\u09b2\u09cd\u09b2\u09be\u09b9','\u09a4\u09bf\u09a8\u099f\u09bf\u09b0','\u09a6\u09c7\u09a8','\u09a6\u09c1\u09a8\u09bf\u09af\u09bc\u09be\u09a4\u09c7\u0987','\u09a6\u09cd\u09b0\u09c1\u09a4','\u0986\u0996\u09bf\u09b0\u09be\u09a4\u09c7\u09b0','\u099c\u09ae\u09be','\u09b8\u09ae\u09be\u09a8','\u09ac\u09bf\u09aa\u09a6','\u09b8\u09b0\u09bf\u09af\u09bc\u09c7','\u09b8\u09be\u09b9\u09be\u09ac\u09bf\u09b0\u09be','\u0986\u09b0\u0993','\u09ac\u09c7\u09b6\u09bf','\u0989\u09a4\u09cd\u09a4\u09b0','\u09a6\u09c7\u0996\u09c7\u09a8\u09a8\u09bf','\u09ac\u09be\u0981\u099a\u09bf\u09af\u09bc\u09c7\u099b\u09c7','\u09aa\u09c1\u0981\u099c\u09bf','\u09a8\u09bf\u099c\u09c7\u0987','\u09ac\u09b2\u09c7\u099b\u09c7','\u0995\u09be\u099b\u09c7\u0987','\u0986\u099b\u09bf','\u09a1\u09be\u0995\u09b2\u09c7','\u09b8\u09be\u09a1\u09bc\u09be','\u09a6\u09bf\u0987','\u0995\u09c1\u09b0\u0986\u09a8\u09c7'}
def cap_img(t):
    m,fb=fonts(62);sp=SM.w('sans7',' ',62);words=t.split(' ')
    lines=[];cur=[];cw=0
    for w in words:
        ww=tw(w,m,fb)
        if cur and cw+sp+ww>900: lines.append(cur);cur=[];cw=0
        cur.append(w);cw+=ww+(sp if len(cur)>1 else 0)
    lines.append(cur);lh=96;h=len(lines)*lh+50
    im=Image.new('RGBA',(OW,h),(0,0,0,0));d=ImageDraw.Draw(im)
    wmax=max(sum(tw(w,m,fb) for w in l)+sp*(len(l)-1) for l in lines)
    d.rounded_rectangle([OW/2-wmax/2-36,0,OW/2+wmax/2+36,h-6],34,fill=(8,12,24,150))
    for i,l in enumerate(lines):
        tot=sum(tw(w,m,fb) for w in l)+sp*(len(l)-1);x=OW/2-tot/2;y=i*lh+82
        for w in l:
            core=re.sub(r'[\u2018\u2019,\u0964\u2014?\-]','',w);col=GOLD if core in HL else (255,255,255)
            dtext(d,x,y,w,m,fb,col,stroke=3,sf=(20,14,10));x+=tw(w,m,fb)+sp
    return im
CAP=[cap_img(t) for _,_,t in cues]
TAG=Image.new('RGBA',(OW,90),(0,0,0,0));m,fb=fonts(38,'6');dtext(ImageDraw.Draw(TAG),OW/2,56,'\u099c\u09be\u09a8\u09be\u09b0 \u0997\u09b2\u09cd\u09aa',m,fb,(255,243,224,190),'m')
B={}
SCENE_FN={'s1':sc1,'s2':sc2,'s3':sc3,'s4':sc4,'s5':sc7,'s6':sc6,'s7':sc8,'s8':None}
def bg(n):
    if n not in B:
        if n=='s8':B[n]=(sc9(),ayahcard())
        else:B[n]=SCENE_FN[n]()
    return B[n]
def sm(x,a,b): return min(1,max(0,(x-a)/(b-a)))
MOTES=[(random.Random(i).uniform(0,W),random.Random(i+99).uniform(900,2200),random.Random(i+5).uniform(.3,1)) for i in range(26)]
def motes(im,t,c=(255,226,170)):
    d=ImageDraw.Draw(im)
    for x,y,s in MOTES:
        yy=(y-t*18*s)%1300+900;xx=x+math.sin(t*.6+s*9)*22;d.ellipse([xx-2,yy-2,xx+2,yy+2],fill=c)
def flick(t,s=0): return .78+.22*math.sin(t*7+s)*math.sin(t*3.1+1)
def zoom(im,z,px=0,py=0):
    cw,ch=W/z,H/z;x0=(W-cw)/2+px*(W-cw)/2;y0=(H-ch)/2+py*(H-ch)/2
    return im.resize((OW,OH),Image.BILINEAR,box=(x0,y0,x0+cw,y0+ch))
SC=[('s1',0,4.9),('s2',4.9,11.6),('s3',11.6,20.6),('s4',20.6,27.0),('s5',27.0,35.6),('s6',35.6,41.0),('s7',41.0,49.3),('s8',49.3,DUR)]
def scene(n,a,b,t):
    lt=t-a;base=bg(n)
    if n=='s8': im=base[0].copy()
    else: im=base.copy()
    d=ImageDraw.Draw(im)
    if n=='s1':
        glow(im,490,1330,330,(255,170,70),.5*flick(t))
        for i in range(3):
            pts=[(490+math.sin(lt*2+k*.5+i)*(10+k*2)+(i-1)*28,1260-k*22) for k in range(10)];d.line(pts,fill=(210,215,225),width=6)
        hand(d,1000,520,lt*6,86,4,BRN);hand(d,1000,520,270,60,9,BRN);hand(d,1000,520,15,80,9,BRN)
        motes(im,t);z=1.0+.08*sm(lt,0,2.6);return zoom(im,z+.1,.2,.1)
    if n=='s2':
        pr=sm(lt,0,5.4);ang=6*360*(1-(1-pr)**3)+10;cx,cy=648,980
        glow(im,cx,cy,520,(255,201,60),.25+.3*sm(lt,5.0,6.0))
        hand(d,cx,cy,ang,290,11,BRN);hand(d,cx,cy,300,190,17,BRN);d.ellipse([cx-18,cy-18,cx+18,cy+18],fill=BRN)
        return zoom(im,1.02+.08*sm(lt,0,6.2))
    if n=='s3':
        glow(im,648,1740,380,(255,190,90),.5*flick(t,2));motes(im,t,(255,220,150))
        return zoom(im,1.0+.07*sm(lt,0,9.0),0,-.2*sm(lt,0,9.0))
    if n=='s4':
        glow(im,900,420,300,(255,232,170),.35);motes(im,t,(255,240,210));return zoom(im,1.0+.1*sm(lt,0,5.8),-.1,0)
    if n=='s5':
        return zoom(im,1.06+.04*sm(lt,0,8.6))
    if n=='s6':
        k=flick(t,1);glow(im,648,1620,560,(255,170,60),.55*k+.25*sm(lt,0,3.4));glow(im,648,1630,200,(255,214,130),.8*k)
        for i in range(3):
            off=(t*40*(i+1))%W;fog=Image.new('RGB',(W,160),(70,110,120));m=Image.new('L',(W,160),0);ImageDraw.Draw(m).ellipse([-200+off,10,500+off,150],fill=55);ImageDraw.Draw(m).ellipse([-200+off-W,10,500+off-W,150],fill=55)
            im.paste(fog,(0,1200+i*160),m.filter(ImageFilter.GaussianBlur(30)))
        return zoom(im,1.0+.14*sm(lt,0,5.4),0,.2)
    if n=='s7':
        glow(im,1070,1380,380,(255,170,70),.55*flick(t,3));glow(im,648,600,520,(255,190,110),.15+.1*math.sin(t*.8));motes(im,t)
        return zoom(im,1.0+.1*sm(lt,0,8.3),0,.25)
    if n=='s8':
        motes(im,t,(255,240,200));glow(im,648,600,520,(255,190,110),.18+.12*math.sin(t*.8))
        card=base[1].copy();a2=sm(t,52.75,53.35);card.putalpha(card.getchannel('A').point(lambda v:int(v*a2)));im.paste(card,(0,0),card)
        return zoom(im,1.0+.08*sm(lt,0,4.4),0,.1)
def frame(t):
    for i,(n,a,b) in enumerate(SC):
        if a<=t<b: break
    fr=scene(n,a,b,t)
    if i>0 and t<a+.5:
        pn,pa,pb=SC[i-1];fr=Image.blend(scene(pn,pa,pb,t),fr,sm(t,a,a+.5))
    fr=fr.convert('RGBA')
    ta=sm(t,0,.5)*(1-sm(t,50.9,51.4))
    tag=TAG.copy();tag.putalpha(tag.getchannel('A').point(lambda v:int(v*ta)));fr.alpha_composite(tag,(0,90))
    for (a,b,_),ci in zip(cues,CAP):
        if a-.05<=t<=b+.1:
            k=sm(t,a,a+.18)*(1-sm(t,b-.02,b+.1));c=ci
            if k<1:c=ci.copy();c.putalpha(ci.getchannel('A').point(lambda v:int(v*k)))
            fr.alpha_composite(c,(0,1420-c.size[1]//2+60));break
    fr=fr.convert('RGB')
    f=sm(t,0,.5)*(1-sm(t,53.55,53.78))
    return fr if f>=1 else Image.blend(Image.new('RGB',(OW,OH)),fr,f)
if __name__=='__main__':
    if sys.argv[1]=='test':
        for t in map(float,sys.argv[2:]): frame(t).resize((540,960)).save(f'test_{t}.png')
    else:
        a,b=int(sys.argv[2]),int(sys.argv[3]);p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{OW}x{OH}','-r','30','-i','-','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',f'part{sys.argv[1]}.mp4'],stdin=subprocess.PIPE)
        for i in range(a,b): p.stdin.write(frame(i/FPS).tobytes())
        p.stdin.close();p.wait()
