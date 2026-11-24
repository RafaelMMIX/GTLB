import xml.etree.ElementTree as ET, math, json, sys, collections
# usage: python3 build_data.py SRC.osm OUT.json [poi.json]
#   sans poi.json : points d'intérêt de Lamotte-Beuvron (intégrés) ; avec poi.json : {cle: [nom, lat, lon]}
SRC=sys.argv[1] if len(sys.argv)>1 else 'map.osm'; OUT=sys.argv[2] if len(sys.argv)>2 else 'data.json'; POIFILE=sys.argv[3] if len(sys.argv)>3 else None
r=ET.parse(SRC).getroot()
bb=r.find('bounds').attrib
lat0,lon0=((float(bb['minlat'])+float(bb['maxlat']))/2,(float(bb['minlon'])+float(bb['maxlon']))/2) if POIFILE else (47.611,2.031); kx=math.cos(lat0*math.pi/180)*111320; ky=110574
def tags(e): return {x.get('k'):x.get('v') for x in e.findall('tag')}
N={}
for n in r.iter('node'): N[n.get('id')]=((float(n.get('lon'))-lon0)*kx, -(float(n.get('lat'))-lat0)*ky)
W={}
for w in r.iter('way'): W[w.get('id')]=([x.get('ref') for x in w.findall('nd')],tags(w))
def rdp(pts,tol):
    if len(pts)<3: return pts
    keep=[False]*len(pts); keep[0]=keep[-1]=True; st=[(0,len(pts)-1)]
    while st:
        a,b=st.pop(); x1,y1=pts[a]; x2,y2=pts[b]; dx,dy=x2-x1,y2-y1; l=math.hypot(dx,dy); md=-1; mi=-1
        for i in range(a+1,b):
            d=abs((pts[i][0]-x1)*dy-(pts[i][1]-y1)*dx)/l if l else math.hypot(pts[i][0]-x1,pts[i][1]-y1)
            if d>md: md=d; mi=i
        if md>tol: keep[mi]=True; st.append((a,mi)); st.append((mi,b))
    return [p for p,k in zip(pts,keep) if k]
def flat(pts): return [int(round(c*10)) for p in pts for c in p]
def coords(ids): return [N[i] for i in ids if i in N]
CLS=['motorway','motorway_link','primary','secondary','tertiary','unclassified','residential','living_street','service','track','bridleway','path','footway','cycleway']
names=[]; nmap={}
def nid(s):
    if not s: return -1
    if s not in nmap: nmap[s]=len(names); names.append(s)
    return nmap[s]
roads=[]; drv=[]
DR={'primary','secondary','tertiary','residential','unclassified','living_street'}
for wid,(ids,t) in W.items():
    h=t.get('highway')
    if h in CLS:
        p=coords(ids)
        if len(p)<2: continue
        roads.append([CLS.index(h),nid(t.get('name','')),flat(rdp(p,0.5))])
        if h in DR or h=='service': drv.append((h,ids))
# graph (main drivable classes only)
cnt=collections.Counter()
for h,ids in drv:
    if h in DR:
        for i in ids: cnt[i]+=1
edges=set(); used=set()
for h,ids in drv:
    if h not in DR: continue
    ids=[i for i in ids if i in N]
    if len(ids)<2: continue
    keep=[0]
    for k in range(1,len(ids)-1):
        if cnt[ids[k]]>1: keep.append(k)
    keep.append(len(ids)-1)
    kk=[0]
    for a,b in zip(keep,keep[1:]):
        seg=[N[i] for i in ids[a:b+1]]
        simp=rdp(seg,1.0)
        # map simplified pts back to ids
        sel=[ids[a]]
        for p in simp[1:-1]:
            for i in ids[a:b+1]:
                if N[i]==p: sel.append(i); break
        sel.append(ids[b]); 
        for u,v in zip(sel,sel[1:]):
            if u!=v: edges.add((min(u,v),max(u,v)))
