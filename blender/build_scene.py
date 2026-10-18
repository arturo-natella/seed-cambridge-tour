"""SEED: one dimensioned Blender master, a GLB, and four coordinated stills.
Run: Blender --background --python tour/blender/build_scene.py
No downloaded assets. Everything is generated locally from layout.json.
"""
import bpy, math, json, random, os, sys
from pathlib import Path
from mathutils import Vector, Matrix
from collections import defaultdict
ROOT=Path(__file__).resolve().parent.parent
L=json.loads((ROOT/'blender/layout.json').read_text())
random.seed(1842)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
scene['revision']=L['revision']; scene['dimension_status']=L['dimension_status']
M={}; batches={}; groups={}; inventory=[]; connection_routes=[]; rotor_origins={}
def mat(name,hex,rough=.65,metal=0,alpha=1):
    c=tuple(int(hex[i:i+2],16)/255 for i in (0,2,4))
    # Blender inputs are linear; convert the design's sRGB swatches.
    c=tuple(v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in c)
    m=bpy.data.materials.new(name); m.diffuse_color=(*c,alpha); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*c,alpha)
    p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    p.inputs['Alpha'].default_value=alpha
    if alpha<1: m.surface_render_method='DITHERED'
    M[name]=m; return m
for args in [('grass','8FA35B'),('meadow','8FA35B'),('earth','80705A'),('till','B49D7D'),('rock','686B68'),('asphalt','656A68'),('concrete','BFBAB0'),('gravel','A59C8E'),('wall','C9C6BF'),('wood','B07A45'),('timber','D9B38C'),('roof','B9BCBF'),('charcoal','3A3D40'),('steel','A7ADB2',.4,.65),('silver','D9D9D9',.3,.7),('panel','1B2430',.25,.3),('panelGrid','465565',.3,.45),('white','E6E8EA',.42,.15),('black','141C21',.45),('rack','20282D',.4,.4),('network','394145',.5,.3),('blue','378ADD',.3,.2),('warm','D85A30',.4,.2),('led','52B6DC',.2),('glass','89ADB1',.14,.25,.26),('leaf','58733E'),('leafLight','809152'),('leafGold','B6934B'),('leafRust','9B613A'),('snow','EFF1EC'),('line','DEDCCB'),('red','AB5545'),('sign','E8E5D8')]: mat(*args)
mat('powerAmber','E9AF35',.38,.18);mat('cableTray','CBD0CD',.7,.1)
mat('batteryFace','607362',.6,.1);mat('groundPipe','8C9894',.7,.1)
mat('bypassYellow','E8B53A',.4,.2);mat('freezeActuator','304E68',.5,.15);mat('drainJacket','DBDDD5',.65,.08);mat('drainBand','81619A',.5,.08);mat('coldJacket','F0F0E8',.55,.08);mat('sensorScreen','405E58',.35,.1)
# Fire water and heat-carrying coolant must remain visually distinct.
M['red'].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.5,.008,.025,1)
M['red'].diffuse_color=(.5,.008,.025,1)
# Gentle procedural surface detail for the Blender renders. Base colors export to GLB.
for name,scale,strength in [('grass',.9,.25),('meadow',1.6,.32),('concrete',2,.12),('gravel',4,.45),('wood',3,.18),('earth',1,.25),('rock',.4,.35),('asphalt',4,.18)]:
    m=M[name]; nt=m.node_tree; p=nt.nodes.get('Principled BSDF')
    noise=nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=scale
    bump=nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=strength; bump.inputs['Distance'].default_value=.09
    nt.links.new(noise.outputs['Fac'],bump.inputs['Height']); nt.links.new(bump.outputs['Normal'],p.inputs['Normal'])

def group(key):
    if key not in groups:
        obj=bpy.data.objects.new(key,None); scene.collection.objects.link(obj); obj['objectId']=key; groups[key]=obj
    return groups[key]
def geom(key,material,verts,faces):
    b=batches.setdefault((key,material),[[],[]]); n=len(b[0]); b[0].extend(verts); b[1].extend([tuple(n+i for i in f) for f in faces])
