import json,math,random,sys,re,subprocess,unicodedata
from types import SimpleNamespace
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
def n1():
    c9=(9,14,30); c=Cv([(0,(7,11,26)),(.55,(18,26,52)),(1,c9)]);c.stars(70,1200,41);c.crescent(210,210,58,(255,232,170))
    bx=1050; c.rect(bx-560,260,bx+260,H,c9)
    c.rect(bx-560,260,bx+260,275,(24,34,58))
    for yy in range(460,2000,60):c.line([(bx-560,yy),(bx+260,yy)],(13,20,38),4)
    c.circ(bx-140,1050,430,(20,30,56),(60,74,110),10)
    for i in range(12):
        a=i*math.pi/6;c.line([(bx-140+math.sin(a)*(430-40),1050-math.cos(a)*(430-40)),(bx-140+math.sin(a)*430,1050-math.cos(a)*430)],(90,110,150),10 if i%3==0 else 5)
    c.rect(bx-560,230,bx+260,270,(30,20,14),None,0,0)
    return c.out()
def n2():
    c=Cv([(0,(10,14,28)),(.5,(24,30,54)),(1,(10,13,24))]);c.stars(60,1000,42)
    cw,ch=340,1000;cx,cy=648,1120
    glow(c.im,cx,cy,420,(255,201,60),.35)
    c.poly([(cx-cw//2,cy-ch//2-60),(cx+cw//2,cy-ch//2-60),(cx,cy+ch//2-40),(cx-90,cy-ch//2+40)],None,GOLD,0)
    c.line([(cx-cw//2,cy-ch//2-60),(cx-90,cy-ch//2+40)],GOLD,12)
    c.line([(cx+cw//2,cy-ch//2-60),(cx+90,cy-ch//2+40)],GOLD,12)
    c.line([(cx-cw//2,cy-ch//2-60),(cx+cw//2,cy-ch//2-60)],GOLD,14)
    c.line([(cx-90,cy-ch//2+40),(cx+90,cy-ch//2+40)],GOLD,12)
    c.line([(cx-90,cy-ch//2+40),(cx-90,cy+ch//2+60)],GOLD,12)
    c.line([(cx+90,cy-ch//2+40),(cx+90,cy+ch//2+60)],GOLD,12)
    c.line([(cx-cw//2,cy+ch//2+60),(cx+cw//2,cy+ch//2+60)],GOLD,14)
    c.line([(cx-90,cy+ch//2+60),(cx-cw//2,cy+ch//2+60)],GOLD,12)
    c.line([(cx+90,cy+ch//2+60),(cx+cw//2,cy+ch//2+60)],GOLD,12)
    c.rect(cx-330,cy-260,cx+330,cy-236,GOLD);c.rect(cx-250,cy+230,cx+250,cy+254,GOLD)
    return c.out()
def n3():
    c=Cv([(0,(24,15,9)),(.55,(46,29,17)),(1,(20,12,8))])
    glow(c.im,648,700,520,(255,190,90),.5)
    d=320
    c.poly([(648,1780),(648-d,1720),(648,1560),(648+d,1720)],(58,36,22),None,0)
    c.poly([(648,1560),(648-210,1640),(648,1780),(648+210,1640)],(80,52,30),None,0)
    for sx in (-1,1):
        c.poly([(648+sx*34,1080),(648+sx*470,1112),(648+sx*470,1500),(648+sx*34,1470)],(243,232,205),None,0)
        c.line([(648+sx*34,1080),(648+sx*34,1470)],(168,150,120),6)
        for k in range(7):
            c.line([(648+sx*(90+k*10),1150+k*24),(648+sx*(420-k*6),1168+k*24)],(206,188,152),4)
    c.rect(0,1900,W,H,(16,9,6))
    return c.out()
def ayahcard():
    c=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(c)
    d.rounded_rectangle([110,560,1186,1360],36,fill=(12,20,42,230),outline=GOLD,width=8)
    a1=arabic.arab_img('كُلُّ نَفْسٍ ذَآئِقَةُ ٱلْمَوْتِ',96,GOLD)
    if a1.width>960:a1=a1.resize((960,int(a1.height*960/a1.width)),Image.LANCZOS)
    c.alpha_composite(a1,(648-a1.width//2,760-a1.height//2))
    m,fb=fonts(46,'6');dtext(d,648,980,'সূরা আলে ইমরান ৩:১৮৫',m,fb,CREAM,'m')
    m,fb=fonts(40,'6');dtext(d,648,1080,'প্রত্যেক প্রাণীকে মৃত্যুর স্বাদ গ্রহণ করতে হবে',m,fb,(210,200,180),'m')
    d.line([(360,880),(936,880)],fill=GOLD,width=4)
    return c
def n4():
    c=Cv([(0,(8,14,32)),(.6,(20,34,62)),(1,(8,13,26))]);c.stars(50,1300,44);c.crescent(1060,240,52,(255,232,170))
    r=random.Random(11)
    for _ in range(14):
        x,y=r.uniform(100,1200),r.uniform(300,1900);Z=r.uniform(.5,1)
        glow(c.im,x,y,int(26*Z),(255,214,130),.5*Z)
    return c.out()
def n5():
    c=Cv([(0,(14,16,26)),(.5,(30,32,48)),(1,(16,15,24))])
    for qy in range(6):
        for qx in range(5): c.poly(None,(90,72,60)) if False else None
    r=random.Random(13)
    for _ in range(34):
        x=r.uniform(0,W);ln=r.uniform(300,700);c.line([(x,300),(x+40,300+ln)],(60,70,92),3)
    c.rect(0,1680,W,H,(20,18,26))
    c.poly([(0,1900),(360,1730),(900,1880),(W,1760),(W,H),(0,H)],(24,20,28))
    return c.out()
def figure(c,x,y,s,col):
    X,Y,Sx=x,y,s
    c.d.ellipse([X-58*Sx,Y-618*Sx,X+58*Sx,Y-502*Sx],fill=col[:3])
    c.d.polygon([(X-90*Sx,Y-480*Sx),(X+90*Sx,Y-480*Sx),(X+120*Sx,Y-40*Sx),(X-120*Sx,Y-40*Sx)],fill=col[:3])
    c.d.line([(X-70*Sx,Y-40*Sx),(X-80*Sx,Y)],fill=col[:3],width=int(20*Sx))
    c.d.line([(X+70*Sx,Y-40*Sx),(X+80*Sx,Y)],fill=col[:3],width=int(20*Sx))
def n6():
    c=Cv([(0,(7,15,30)),(.5,(16,38,56)),(1,(9,17,28))]);c.stars(80,850,46)
    glow(c.im,648,620,300,(80,220,150),.42)
    d=205
    c.poly([(648-d,1520),(648-d,1130),(648,700),(648+d,1130),(648+d,1520)],(11,24,22))
    c.rect(648-d,1500,648+d,1770,(11,24,22))
    for sx in (-1,1):
        mx=648+sx*380
        c.rect(mx-24,900,mx+24,1770,(10,20,19))
        c.ell(mx-36,820,mx+36,905,(10,20,19));c.rect(mx-36,780,mx+36,808,(13,28,25))
    c.rect(0,1750,W,H,(6,12,18))
    for wx in (560,648,736):
        c.rect(wx-20,1600,wx+20,1750,(255,220,140,66))
    return c.out()
def n7():
    c=Cv([(0,(20,16,32)),(.6,(36,28,44)),(1,(16,12,22))])
    for qy in range(9):
        c.rect(0,240+qy*230,W,252+qy*230,(30,22,36))
    for i,qx in enumerate((-1,1)):
        x=648+qx*330
        c.rect(x-60,240,x+60,1900,(26,20,34))
        c.ell(x-60,180,x+60,300,(26,20,34))
    arch(c,648,620,1400,420,(15,12,26),GOLD,9)
    glow(c.im,648,900,420,(255,208,120),.3)
    return c.out()
def n8():
    c=Cv([(0,(44,22,36)),(.45,(122,52,42)),(.75,(206,98,50)),(1,(240,142,62))])
    c.circ(648,1400,140,(255,214,130));glow(c.im,648,1400,360,(255,170,80),.8)
    c.poly([(0,1600),(430,1440),(920,1650),(W,1520),(W,H),(0,H)],(62,30,28))
    c.poly([(0,1760),(520,1620),(1040,1790),(W,1680),(W,H),(0,H)],(38,18,20))
    def camel(x,y,s,col=(18,9,11)):
        c.ell(x-40*s,y-44*s,x+40*s,y-8*s,col);c.circ(x-18*s,y-40*s,20*s,col);c.circ(x+18*s,y-40*s,20*s,col)
        c.line([(x-36*s,y-26*s),(x-52*s,y-62*s)],col,max(3,int(9*s)))
        c.ell(x-66*s,y-72*s,x-42*s,y-56*s,col)
        for lx in (-32,-20,20,32):c.line([(x+lx*s,y-12*s),(x+lx*s,y)],col,max(3,int(6*s)))
    camel(500,1590,2.0);camel(680,1620,1.7);camel(830,1650,1.45)
    return c.out()
def n9():
    c=Cv([(0,(9,12,22)),(.55,(18,24,38)),(1,(7,9,17))])
    c.poly([(500,700),(796,700),(1150,H),(146,H)],(16,20,32))
    c.poly([(600,700),(696,700),(950,H),(346,H)],(26,32,48))
    lx=796
    c.rect(lx-10,900,lx+10,1390,(12,16,28));c.rect(lx-70,860,lx+70,900,(12,16,28))
    return c.out()
def n10():
    day=Cv([(0,(30,84,120)),(1,(252,196,120))]).im
    night=Cv([(0,(8,12,30)),(1,(24,20,52))]).im
    im=Image.new('RGB',(W*S,H*S))
    im.paste(day,(0,0));im.paste(night,(W*S//2,0))
    c=Cv([(0,(0,0,0)),(1,(0,0,0))]);c.im=im;c.d=ImageDraw.Draw(im)
    r=random.Random(21)
    for _ in range(60):
        x=r.uniform(W*S//2,W*S);y=r.uniform(0,H*S*.45);c.circ(x/S,y/S,r.choice([2,2,3]),(230,230,255))
    c.crescent(1050,330,55,(255,240,200))
    c.circ(240,820,90,(255,240,190))
    c.poly([(0,2304),(400,1500),(820,1650),(W,1560),(W,H),(640,H),(640,2304)],(30,16,18))
    c.poly([(640,2304),(880,1740),(W,1900),(W,H),(640,H)],(22,12,14))
    c.line([(W//2,0),(W//2,H)],(8,10,20),8)
    return im.resize((W,H),Image.LANCZOS)
def n11():
    c=Cv([(0,(10,15,24)),(.6,(22,30,42)),(1,(8,12,20))])
    c.poly([(150,760),(1146,760),(1296,1900),(0,1900)],(26,96,86))
    c.poly([(230,840),(1066,840),(1190,1820),(106,1820)],None,GOLD,6)
    for i in range(3):
        c.line([(396,1000+i*140),(648,1060+i*140),(900,1000+i*140)],(224,206,170),5)
    for i in range(24):
        t=i/23;x=300+t*700;y=1960-200*math.sin(t*math.pi)-t*18
        c.circ(x,y,11,(242,226,190))
    c.circ(1010,1730,16,GOLD)
    return c.out()
def n12():
    c=Cv([(0,(52,26,40)),(.5,(140,62,46)),(.8,(222,110,58)),(1,(252,156,72))])
    c.circ(648,980,170,(255,220,146));glow(c.im,648,980,420,(255,178,90),.85)
    c.rect(0,1700,W,H,(30,14,14))
    for sx in (-1,1):
        mx=648+sx*330
        c.rect(mx-36,700,mx+36,1720,(24,10,12))
        c.ell(mx-52,600,mx+52,760,(24,10,12))
        c.rect(mx-56,560,mx+56,600,(30,14,14))
    c.rect(330,1320,966,1720,(24,10,12))
    c.ell(330,1150,966,1500,(24,10,12))
    c.poly([(560,1720),(736,1720),(900,2304),(400,2304)],(252,178,96))
    return c.out()
DUR=67.631
cues=json.load(open('cues.json'))
def split_long():
    out=[]
    for a,b,t in cues:
        ws=t.split(' ')
        if len(ws)<=11 and len(t)<=75: out.append([a,b,t]);continue
        mid=len(t)/2;best=None;pos=0
        for k,w in enumerate(ws[:-1]):
            pos+=len(w)+1;sc=abs(pos-mid)-(8 if w[-1] in ',,।—' else 0)
            if best is None or sc<best[0]: best=(sc,k)
        k=best[1];t1,t2=' '.join(ws[:k+1]),' '.join(ws[k+1:]);s=a+(b-a)*len(t1)/len(t)
        out+=[[a,s-0.05,t1],[s+0.05,b,t2]]
    cues[:]=out
split_long()
def ts(t):
    h=int(t//3600);m=int(t%3600//60);s=t%60;return f'{h:02d}:{m:02d}:{int(s):02d},{int(round((s-int(s))*1000)):03d}'
open('final.srt','w',encoding='utf-8').write('\n'.join(f'{i+1}\n{ts(a)} --> {ts(b)}\n{t}\n' for i,(a,b,t) in enumerate(cues)))
HL={'মৃত্যু','নিশ্চয়তা','সত্য','কুরআনে','স্বাদ','গ্রহণ','ইমরান','বয়স','জানিয়ে','পাশে','কাল','করণীয়','বুখারিতে','ইবনে','উমর','রাসূলুল্লাহ','দুনিয়াতে','থাকো','অপরিচিত','পথচারী','পথিক','বাঁধে','গন্তব্যের','প্রস্তুতি','সন্ধ্যা','সকালের','অপেক্ষা','সন্ধ্যার','ক্ষমা','তওবা','আজই','এড়াতে'}
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
            core=re.sub(r'[‘’,—?\-।,]','',w);col=GOLD if core in HL else (255,255,255)
            dtext(d,x,y,w,m,fb,col,stroke=3,sf=(20,14,10));x+=tw(w,m,fb)+sp
    return im
CAP=[cap_img(t) for _,_,t in cues]
TAG=Image.new('RGBA',(OW,90),(0,0,0,0));m,fb=fonts(38,'6');dtext(ImageDraw.Draw(TAG),OW/2,56,'জানার গল্প',m,fb,(255,243,224,190),'m')
B={}
SCENE_FN={'s1':n1,'s2':n2,'s3':n3,'s4':n4,'s5':n5,'s6':n6,'s7':n7,'s8':n8,'s9':n9,'s10':n10,'s11':n11,'s12':n12}
def bg(n):
    if n not in B:B[n]=SCENE_FN[n]()
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
SC=[('s1',0,5.6),('s2',5.6,9.5),('s3',9.5,13.2),('s4',13.2,17.6),('s5',17.6,25.2),('s6',25.2,30.5),('s7',30.5,35.3),('s8',35.3,40.5),('s9',40.5,46.1),('s10',46.1,51.7),('s11',51.7,59.6),('s12',59.6,DUR)]
CHIP=Image.new('RGBA',(OW,120),(0,0,0,0));m,fb=fonts(42,'6');dtext(ImageDraw.Draw(CHIP),OW/2,84,'সহিহ বুখারি ৬৪১৬ • বর্ণনায় ইবনে উমর (রা.)',m,fb,(255,220,140,230),'m')
def scene(n,a,b,t):
    lt=t-a;base=bg(n);im=base.copy();d=ImageDraw.Draw(im)
    if n=='s1':
        ang=(lt*40)%360;hand(d,910,1050,ang,330,14,(200,210,230));hand(d,910,1050,140,210,20,(200,210,230))
        d.ellipse([892,1032,928,1068],fill=(90,110,150));motes(im,t,(200,215,240))
        return zoom(im,1.05+.1*sm(lt,0,5.0),.15,0)
    if n=='s2':
        k=sm(lt,0,3.8);d=ImageDraw.Draw(im)
        yg=660+int(430*k);wk=int(84*(1-k))
        d.polygon([(648-wk,yg),(648+wk,yg),(648,1120)],fill=(255,206,110))
        ap=1680-260*k
        d.polygon([(648,ap),(648+84,1680),(648-84,1680)],fill=(255,206,110))
        if lt<3.6:d.line([(648,1120),(648,min(ap,1675))],fill=(255,232,150),width=8)
        return zoom(im,1.0+.12*sm(lt,0,3.9))
    if n=='s3':
        glow(im,648,700,460,(255,188,92),.45*flick(t,2));motes(im,t,(255,220,150))
        return zoom(im,1.0+.07*sm(lt,0,3.7),0,-.15)
    if n=='s4':
        card=ayahcard();a2=sm(lt,0,0.7);card.putalpha(card.getchannel('A').point(lambda v:int(v*a2)))
        im=Image.alpha_composite(im.convert('RGBA'),card).convert('RGB')
        return zoom(im,1.0+.05*sm(lt,0,4.4))
    if n=='s5':
        fig=Image.new('RGBA',(W,H),(0,0,0,0));fd=SimpleNamespace(d=ImageDraw.Draw(fig))
        figure(fd,520,1880,1.0,(30,26,36,255));figure(fd,800,1890,1.0,(40,34,44,int(255*(1-.72*sm(lt,1.5,6.5)))))
        im=Image.alpha_composite(im.convert('RGBA'),fig).convert('RGB')
        return zoom(im,1.02+.06*sm(lt,0,7.6))
    if n=='s6':
        glow(im,648,620,300,(80,220,150),.42+.18*flick(t,1));motes(im,t,(220,255,235))
        return zoom(im,1.0+.08*sm(lt,0,5.3),0,-.1)
    if n=='s7':
        sh=Image.new('RGBA',(W,H),(0,0,0,0));sd=ImageDraw.Draw(sh)
        for a_,b_ in [(500,600),(620,710),(760,860)]:
            sd.polygon([(a_,0),(b_,0),(b_+230,H),(a_+180,H)],fill=(255,206,130,80))
        sh=sh.filter(ImageFilter.GaussianBlur(36))
        im=Image.alpha_composite(im.convert('RGBA'),sh.rotate(16,center=(648,1152))).convert('RGB')
        d=ImageDraw.Draw(im);motes(im,t)
        return zoom(im,1.0+.07*sm(lt,0,4.8),0,.1)
    if n=='s8':
        return zoom(im,1.0+.09*sm(lt,0,5.2),0,.08)
    if n=='s9':
        glow(im,826,880,240,(255,188,110),.6*flick(t,4));motes(im,t,(200,215,240))
        return zoom(im,1.0+.08*sm(lt,0,5.6))
    if n=='s10':
        glow(im,230,1000,260,(255,214,120),.55);glow(im,980,1000,220,(150,140,220),.5)
        return zoom(im,1.0+.07*sm(lt,0,5.6))
    if n=='s11':
        beam=Image.new('RGBA',(W,H),(0,0,0,0));bd=ImageDraw.Draw(beam)
        bd.polygon([(540,0),(860,0),(1150,H),(240,H)],fill=(255,216,150,40))
        beam=beam.filter(ImageFilter.GaussianBlur(60)).rotate(9,center=(648,1152))
        im=Image.alpha_composite(im.convert('RGBA'),beam).convert('RGB')
        d=ImageDraw.Draw(im);motes(im,t,(255,240,200));glow(im,660,1700,330,(255,190,110),.35*flick(t,5))
        return zoom(im,1.0+.09*sm(lt,0,7.9),0,.05)
    if n=='s12':
        glow(im,648,980,430,(255,178,90),.8-.1*math.sin(t*1.2))
        return zoom(im,1.0+.07*sm(lt,0,8.0),0,-.05)
def frame(t):
    for i,(n,a,b) in enumerate(SC):
        if a<=t<b: break
    fr=scene(n,a,b,t)
    if i>0 and t<a+.5:
        pn,pa,pb=SC[i-1];fr=Image.blend(scene(pn,pa,pb,t),fr,sm(t,a,a+.5))
    fr=fr.convert('RGBA')
    if 42.6<t<44.5:
        ca=sm(t,42.62,42.85)*(1-sm(t,44.15,44.45));ch=CHIP.copy();ch.putalpha(ch.getchannel('A').point(lambda v:int(v*ca)))
        fr.alpha_composite(ch,(0,300))
    ta=sm(t,0,.5)*(1-sm(t,58.0,58.5))
    tag=TAG.copy();tag.putalpha(tag.getchannel('A').point(lambda v:int(v*ta)));fr.alpha_composite(tag,(0,90))
    for (a,b,_),ci in zip(cues,CAP):
        if a-.05<=t<=b+.1:
            k=sm(t,a,a+.18)*(1-sm(t,b-.02,b+.1));c=ci
            if k<1:c=ci.copy();c.putalpha(ci.getchannel('A').point(lambda v:int(v*k)))
            fr.alpha_composite(c,(0,1420-c.size[1]//2+60));break
    fr=fr.convert('RGB')
    f=sm(t,0,.5)*(1-sm(t,67.38,67.62))
    return frame_ret(fr,f)
def frame_ret(fr,f):
    return fr if f>=1 else Image.blend(Image.new('RGB',(OW,OH)),fr,f)
if __name__=='__main__':
    if sys.argv[1]=='test':
        for t in map(float,sys.argv[2:]): frame(t).resize((540,960)).save(f'test_{t}.png')
    else:
        a,b=int(sys.argv[2]),int(sys.argv[3]);p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{OW}x{OH}','-r','30','-i','-','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',f'part{sys.argv[1]}.mp4'],stdin=subprocess.PIPE)
        for i in range(a,b): p.stdin.write(frame(i/FPS).tobytes())
        p.stdin.close();p.wait()