# filtre bornes
def inb(i): x,y=N[i]; return bb0[0]+10<x<bb0[2]-10 and bb0[1]+10<y<bb0[3]-10
_a=((float(bb['minlon'])-lon0)*kx, -(float(bb['maxlat'])-lat0)*ky); _b=((float(bb['maxlon'])-lon0)*kx, -(float(bb['minlat'])-lat0)*ky)
bb0=[_a[0],_a[1],_b[0],_b[1]]
edges={(u,v) for u,v in edges if inb(u) and inb(v)}
# largest component
par={}
def f(x):
    while par.setdefault(x,x)!=x: par[x]=par[par[x]]; x=par[x]
    return x
for u,v in edges: par[f(u)]=f(v)
comp=collections.Counter(f(u) for u,v in edges); big=comp.most_common(1)[0][0]
E=[(u,v) for u,v in edges if f(u)==big]
nodes=sorted({x for e in E for x in e}); idx={n:i for i,n in enumerate(nodes)}
gn=[int(round(c*10)) for n in nodes for c in N[n]]
ge=[x for u,v in E for x in (idx[u],idx[v])]
print('graph nodes',len(nodes),'edges',len(E),'components',len(comp))
# buildings, water, green, rail
bld=[];water=[];wline=[];green=[];rail=[]
GT=['forest','farmland','grass','meadow','park','pitch','playground','sports_centre','industrial','swimming_pool','scrub','grassland','flowerbed','residential','military','sports_hall','wood']
def poly_ok(ids): return len(ids)>=4 and ids[0]==ids[-1]
rels={}
for e in r.iter('relation'):
    t=tags(e)
    if t.get('type')=='multipolygon' and (t.get('landuse') or t.get('natural') or t.get('leisure')):
        outer=[m.get('ref') for m in e.findall('member') if m.get('type')=='way' and m.get('role')=='outer' and m.get('ref') in W]
        rels[e.get('id')]=(outer,t)
def chain(wids):
    segs=[list(W[w][0]) for w in wids]; rings=[]
    while segs:
        cur=segs.pop(0)
        while cur[0]!=cur[-1]:
            for i,s in enumerate(segs):
                if s[0]==cur[-1]: cur+=s[1:]; segs.pop(i); break
                if s[-1]==cur[-1]: cur+=s[::-1][1:]; segs.pop(i); break
                if s[0]==cur[0]: cur=s[::-1]+cur[1:]; segs.pop(i); break
                if s[-1]==cur[0]: cur=s+cur[1:]; segs.pop(i); break
            else: break
        if cur[0]==cur[-1]: rings.append(cur)
    return rings
relways=set()
for rid,(outer,t) in rels.items():
    k=t.get('landuse') or t.get('natural') or t.get('leisure')
    for ring in chain(outer):
        p=rdp(coords(ring),1.5)
        if k in GT and len(p)>=4: green.append([GT.index(k),flat(p)])
    relways.update(outer)
for wid,(ids,t) in W.items():
    if wid in relways: continue
    p=coords(ids)
    if t.get('building') and poly_ok(ids): 
        q=rdp(p,0.35)
        if len(q)>=4: bld.append(flat(q))
    elif t.get('natural')=='water' and poly_ok(ids): water.append(flat(rdp(p,0.5)))
    elif t.get('waterway') in ('river','canal','stream','drain') and len(p)>1: wline.append([{'river':0,'canal':1,'stream':2,'drain':3}[t['waterway']],flat(rdp(p,1.0))])
    elif t.get('railway') in ('rail','narrow_gauge') and len(p)>1: rail.append(flat(rdp(p,0.8)))
    else:
        k=t.get('leisure') or t.get('landuse') or t.get('natural')
        if k in GT and poly_ok(ids):
            q=rdp(p,1.0)
            if len(q)>=4: green.append([GT.index(k),flat(q)])