def box(key,material,c,d,rx=0,ry=0,rz=0):
    R=Matrix.Rotation(rx,3,'X')@Matrix.Rotation(ry,3,'Y')@Matrix.Rotation(rz,3,'Z')
    v=[tuple(R@Vector((i*d[0]/2,j*d[1]/2,k*d[2]/2))+Vector(c)) for i,j,k in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    geom(key,material,v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
def pipe(key,material,a,b,r=.15,n=8):
    a=Vector(a); b=Vector(b); w=(b-a).normalized(); u=w.cross(Vector((0,0,1)))
    if u.length<.1:u=w.cross(Vector((0,1,0)))
    u.normalize(); v=w.cross(u)
    verts=[tuple(p+r*(math.cos(i*math.tau/n)*u+math.sin(i*math.tau/n)*v)) for p in (a,b) for i in range(n)]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    geom(key,material,verts,faces)
def route(key,material,points,r=.18):
    for a,b in zip(points,points[1:]):pipe(key,material,a,b,r)
def tracked_route(name,key,material,points,r=.18):
    route(key,material,points,r);connection_routes.append({'name':name,'group':key,'material':material,'points':points,'radius':r})
def ball(key,material,c,d,n=9,rings=5):
    verts=[]
    for j in range(rings+1):
        p=math.pi*j/rings
        for i in range(n):
            t=math.tau*i/n;verts.append((c[0]+math.sin(p)*math.cos(t)*d[0],c[1]+math.sin(p)*math.sin(t)*d[1],c[2]+math.cos(p)*d[2]))
    faces=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(rings) for i in range(n)]
    geom(key,material,verts,faces)
def item(kind,pos,d): inventory.append({'kind':kind,'center':pos,'dimensions':d})
def text_obj(body,pos,size=2,key='decor',rot=(math.pi/2,0,0),material='sign'):
    cu=bpy.data.curves.new(body,'FONT');cu.body=body;cu.size=size;cu.extrude=.015;cu.align_x='CENTER'
    ob=bpy.data.objects.new(body,cu);scene.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=rot;ob.parent=group(key);cu.materials.append(M[material]);return ob

def tree(x,y,s=1):
    key='landscape';pipe(key,'wood',(x,y,0),(x,y,5.5*s),.3*s)
    color=random.choice(['leaf','leafLight','leafGold','leafRust'])
    for dx,dy,dz,r in [(0,0,6,3),(-1.6,0,5.2,2.1),(1.4,.4,6,2),(0,1.3,7.3,2)]:ball(key,color,(x+dx*s,y+dy*s,dz*s),(r*s,r*s,r*1.2*s))
def solar(key,x,y,z,w,h,tilt):
    box(key,'silver',(x,y,z),(w+.12,h+.12,.1),rx=tilt)
    box(key,'panel',(x,y,z+.075),(w,h,.09),rx=tilt)
    # Fine panel grid is geometry, not a texture.
    for dx in [-w/2+w*i/6 for i in range(1,6)]:box(key,'panelGrid',(x+dx,y,z+.126),(.018,h,.012),rx=tilt)
    for a in (-.5,0,.5):
        yy=a*h/1.5;box(key,'panelGrid',(x,y+yy*math.cos(tilt),z+.13+yy*math.sin(tilt)),(w,.014,.012),rx=tilt)

# Ground is split at the section opening, so the cutaway exposes real boreholes.
# Real openings for both the floor trenches and the ground section.
xs=[-350,-105,-80,75,105,300];ys=[-330,-220,-65,-30,30,200]
for xa,xb in zip(xs,xs[1:]):
    for ya,yb in zip(ys,ys[1:]):
        x=(xa+xb)/2;y=(ya+yb)/2
        if (-105<x<105 and -30<y<30) or (-80<x<75 and -220<y<-65):continue
        box('terrain','grass',(x,y,-1.1),(xb-xa,yb-ya,2))
box('groundCap','meadow',(-2.5,-142.5,-.5),(155,155,1))
# Larger meadow strips outside the drilled field.
for c,d in [((-140,-185,.025),(120,250,.05)),((137.5,-215,.025),(125,190,.05)),((-2.5,-265,.025),(155,90,.05))]:box('terrain','meadow',c,d)
# Urban surroundings, road and railway, with southeastern skyline.
box('context','grass',(200,-65,-1.1),(1800,1500,2))
for c,d in [((-25,218,-.05),(760,13,.1)),((-373,-65,-.05),(13,600,.1)),((326,-65,-.05),(12,600,.1)),((-25,-351,-.05),(760,12,.1))]:box('context','asphalt',c,d)
for y in [235,238]:pipe('context','steel',(-420,y,.1),(440,y,.1),.12)
for x in range(-420,440,4):box('context','wood',(x,236.5,0),(1.5,5,.2))
for x in range(-400,460,47):
    if -100<x<120:continue
    h=random.uniform(7,17);box('context','concrete',(x,275,h/2),(random.uniform(22,39),28,h));box('context','roof',(x,275,h+.1),(36,28,.2))
for i in range(26):
    x=450+i*22; y=-650+random.uniform(-50,60);h=random.uniform(22,90)
    box('skyline','wall',(x,y,h/2),(18,20,h))
for x,y,w,h in [(-265,-10,110,100),(0,-37,220,8),(0,70,280,8),(-115,20,8,120),(122,-5,9,70),(230,55,85,9),(-220,-75,15,160)]:box('roads','asphalt',(x,y,.06),(w,h,.12))

for a,b in [((-345,-160),(-260,-100)),((-260,-100),(-218,-15))]:
    box('roads','asphalt',((a[0]+b[0])/2,(a[1]+b[1])/2,.07),(math.dist(a,b),10,.14),rz=math.atan2(b[1]-a[1],b[0]-a[0]))
# Native swales and perimeter trees.
for x in range(-335,296,16):tree(x,185,random.uniform(.75,1.3))
for y in range(-320,180,17):
    tree(-340,y,random.uniform(.7,1.2));tree(287,y,random.uniform(.7,1.1))
for x in range(-205,111,20):tree(x,-322,random.uniform(.7,1.1))
for y in range(-100,35,12):tree(-202,y,.9)
for x in range(-331,-222,5):box('landscape','gravel',(x,-85,.6),(4,1.2,1.2))
# Hall shell and single-slope roof. Roof slope 1.5 m / 60 m.
# Slab with physical slots under every covered aisle trench.
slots=sorted((start+3.05+row*2.9-.45,start+3.05+row*2.9+.45) for start in L['hall']['pods'] for row in range(8))
last=-105
for a,b in slots+[(105,105)]:
    if a>last:box('sealed','concrete',((last+a)/2,-5,-.18),(a-last,42,.36))
    last=b
box('sealed','concrete',(0,-28,-.18),(210,4,.36));box('sealed','concrete',(0,23,-.18),(210,14,.36))
box('hall','wall',(0,-29.8,1.0),(210,.4,2))
box('hall','wood',(0,-29.8,5.5),(210,.4,5))
box('hall','glass',(0,-29.81,2.5),(208,.12,1))
# North wall has a real intake opening, x73.5..76.5, z1.2..2.6.
for x,w in [((-105+73.5)/2,178.5),((76.5+105)/2,28.5)]:box('hall','charcoal',(x,29.8,4.75),(w,.4,9.5))
box('hall','charcoal',(75,29.8,.6),(3,.4,1.2));box('hall','charcoal',(75,29.8,6.05),(3,.4,6.9))

def slope_wall(x,ya,yb,material):
    za=8+(ya+30)*.025;zb=8+(yb+30)*.025
    geom('hall',material,[(x-.2,ya,0),(x+.2,ya,0),(x+.2,yb,0),(x-.2,yb,0),(x-.2,ya,za),(x+.2,ya,za),(x+.2,yb,zb),(x-.2,yb,zb)],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
slope_wall(-104.8,-30,30,'wood')
# East facade with three actual dock openings.
for y,h in [(-26,8),(-10,8),(6,8),(26,8)]:slope_wall(104.8,y-h/2,y+h/2,'wall')
for y in [-18,-2,14]:
    box('hall','wall',(104.8,y,6.6),(.4,8,4.2));box('airlock','charcoal',(104.9,y,2.25),(.15,4,4.5))
    box('hall','concrete',(109,y,.5),(8,5,1))
for x in range(-104,105,2):box('hall','wood',(x,-30.04,4.1),(.05,.14,7.8))
box('hallRoof','roof',(0,0,8.75),(210,60,.2),rx=math.atan(1.5/60))
for x in range(-104,105,2):box('hallRoof','silver',(x,0,8.9),(.045,60,.07),rx=math.atan(1.5/60))
for x in range(-98,99,4):
    for y in range(-24,25,6):solar('roofSolar',x,y,8.75+y*.025+.6,3.8,5.4,math.radians(10))
item('hall', [0,0,4.75],[210,60,9.5])
# Enclosed dock vestibules: each has an outer and inner door, never both shown open.
for y in [-18,-2,14]:
    for side in [-2.4,2.4]:box('airlock','wall',(102,y+side,2.5),(6,.2,5))
    box('airlock','wall',(99,y,4.75),(.2,4.8,.5))
    for side in [-2.2,2.2]:box('airlock','wall',(99,y+side,2.25),(.2,.4,4.5))
    box('airlock','charcoal',(99,y,2.25),(.15,4,4.5))
    for z in [.3,.9,1.5,2.1,2.7,3.3,3.9,4.4]:box('airlock','silver',(98.9,y,z),(.025,3.9,.025))
    box('airlockRoof','wall',(102,y,5.08),(6.2,5,.16))
    box('airlock','sensorScreen',(98.82,y-2.05,1.6),(.12,.18,.25))
    item('dockAirlock',[102,y,2.5],[6,4.8,5])
    item('airlockInnerDoor',[99,y,2.25],[.15,4,4.5])
    item('airlockOuterDoor',[104.9,y,2.25],[.15,4,4.5])
for x,y in [(91,-15),(91,0)]:
    box('airlock','wood',(x,y,.12),(1.1,1.7,.24));box('airlock','wall',(x,y,1.4),(.85,1.5,2.55))
    for z in [.45,2.35]:box('airlock','drainBand',(x,y-.76,z),(.82,.02,.06))
text_obj('WARM-UP STAGING',(91,-23,.04),.8,'airlock',rot=(0,0,math.pi/2))
# Detailed interiors: 4 pods, alternating rows; 368 active and 32 spare positions.
for pod,start in enumerate(L['hall']['pods']):
    for sensor_y in [-16,8]:
        box('dewpoint','white',(start+.18,sensor_y,1.8),(.15,.15,.15));box('dewpoint','sensorScreen',(start+.262,sensor_y,1.81),(.014,.09,.055));box('dewpoint','led',(start+.27,sensor_y,1.765),(.012,.025,.012));item('dewpointSensor',[start+.18,sensor_y,1.8],[.15,.15,.15])
    for side in [start,start+25]:box('partitions','wall',(side,-5,3.5),(.18,42,7))
    box('partitions','wall',(start+12.5,-25.9,3.5),(25,.18,7))
    box('electrical','concrete',(start+35,-5,.03),(19.7,41.7,.06))
    for xx in [start+29,start+34,start+39]:
        for yy in range(-20,16,5):
            battery=xx<start+39
            box('electrical','white',(xx,yy,1.4),(1.4,1,2.8));box('electrical','batteryFace' if battery else 'charcoal',(xx,yy-.52,1.5),(1.2,.04,1.7));box('electrical','led',(xx,yy-.55,2.5),(.3,.02,.06))
            if battery:
                for zz in [.8,1.2,1.6,2]:box('electrical','silver',(xx,yy-.55,zz),(1.05,.03,.035))
            else:box('electrical','powerAmber',(xx,yy-.55,2.1),(.6,.04,.18))
            item('batteryCabinet' if battery else 'upsCabinet',[xx,yy,1.4],[1.4,1,2.8])
            # Illustrative DC connections from the battery banks into the UPS.
            if battery:route('power','powerAmber',[(xx,yy,2.8),(xx,yy,3.5),(start+39,yy,3.5),(start+39,yy,2.8)],.045)
            else:route('power','powerAmber',[(xx+.4,yy,2.8),(xx+.4,yy,4.0),(xx+.4,16,4.0)],.055)
    # Distinct UPS output/distribution cabinet and continuous overhead feeder.
    out=start+43
    box('electrical','white',(out,12,1.5),(1.6,1.2,3));box('electrical','powerAmber',(out,11.38,1.5),(1.4,.05,2.7))
    box('electrical','charcoal',(out,11.34,2.25),(.65,.03,.4))
    text_obj('BATTERIES',(start+31.5,-21.2,3.2),.68,'electrical')
    text_obj('UPS',(start+39,-21.2,3.2),.75,'electrical')
    text_obj('DISTRIBUTION',(out,11.3,3.35),.48,'electrical')
    route('power','powerAmber',[(start+39.4,16,4),(out,16,4),(out,12,4),(out,12,3)],.09)
    route('power','powerAmber',[(out+.45,12,3),(out+.45,12,4.8),(out+.45,18,4.8)],.12)
    box('power','powerAmber',((start+2+out+.45)/2,18,4.8),(out+.45-(start+2),.35,.26))
    item('upsDistribution',[out,12,1.5],[1.6,1.2,3])
    for row in range(8):
        x=start+2+row*2.9
        # Four compute rows and four network rows.
        compute=row%2==0; n=25 if compute else 23;key='compute' if compute else 'network'
        tx=x+1.05
        box('trench','charcoal',(tx,-5,-.28),(.9,41,.6))
        for off,mm in [(-.18,'warm'),(.18,'blue')]:pipe('trench',mm,(tx+off,-25,-.1),(tx+off,20,-.1),.08)
        # Open-slatted lids let the below-floor cooling lines read in cutaway.
        for yy in range(-25,17):box('trench','steel',(tx,yy,.06),(.9,.11,.08))
        for j in range(n):
            y=-23+j*1.52
            active=(not compute or j<23)
            if not active:
                box('spares','steel',(x,y,.04),(.6,1.2,.08));item('sparePosition',[x,y,.04],[.6,1.2,.08]);continue
            box(key,'rack' if compute else 'network',(x,y,1.15),(.6,1.2,2.3))
            box(key,'black',(x,y-.607,1.15),(.53,.025,2.14))
            for z in [.3,.55,.8,1.05,1.3,1.55,1.8,2.05]:
                box(key,'steel',(x,y-.626,z),(.48,.025,.018))
            box(key,'led',(x-.245,y-.633,1.25),(.024,.018,1.9))
            if not compute:
                box(key,'steel',(x,y+.635,1.15),(.56,.06,2.18))
                for z in [.25,.5,.75,1,1.25,1.5,1.75,2]:box(key,'black',(x,y+.673,z),(.51,.02,.1))
            for off,mm in [(-.1,'warm'),(.1,'blue')]:route(key,mm,[(tx+off,y,-.05),(tx+off,y,.3),(x+.36,y+.43,.4),(x+.36,y+.43,1.8)],.025)
            # A visible tap-off and drop connect every active rack to its busway.
            box('power','powerAmber',(x,y,4.57),(.28,.28,.3))
            route('power','powerAmber',[(x,y,4.45),(x-.25,y,4.25),(x-.25,y,2.3)],.035)
            item('rackPowerDrop',[x-.25,y,3.375],[.07,.07,2.15])
            item('computeRack' if compute else 'networkRack',[x,y,1.15],[.6,1.2,2.3])
        box('spine','white',(x,20,1.25),(1.4,1.4,2.5));box('spine','charcoal',(x,19.28,1.3),(1.1,.05,1.8))
        item('coolingUnit',[x,20,1.25],[1.4,1.4,2.5])
        # Pass below the other headers, then rise only into the intended circuit.
        for dx,mm,yy in [(-.22,'warm',26 if compute else 28),(.22,'blue',27 if compute else 29)]:route('spine',mm,[(tx+dx,16,-.1),(tx+dx,20,-.1),(x+dx,20,2.7),(x+dx,21,2.3),(x+dx,yy,2.3),(x+dx,yy,2.8)],.1)
        box('power','powerAmber',(x,-3.5,4.8),(.3,43,.25))
        box('power','cableTray',(x+.5,-4,5.2),(.4,42,.12))
        # Support rods and tray sides make trays legible as hardware, not beams.
        for yy in [-22,-12,-2,8,16]:pipe('power','steel',(x+.5,yy,5.2),(x+.5,yy,7),.018)
        for off in [-.2,.2]:box('power','cableTray',(x+.5+off,-4,5.3),(.035,42,.2))
        item('rowBusway',[x,-3.5,4.8],[.3,43,.25])
        pipe('fire','red',(x,-25,6.6),(x,16,6.6),.035)
        pipe('fire','white',(x+.4,-25,6.8),(x+.4,16,6.8),.015)
        for y in range(-22,17,6):
            pipe('fire','red',(x,y,6.6),(x,y,6.35),.025)
            pipe('fire','silver',(x,y,6.34),(x,y,6.37),.11,12)
    for x in [start+3,start+23]:box('partitions','steel',(x,15,3.5),(.18,.18,7))
# The sprinkler cross-main and west-side riser are distinct from floor coolant.
route('fire','red',[(-101,-25,.2),(-101,-25,6.6),(start+22.3,-25,6.6)],.075)
for yy,mm,circuit in [(26,'warm','chipWarm'),(27,'blue','chipCool'),(28,'warm','roomWarm'),(29,'blue','roomCool')]:tracked_route(circuit+'_spine','spine',mm,[(-102,yy,2.8),(102,yy,2.8)],.22)
# Cooling ridge: 102 units, 816 fans; decks, legs, rails, end stairs.
box('coolers','steel',(0,48,5.9),(210,24,.2))
for x in range(-102,103,6):
    for y in [37,48,59]:box('coolers','steel',(x,y,3),(.23,.23,6))
for y in [36,60]:
    for z in [6.6,7.1]:pipe('coolers','silver',(-105,y,z),(105,y,z),.035)
    for x in range(-105,106,5):pipe('coolers','silver',(x,y,6),(x,y,7.1),.045)
for row in range(6):
    for col in range(17):
        x=-99+col*12.375;y=37.6+row*4.1;z=8.6
        box('coolers','white',(x,y,z),(12,2.4,2.6));box('coolers','charcoal',(x,y-1.21,z),(11.6,.03,1.8))
        for xx in [x-5,x+5]:
            for yy in [y-.8,y+.8]:box('coolers','steel',(xx,yy,6.65),(.12,.12,1.3))
        for f in range(8):
            fx=x-5.2+f*1.48;pipe('coolers','black',(fx,y,9.9),(fx,y,9.96),.5,16)
            pipe('coolers','silver',(fx,y,9.97),(fx,y,10.04),.12,8)
            for a in [0,math.pi/3,2*math.pi/3]:
                if row==0 and col==8:
                    rotor='coolerRotor'+str(f);rotor_origins[rotor]=[fx,y,9.99];box(rotor,'steel',(0,0,0),(.8,.065,.025),rz=a)
                else:box('coolers','steel',(fx,y,9.99),(.8,.065,.025),rz=a)
        item('dryCooler',[x,y,z],[12,2.4,2.6])
for x in [-109,109]:
    for i in range(25):box('coolers','steel',(x,42+i*.3,i*.24+.12),(3,.31,.24))
    route('coolers','silver',[(x-1.5,42,1),(x-1.5,49.5,7)],.055)
# Three bridges. Water crosses outside, never over racks.
for x in [-60,0,60]:
    box('bridges','steel',(x,33,6.8),(4,6,.2))
    for off,r,mm,header in [(-1.3,.3,'warm',26),(-.4,.3,'blue',27),(.5,.2,'warm',28),(1.25,.2,'blue',29)]:
        circuit={26:'chipWarm',27:'chipCool',28:'roomWarm',29:'roomCool'}[header]
        tracked_route(circuit+'_main_bridge_'+str(x),'bridges',mm,[(x+off,header,2.8),(x+off,header,1.8),(x+off,30,1.8),(x+off,30,7.2),(x+off,36,7.2),(x+off,38,7.2)],r)
    item('pipeBridge',[x,33,7],[4,6,.4])
# Revision03: dry halls, positive-pressure fresh air, and cold-weather safeguards.
# Tank and drain sizes/grades are illustrative envelopes, not hydraulic engineering.
for t in L['freeze_protection']['drain_tanks']:
    x,y,z=t['center'];pipe('drainTanks','white',(x-6,y,z),(x+6,y,z),1.5,24)
    for dx in [-4,4]:box('drainTanks','steel',(x+dx,y,.2),(.6,2.4,.4))
    for dx in [-5.6,5.6]:pipe('drainTanks','drainBand',(x+dx-.08,y,z),(x+dx+.08,y,z),1.51,24)
    item('drainTank',[x,y,z],[12,3,3])
for c in L['freeze_protection']['expansion_tanks']['centers']:
    x,y,z=c;pipe('drainTanks','white',(x,y,.2),(x,y,2.4),.5,16)
    pipe('drainTanks','drainBand',(x,y,1.65),(x,y,1.8),.51,16)
    box('drainTanks','steel',(x,y,.1),(.8,.8,.2));item('expansionTank',c,[1,1,2.2])
text_obj('DRAIN-DOWN / GLYCOL',(-88,21.45,2),.65,'drainTanks')
# Service panels are a separate group so X-ray can reveal the coil and drain pan.
fx,fy,fz=L['freeze_protection']['fresh_air_unit']['center']
for dx in [-2.92,2.92]:box('freshAirCase','white',(fx+dx,fy,fz),(.16,2.5,2.5))
for dy in [-1.17,1.17]:box('freshAirCase','white',(fx,fy+dy,fz),(6,.16,2.5))
box('freshAirCase','white',(fx,fy,2.7),(6,2.5,.1));box('freshAir','steel',(fx,fy,.25),(6,2.5,.1))
box('freshAir','charcoal',(fx,fy,1.45),(5.5,.15,1.9))
for xx in [72.4+i*.2 for i in range(27)]:box('freshAir','silver',(xx,fy-.12,1.45),(.035,.13,1.85))
for zz in [.7,1.1,1.5,1.9,2.3]:pipe('freshAir','blue',(72.35,fy-.22,zz),(77.65,fy-.22,zz),.045)
box('freshAir','silver',(fx,fy-.1,.45),(5.6,1.8,.12))
# An intake duct below the service headers reaches the real facade opening.
for dx in [-1.42,1.42]:box('freshAir','steel',(fx+dx,27.12,1.9),(.08,5.5,1.25))
for zz in [1.31,2.49]:box('freshAir','steel',(fx,27.12,zz),(2.85,5.5,.08))
for zz in [1.26+i*.15 for i in range(9)]:box('freshAir','silver',(75,30.03,zz),(2.85,.25,.07),rx=.25)
box('freshAir','charcoal',(75,29.85,1.9),(2.8,.04,1.3))
tracked_route('fresh_air_condensate','freshAir','silver',[(77.7,23.1,.45),(78.4,23.1,.45),(78.4,23.1,.15),(78.4,24.2,.15)],.025)
box('freshAir','steel',(78.4,24.2,.04),(.35,.35,.08));item('freshAirUnit',[fx,fy,fz],[6,2.5,2.5]);item('freshAirDrainPan',[fx,fy-.1,.45],[5.6,1.8,.12])
item('freshAirLouver',[75,30.03,1.9],[2.85,.25,1.4])
text_obj('DRIED FRESH AIR',(75,21.9,2.9),.42,'freshAir')
# Bypass mixes warm return with supply; its actuator has its own material for explanation.
box('bypass','steel',(0,34.5,6.78),(4,3,.16))
tracked_route('chip_bypass','bypass','warm',[(-1.3,35,7.2),(-1.3,35,8.3),(-.4,35,8.3),(-.4,35,7.2)],.18)
pipe('bypass','steel',(-1.05,35,8.3),(-.65,35,8.3),.27,16)
pipe('bypass','steel',(-.85,35,8.3),(-.85,35,8.67),.09,12)
box('bypass','bypassYellow',(-.85,35,8.9),(.65,.5,.48));box('bypass','sensorScreen',(-.85,34.74,8.95),(.3,.02,.18))
item('bypassValve',[-.85,35,8.3],[.55,.55,.55]);item('bypassActuator',[-.85,35,8.9],[.65,.5,.48])
# Four independent operating circuits below the deck connect to all three actual bridges.
circuits={'chipWarm':(-1.3,5.1,'warm'),'chipCool':(-.4,4.7,'blue'),'roomWarm':(.5,4.2,'warm'),'roomCool':(1.25,3.8,'blue')}
crossfeed_y={'chipWarm':31.0,'chipCool':31.7,'roomWarm':32.4,'roomCool':33.1}
row_offsets={'chipWarm':1.42,'chipCool':1.75,'roomWarm':2.08,'roomCool':2.4}
for name,(off,z,material) in circuits.items():
    cy=crossfeed_y[name]
    tracked_route(name+'_crossfeed','coolerCircuitPipes',material,[(-60+off,cy,z),(60+off,cy,z)],.16)
    tracked_route(name+'_north_trunk','coolerCircuitPipes',material,[(off,cy,z),(off,61,z)],.16)
    for bx in [-60,0,60]:tracked_route(name+'_bridge_'+str(bx),'coolerCircuitPipes',material,[(bx+off,36,7.2),(bx+off,cy,7.2),(bx+off,cy,z)],.16)
# Row manifolds are at separate elevations so the four circuits never cross-connect.
for row in range(6):
    y=37.6+row*4.1
    for family in ['chip','room']:
        cols=[c for c in range(17) if (row*17+c<73)==(family=='chip')]
        if not cols:continue
        for suffix in ['Warm','Cool']:
            name=family+suffix;tx,z,mm=circuits[name];port_dx=4 if suffix=='Warm' else -4
            xx=[-99+c*12.375+port_dx for c in cols]
            my=y+row_offsets[name]
            tracked_route(name+'_row_'+str(row),'coolerCircuitPipes',mm,[(min(min(xx),tx),my,z),(max(max(xx),tx),my,z)],.11)
# Every module has two actual isolation valves, one outlet freeze sensor and a lowest-point drain.
for row in range(6):
    for col in range(17):
        x=-99+col*12.375;y=37.6+row*4.1;idx=row*17+col;family='chip' if idx<73 else 'room'
        for suffix,dx in [('Warm',4),('Cool',-4)]:
            name=family+suffix;tx,z,mm=circuits[name];px=x+dx;my=y+row_offsets[name];vy=(y+1.2+my)/2
            tracked_route('cooler_'+str(idx)+'_'+suffix,'freezeProtection',mm,[(px,y+1.2,7.6),(px,my,7.6),(px,my,z)],.095)
            pipe('freezeProtection','steel',(px,vy-.1,7.6),(px,vy+.1,7.6),.15,12)
            box('freezeProtection','freezeActuator',(px,vy,7.92),(.26,.26,.28));pipe('freezeProtection','steel',(px,vy,7.6),(px,vy,7.8),.04)
            item('coolerIsolationValve',[px,vy,7.6],[.3,.2,.3])
        sy=y+row_offsets[family+'Cool'];box('freezeProtection','white',(x-4,sy,7.72),(.18,.15,.18));box('freezeProtection','led',(x-4,sy+.09,7.74),(.08,.015,.045));item('coolerFreezeSensor',[x-4,sy,7.72],[.18,.15,.18])
        drain_y=y-1.3;bx=min(L['freeze_protection']['drain_bridge_x'],key=lambda p:abs(p-x));base=6.5+(drain_y-36)*.004;dz=base+abs(x-bx)*.002
        tracked_route('cooler_'+str(idx)+'_drain','drainLines','drainJacket',[(x,y-1.1,7.3),(x,drain_y,7.24),(x,drain_y,dz)],.065)
        pipe('freezeProtection','steel',(x,y-1.1,7.3),(x,drain_y,7.24),.10,10);box('freezeProtection','freezeActuator',(x+.17,drain_y,7.22),(.18,.18,.18));item('coolerDrainValve',[x,drain_y,7.24],[.2,.2,.2])
        pipe('drainLines','drainBand',(x,drain_y,dz+.04),(x,drain_y,dz+.10),.071,10)
        item('coolerDrainJoin',[x,drain_y,dz],[.13,.13,.13])
# Separate drain rows fall toward the nearest pipe bridge. Grades are explanatory only.
for row in range(6):
    y=37.6+row*4.1-1.3;base=6.5+(y-36)*.004
    for bx in L['freeze_protection']['drain_bridge_x']:
        xx=[-99+c*12.375 for c in range(17) if min(L['freeze_protection']['drain_bridge_x'],key=lambda p:abs(p-(-99+c*12.375)))==bx]
        ends=sorted(set([min(xx),bx,max(xx)]));pts=[(x,y,base+abs(x-bx)*.002) for x in ends]
        tracked_route('drain_row_'+str(row)+'_'+str(bx),'drainLines','drainJacket',pts,.075)
for bx in L['freeze_protection']['drain_bridge_x']:
    hz=4.4+(bx+95)*.001
    tracked_route('drain_to_tanks_'+str(bx),'drainLines','drainJacket',[(bx,56.8,6.5+(56.8-36)*.004),(bx,36,6.5),(bx,30.5,6.48),(bx,30.5,hz+.3),(bx,25.2,hz)],.085)
    pipe('drainLines','drainBand',(bx,33.4,6.491),(bx,33.8,6.4925),.091,12)
tracked_route('indoor_drain_manifold','drainLines','drainJacket',[(-95,25.2,4.4),(61.8,25.2,4.5568)],.12)
for x in [-95,-81]:tracked_route('tank_inlet_'+str(x),'drainTanks','drainJacket',[(x,25.2,4.4+(x+95)*.001),(x,23,4.4),(x,23,3.35)],.12)
tracked_route('expansion_manifold','drainTanks','drainJacket',[(-81,25.2,4.414),(-66,25.2,4.414),(-66,23,2.7),(-69,23,2.7),(-63,23,2.7)],.055)
for x in [-69,-67,-65,-63]:tracked_route('expansion_'+str(x),'drainTanks','drainJacket',[(x,23,2.7),(x,23,2.4)],.055)

# Six chillers, long side north-south, 3 columns of 2.
box('chillers','concrete',(123,48,.18),(30,28,.36))
for x in [113,123,133]:
    for y in [41,55]:
        box('chillers','white',(x,y,1.65),(2.3,12,2.5));box('chillers','black',(x-1.16,y,1.7),(.025,11.7,1.8))
        for j in range(7):pipe('chillers','black',(x,y-5+j*1.65,2.92),(x,y-5+j*1.65,3),.8,12)
        item('backupChiller',[x,y,1.65],[2.3,12,2.5])
for x,mm,header in [(112,'blue',29),(114,'warm',28)]:route('chillers',mm,[(x,34,.6),(x,header,.6),(100,header,.6),(100,header,2.8)],.16)
# Ground cutaway: geological faces, bottom, and all 32 x 32 U loops.
box('geology','earth',(-81,-142.5,-.5),(2,155,1))
box('geology','till',(-81,-142.5,-8),(2,155,14))
box('geology','rock',(-81,-142.5,-82.5),(2,155,135))
box('geology','rock',(-2.5,-142.5,-151),(159,159,2))
for center,height,mm in [(-.5,1,'earth'),(-8,14,'till'),(-82.5,135,'rock')]:box('geology',mm,(-2.5,-63,center),(159,2,height))
for i in range(32):
    for j in range(32):
        x=-80+i*5;y=-220+j*5
        focus=x==0 and y==-220;key='boreholeFocus' if focus else 'boreholes'
        route(key,'blue' if focus else 'groundPipe',[(x-.13,y,-1),(x-.13,y,-149.8),(x,y,-150)],.07)
        route(key,'warm' if focus else 'groundPipe',[(x,y,-150),(x+.13,y,-149.8),(x+.13,y,-1)],.07)
        pipe('boreholeSurface','concrete',(x,y,.01),(x,y,.055),.15,8)
        item('borehole',[x,y,-75],[.4,.2,150])
# Buried distribution headers connect every loop to the Cold Battery House.
for i in range(32):
    x=-80+i*5
    for off,mm,end in [(-.13,'blue',-62),(.13,'warm',-61)]:
        pipe('groundHeaders',mm,(x+off,-220,-1),(x+off,end,-1),.10)
        if mm=='blue':pipe('groundHeaders',mm,(x+off,end,-1),(x+off,end,-1.8),.10)
for yy,mm in [(-62,'blue'),(-61,'warm')]:
    z=-1.8 if mm=='blue' else -1
    route('groundHeaders',mm,[(-80.13,yy,z),(75.13,yy,z)],.22)
    hx,hy,west,header=(-.6,-47,-110,28) if mm=='warm' else (.6,-48.5,-111.5,29)
    ix=-3 if mm=='warm' else 3
    wz=-.7 if mm=='warm' else -2
    house_path=[(hx,yy,z),(hx,hy,z),(hx,hy,1.2),(ix,hy,1.2),(ix,hy,wz)]
    tracked_route('ground_house_'+mm,'groundHeaders',mm,house_path+[(west,hy,wz),(west,header,wz),(west,header,2.8),(-102,header,2.8)],.18)
    tracked_route('cold_insulation_'+mm,'coldInsulation','coldJacket',house_path,.29)
    for zz in [.15,.9]:pipe('coldInsulation',mm,(hx,hy,zz),(hx,hy,zz+.12),.3,12)
    px=(hx+ix)/2
    box('batteryHouse','steel',(px,hy,.35),(1.1,.8,.7));pipe('batteryHouse',mm,(px-.4,hy,1.2),(px+.4,hy,1.2),.4,16)
    item('groundLoopPump',[px,hy,1.2],[.8,.8,.8])
for x in [-40,40]:box('batteryHouse','concrete',(x,-62,.1),(3,3,.2))
for xx in [-14.9,14.9]:box('batteryHouse','wood',(xx,-47.5,3),(.2,15,6))
for yy in [-54.9,-40.1]:box('batteryHouse','wood',(0,yy,3),(30,.2,6))
box('batteryHouseRoof','leaf',(0,-47.5,6.15),(30.4,15.4,.3))
for x in range(-14,15):box('batteryHouse','timber',(x,-55.04,3),(.05,.08,5.8))
box('batteryHouse','charcoal',(0,-55.08,1.5),(3,.1,3))
# Meadow panels stop west of the snow pad, with grass access lanes.
for y in range(-300,-65,6):
    for x in range(-180,116,12):
        if abs(x+40)<5 or abs(x-40)<5:continue
        solar('solarField',x,y,2.3,10.7,4,math.radians(25))
        for xx in [x-4,x+4]:pipe('solarField','steel',(xx,y,0),(xx,y,2.4),.07)
# Four canopy rows, 100 m north-south, on the parking lot.
for x in [-313,-286,-259,-232]:
    for y in range(-54,40,5):solar('solar',x,y,4.1,11.8,4.9,math.radians(10))
    for y in range(-55,41,10):
        box('solar','steel',(x,y,1.75),(.18,.18,3.5));box('solar','steel',(x,y,3.5),(12,.15,.25))
    for yy in range(-55,40,3):
        for xx in [x-4,x+4]:
            box('parking','line',(xx,yy,.14),(5.2,.05,.02))
            if random.random()<.6:
                color=random.choice(['white','charcoal','silver','red']);box('parking',color,(xx,yy+1.4,.65),(4.3,1.8,1.15));box('parking','glass',(xx-.1,yy+1.4,1.35),(2.5,1.6,.5))
# Substation, transformers, control building, gantries, east power line.
box('substation','gravel',(175,0,.12),(70,80,.24))
for y in [-22,0,22]:
    box('substation','white',(171,y,3.5),(8,6,7))
    for x in [166.8,175.2]:
        for yy in range(-2,3):box('substation','charcoal',(x,y+yy,3.4),(.18,.5,5.5))
    for xx in [168,171,174]:pipe('substation','black',(xx,y,7),(xx,y,9),.24,10)
    item('transformer',[171,y,3.5],[8,6,7])
box('substation','wall',(194,-25,2.5),(20,10,5))
for y in [-25,0,25]:
    for x in [147,202]:box('substation','steel',(x,y,6),(.25,.25,12))
    box('substation','steel',(174.5,y,12),(55,.3,.3))
for x in [240,310,390]:
    for dx,dy in [(-3,-3),(-3,3),(3,-3),(3,3)]:pipe('powerLine','steel',(x+dx,dy,0),(x+dx*.2,dy*.2,27),.15)
    for z in range(3,27,3):
        for yy in [-2,2]:route('powerLine','steel',[(x-2,yy,z),(x+2,yy,z+3)],.07)
    box('powerLine','steel',(x,0,25),(1,14,.25))
for y in [-6,0,6]:route('powerLine','charcoal',[(210,y,12),(240,y,25),(275,y,21),(310,y,25),(350,y,21),(390,y,25),(450,y,22)],.07)
# Backup yard with 30 containers, 4 tanks and reserved north pad.
box('generators','gravel',(210,120,.1),(120,100,.2))
for row in range(5):
    for col in range(6):
        x=159+col*14;y=81+row*14
        box('generators','white',(x,y,1.6),(12.2,2.44,2.9))
        box('generators','charcoal',(x+5.7,y,1.5),(.6,2.46,2.3))
        for xx in range(8):box('generators','steel',(x-5+xx,y-1.24,1.6),(.04,.03,2.6))
        pipe('generators','charcoal',(x-3,y,3.05),(x-3,y,4.5),.18)
        item('generator',[x,y,1.6],[12.2,2.44,2.9])
box('fuel','concrete',(255,113,.2),(24,39,.4))
for x in [246,252,258,264]:
    pipe('fuel','white',(x,98,2.1),(x,127,2.1),1.75,20)
    for y in [102,123]:box('fuel','steel',(x,y,.45),(3.5,1,.9))
    item('fuelTank',[x,112.5,2.1],[3.5,29,3.5])
for x in [242,268]:box('fuel','concrete',(x,113,.65),(.4,40,1.3))
for y in [93,133]:box('fuel','concrete',(255,y,.65),(26,.4,1.3))
box('reserved','concrete',(208,158,.15),(85,15,.3))
for x in range(171,248,5):box('reserved','line',(x,158,.32),(.13,12,.02),rz=.5)
# Mesh security fence: posts, 3 wires and vertical strands. Gates left at access.
for a,b in [((-120,-36),(136,-36)),((136,-36),(136,68)),((136,68),(277,68)),((277,68),(277,175)),((277,175),(143,175)),((143,175),(143,68)),((143,68),(-120,68)),((-120,68),(-120,-36))]:
    aa=Vector((*a,0));bb=Vector((*b,0));length=(bb-aa).length
    for z in [.2,1.2,2.4]:pipe('fence','charcoal',(*a,z),(*b,z),.022,6)
    for i in range(int(length/3)+1):
        p=aa.lerp(bb,i/max(1,int(length/3)));pipe('fence','charcoal',p,p+Vector((0,0,2.4)),.035,6)
# SEED House: two floors, timber structure, transparent south and west.
box('house','concrete',(-160,2.5,.1),(50,25,.2))
box('house','timber',(-160,2.5,4.5),(50,25,.25));box('house','leaf',(-160,2.5,9),(50,25,.35))
box('house','wood',(-160,14.8,4.5),(50,.4,9));box('house','wood',(-135.2,2.5,4.5),(.4,25,9))
box('house','glass',(-160,-9.9,4.5),(50,.12,8.7));box('house','glass',(-184.9,2.5,4.5),(.12,25,8.7))
for x in range(-185,-134,5):
    box('house','timber',(x,-10,4.5),(.3,.4,9));box('house','timber',(x,14,4.5),(.3,.4,9))
for y in range(-10,16,5):box('house','timber',(-185,y,4.5),(.3,.3,9))
for z in [.9,5.4]:
    for x in [-178,-168,-158,-148]:box('house','wood',(x,0,z),(2.4,1.3,.12))
box('house','concrete',(-191,2,.1),(12,28,.2));box('house','charcoal',(-193,-7,1.2),(.5,6,2.4))
text_obj('SEED',(-193.28,-7,1.25),1.3,'house',(math.pi/2,0,-math.pi/2))
# Greenhouse gabled glass roof, white frame, planting beds.
box('greenhouse','concrete',(-155,-35,.08),(60,30,.16))
for x in range(-185,-124,5):
    for y in [-50,-20]:box('greenhouse','white',(x,y,2.75),(.12,.12,5.5))
    route('greenhouse','white',[(x,-50,5.5),(x,-35,8),(x,-20,5.5)],.08)
for y in [-50,-20]:box('greenhouse','glass',(-155,y,2.8),(60,.06,5.5))
box('greenhouse','glass',(-185,-35,2.8),(.06,30,5.5));box('greenhouse','glass',(-125,-35,2.8),(.06,30,5.5))
for y,ang in [(-42.5,math.atan(2.5/15)),(-27.5,-math.atan(2.5/15))]:box('greenhouse','glass',(-155,y,6.75),(60,math.hypot(15,2.5),.06),rx=ang)
for y in [-48,-42,-36,-30,-24]:
    box('greenhouse','wood',(-155,y,.4),(56,3,.8))
    for x in range(-181,-127,3):ball('greenhouse','leaf',(x,y,1.3),(1.1,1.1,1.2))
# Greenhouse return-water branch and snow storage.
for yy,mm in [(-34,'warm'),(-35,'blue')]:route('heatPipes',mm,[(-85,26,2.8),(-116,26,2.8),(-116,yy,.6),(-125,yy,.6)],.22)
box('snowpad','gravel',(160,-95,.14),(80,50,.28))
# Paths to the cold battery house and meadow, not across the drilled headers.
box('paths','concrete',(-50,-56,.04),(100,3,.08))
# Human scale at the entrance.
for x,y in [(-191,1),(-190,3),(-178,-14),(-151,-14)]:
    pipe('people','charcoal',(x,y,.15),(x,y,1.3),.18);ball('people','wood',(x,y,1.62),(.16,.16,.19))

# Commit geometry: editable category/material objects, no generated raster assets.
for (key,mname),(verts,faces) in batches.items():
    if not verts:continue
    mesh=bpy.data.meshes.new(key+'_'+mname);mesh.from_pydata(verts,[],faces);mesh.materials.append(M[mname]);mesh.update()
    obj=bpy.data.objects.new(key+'_'+mname,mesh);scene.collection.objects.link(obj);obj.parent=group(key);obj['objectId']=key
# Clickable roots and helper groups retain a common semantic object ID.
for key in ['hallRoof','partitions']:group(key)['objectId']='hall' if key=='hallRoof' else 'sealed'
for key in ['boreholeFocus','boreholeSurface','groundHeaders']:group(key)['objectId']='boreholes'
for key,oid in {'airlockRoof':'airlock','freshAirCase':'freshAir','batteryHouseRoof':'batteryHouse','drainLines':'freezeProtection','coolerCircuitPipes':'coolers',**{key:'coolers' for key in rotor_origins}}.items():
    group(key)['objectId']=oid
    for child in group(key).children:child['objectId']=oid
for key,pos in rotor_origins.items():
    group(key).location=pos;group(key)['animationAxis']='localZ';group(key)['illustrativeAnimation']=True
(ROOT/'blender/inventory.json').write_text(json.dumps(inventory,indent=2))
scene['connection_routes']=json.dumps(connection_routes)
(ROOT/'blender/connections.json').write_text(json.dumps({'revision':L['revision'],'status':'Illustrative routes and sizes; not a pipework/drainability design','routes':connection_routes},indent=2))
(ROOT/'blender/viewer-anchors.json').write_text(json.dumps({'revision':L['revision'],'coordinate_system':'Blender XYZ, meters, Z up','anchors':{'dewpoint':[-49.82,8,1.8],'freshAir':[75,23.2,1.45],'airlock':[102,-2,2.5],'bypass':[-.85,35,8.9],'freezeProtection':[0,39.35,7.72],'drainTanks':[-88,23,1.85],'coldInsulation':[0,-47.75,1.2]},'rotors':rotor_origins,'rotor_axis':'local Blender Z (local glTF Y after export)','bypass_material':'bypassYellow','circuits':circuits,'crossfeed_y':crossfeed_y,'row_offsets':row_offsets},indent=2))
# Cameras and lights.
def camera(name,position,target,lens=45,ortho=None):
    data=bpy.data.cameras.new(name);obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj)
    obj.location=position;obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler();data.lens=lens;data.clip_end=5000
    if ortho:data.type='ORTHO';data.ortho_scale=ortho
    return obj
camera('S1-Hero',(-450,-450,250),(0,-55,0),32)
camera('S2-Winter',(350,300,160),(0,0,0),38)
camera('S3-Cutaway',(-290,-290,140),(-15,-80,-55),42)
camera('S3-Detail',(-37,-22,4),(-37,5,1.5),25)
camera('Power-Detail',(-15,-35,20),(-28,6,2.5),30)
camera('Freeze-Detail',(18,17,18),(0,37,7.5),40)
camera('Drain-Detail',(-77,5,13),(-86,23,2.5),35)
camera('FreshAir-Detail',(65,13,8),(75,25,1.5),38)
camera('S4-Plan',(-25,-65,900),(-25,-65,0),ortho=750)
for name,pos in [('QA-North',(0,470,150)),('QA-South',(0,-560,170)),('QA-East',(580,-50,160)),('QA-West',(-580,-50,160))]:camera(name,pos,(0,-45,0),35)
world=bpy.data.worlds.new('Cambridge daylight');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.62,.73,.82,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5;scene.world=world
light=bpy.data.lights.new('Southwest afternoon','SUN');light.energy=3.5;light.color=(1,.85,.65);light.angle=math.radians(5)
obj=bpy.data.objects.new('Southwest afternoon',light);scene.collection.objects.link(obj);obj.rotation_euler=(math.radians(62),math.radians(-22),math.radians(-35))
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
    for d in prefs.devices:d.use=(d.type=='METAL')
    if any(d.type=='METAL' for d in prefs.devices):scene.cycles.device='GPU'
except Exception:pass
scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.camera=bpy.data.objects['S1-Hero']
for key in ['boreholes','boreholeFocus','groundHeaders','geology','coldInsulation']:
    for o in group(key).children:o.hide_render=True;o.hide_set(True)
# Save the authoritative editable master before making visibility variants.
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/SEED-Cambridge.blend'))
# Export all geometry including hidden cutaway meshes; visibility is handled by the tour.
for obj in bpy.data.objects:obj.hide_set(False)
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.data.objects:
    if obj.type in {'MESH','FONT','EMPTY'}:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'assets/campus.glb'),export_format='GLB',use_selection=True,export_extras=True,export_cameras=False,export_lights=False,export_yup=True,export_apply=True)
print('SEED_MODEL_READY',len(bpy.data.objects),'objects',len(inventory),'inventory items',flush=True)