print('bld',len(bld),'water',len(water),'wline',len(wline),'rail',len(rail),'green',len(green),'roads',len(roads))
# POI
POI={'tatin':('Hôtel Tatin',-569,1870),'mairie':('Mairie',-428,1037),'gare':('Gare SNCF',-636,1902),'gendarmerie':('Gendarmerie',-510,2186),
'eglise':('Église Sainte-Anne',-534,1024),'college':('Collège Jean Rostand',-894,1713),'intermarche':('Intermarché',-346,2775),'lidl':('Lidl',-479,2798),
'carrefour':('Carrefour Market',-309,1199),'pompiers':('Pompiers',21,911),'parc':('Parc Équestre Fédéral',-1449,1047),'hopital':('Institut Médical de Sologne',-253,2181),
'mediatheque':('Médiathèque',-174,621),'boulangerie':('Boulangerie Fleury',-467,1105),'cinema':('Cinéma Le N3',-491,1579),'etang':('Étang de la Cimbaudière',-2021,1164),
'salle':('Salle omnisports',-124,453),'marche':('Place du Marché',-607,1014),'fetes':('Salle des fêtes',-400,1385),'ecole':('École Émile Morin',-344,701)}
if POIFILE:
    POI={k:(v[0],(v[2]-lon0)*kx,-(v[1]-lat0)*ky) for k,v in json.load(open(POIFILE,encoding='utf8')).items()}
segs=[]
for wid,(ids,t) in W.items():
    if t.get('highway') in DR or t.get('highway') in ('service','track','footway','cycleway','path'):
        p=coords(ids)
        for a,b in zip(p,p[1:]): segs.append((a,b))
def snap(x,y):
    best=1e18; res=None
    for (x1,y1),(x2,y2) in segs:
        dx,dy=x2-x1,y2-y1; l2=dx*dx+dy*dy; t=max(0,min(1,((x-x1)*dx+(y-y1)*dy)/l2)) if l2 else 0
        cx,cy=x1+dx*t,y1+dy*t; d=(x-cx)**2+(y-cy)**2
        if d<best: best=d; res=(cx,cy,math.atan2(dy,dx))
    return res
poi={}
for k,(nm,x,y) in POI.items():
    sx,sy,a=snap(x,y); poi[k]={'n':nm,'x':int(x*10),'y':int(y*10),'sx':int(sx*10),'sy':int(sy*10),'a':round(a,3)}
def M(la,lo): return ((lo-lon0)*kx, -(la-lat0)*ky)
a=M(float(bb['minlat']),float(bb['minlon'])); b=M(float(bb['maxlat']),float(bb['maxlon']))
bounds=[int(math.floor(min(a[0],b[0]))),int(math.floor(min(a[1],b[1]))),int(math.ceil(max(a[0],b[0]))),int(math.ceil(max(a[1],b[1])))]
def inside(fl,m=40):
    xs=fl[0::2]; ys=fl[1::2]
    return max(xs)/10>=bounds[0]-m and min(xs)/10<=bounds[2]+m and max(ys)/10>=bounds[1]-m and min(ys)/10<=bounds[3]+m
bld=[p for p in bld if inside(p)]; water=[p for p in water if inside(p)]; rail=[p for p in rail if inside(p)]
roads=[x for x in roads if inside(x[2])]; green=[g for g in green if inside(g[1])]; wline=[g for g in wline if inside(g[1])]
out={'bounds':bounds,'cls':CLS,'names':names,'roads':roads,'bld':bld,'water':water,'wline':wline,'green':green,'gt':GT,'rail':rail,'poi':poi,'gn':gn,'ge':ge}
s=json.dumps(out,ensure_ascii=False,separators=(',',':'))
open(OUT,'w',encoding='utf8').write(s); print('bytes',len(s),'bounds',bounds)
for k,v in poi.items(): print(k,v['n'],'snap dist m',round(math.hypot(v['x']-v['sx'],v['y']-v['sy'])/10))
