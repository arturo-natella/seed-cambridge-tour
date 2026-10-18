import bpy,json,math,hashlib
from pathlib import Path
from collections import Counter,defaultdict,deque
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parent.parent
inv=json.loads((ROOT/'blender/inventory.json').read_text());counts=Counter(x['kind'] for x in inv)
depsgraph=bpy.context.evaluated_depsgraph_get()
def world_mesh(obj):
    evaluated=obj.evaluated_get(depsgraph)
    return [evaluated.matrix_world@v.co for v in evaluated.data.vertices],evaluated.data
def bounds(key):
    points=[]
    ob=bpy.data.objects[key]
    for o in [ob,*ob.children_recursive]:
        if o.type=='MESH':points.extend(world_mesh(o)[0])
    return {'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
checks=[]
def check(name,value,expected,tol=.001):checks.append({'name':name,'measured':value,'expected':expected,'tolerance':tol,'pass':abs(value-expected)<=tol})
b=bounds('sealed');check('Hall slab width',b['max'][0]-b['min'][0],210);check('Hall slab depth',b['max'][1]-b['min'][1],60)
r=bounds('hallRoof');check('Roof low edge',r['min'][2],7.9,.03);check('Roof high edge',r['max'][2],9.6,.1)
b=bounds('boreholes');check('Borehole bottom',b['min'][2],-150,.1);check('Borehole field x span',b['max'][0]-b['min'][0],155.4,.15)
for key,n in {'computeRack':368,'networkRack':368,'sparePosition':32,'dryCooler':102,'backupChiller':6,'borehole':1024,'generator':30,'fuelTank':4,'pipeBridge':3,'transformer':3,'rackPowerDrop':736,'rowBusway':32,'upsDistribution':4,'batteryCabinet':64,'upsCabinet':32}.items():check(key,counts[key],n,0)
focus=bounds('boreholeFocus');check('Highlighted loop bottom',focus['min'][2],-150,.1);check('Highlighted loop at south edge',focus['min'][1],-220.07,.01)
surface=bounds('boreholeSurface');check('Surface lids span field',surface['max'][0]-surface['min'][0],155.3,.01)
def surface_tree(name):
    vertices,mesh=world_mesh(bpy.data.objects[name])
    return BVHTree.FromPolygons(vertices,[list(p.vertices) for p in mesh.polygons],all_triangles=False)
power=surface_tree('power_powerAmber')
rack_points=[Vector((r['center'][0]-.25,r['center'][1],2.3)) for r in inv if r['kind'] in ('computeRack','networkRack')]
max_gap=max(power.find_nearest(p)[3] for p in rack_points)
check('Power drops reach all 736 rack tops (maximum surface gap)',max_gap,0,.001)
for color,y in [('warm',-61),('blue',-62)]:
    tree=surface_tree('groundHeaders_'+color)
    off=.13 if color=='warm' else -.13
    max_gap=max(tree.find_nearest(Vector((-80+i*5+off,y,-1)))[3] for i in range(32))
    check(color+' field columns reach common header (maximum surface distance)',max_gap,0,.11)
for key in ['compute','network']:b=bounds(key);check(key+' rack top',b['max'][2],2.3,.01)
# Revision03 checks use the geometry reopened from the saved file. Component
# records state the requested inventory; disconnected primitive bounds establish
# that the boxes, cylinders and valves are actually present in that file.
for kind,n in {'dewpointSensor':8,'freshAirUnit':1,'dockAirlock':3,'airlockInnerDoor':3,'airlockOuterDoor':3,'drainTank':2,'expansionTank':4,'bypassValve':1,'coolerIsolationValve':204,'coolerDrainValve':102,'coolerFreezeSensor':102}.items():
    check(kind+' inventory',counts[kind],n,0)
component_cache={}
def components(name):
    if name in component_cache:return component_cache[name]
    vertices,mesh=world_mesh(bpy.data.objects[name]);parent=list(range(len(vertices)))
    def find(a):
        while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
        return a
    for edge in mesh.edges:
        a,b=edge.vertices;parent[find(a)]=find(b)
    buckets=defaultdict(list)
    for i,v in enumerate(vertices):buckets[find(i)].append(v)
    result=[]
    for points in buckets.values():
        lo=Vector(tuple(min(p[i] for p in points) for i in range(3)))
        hi=Vector(tuple(max(p[i] for p in points) for i in range(3)))
        result.append({'center':(lo+hi)/2,'dimensions':hi-lo,'min':lo,'max':hi})
    component_cache[name]=result;return result
def primitive_count(label,mesh,dimensions,expected,tol=.001):
    selected=[c for c in components(mesh) if max(abs(c['dimensions'][i]-dimensions[i]) for i in range(3))<=tol]
    check(label+' actual mesh components',len(selected),expected,0)
    return selected
dew=primitive_count('Dew-point sensor boxes','dewpoint_white',(.15,.15,.15),8)
check('Dew-point sensors center height',max(abs(c['center'][2]-1.8) for c in dew),0,.001)
primitive_count('Inner and outer dock doors','airlock_charcoal',(.15,4,4.5),6)
primitive_count('Horizontal drain tanks','drainTanks_white',(12,3,3),2)
primitive_count('Upright expansion tanks','drainTanks_white',(1,1,2.2),4)
isolation_components=primitive_count('Cooler isolation valve bodies','freezeProtection_steel',(.3,.2,.3),204)
sensor_components=primitive_count('Cooler freeze sensors','freezeProtection_white',(.18,.15,.18),102)
drain_components=primitive_count('Cooler drain actuators','freezeProtection_freezeActuator',(.18,.18,.18),102)
primitive_count('Motorized bypass actuator','bypass_bypassYellow',(.65,.5,.48),1)
fresh=bounds('freshAirCase')
for axis,expected in enumerate((6,2.5,2.5)):check('Fresh-air casing '+('width','depth','height')[axis],fresh['max'][axis]-fresh['min'][axis],expected,.06)

# Routing records are embedded in the saved scene (not read from the live build
# script), then independently checked against the evaluated mesh surfaces.
routes=json.loads(bpy.context.scene.get('connection_routes','[]'))
check('Saved routing evidence present',int(bool(routes)),1,0)
route_by_name={r['name']:r for r in routes};trees={};surface_evidence=[]
per_cooler_gaps={'isolation':[],'freeze_sensor':[],'drain_actuator':[]}
for idx in range(102):
    for suffix in ('Warm','Cool'):
        r=route_by_name['cooler_'+str(idx)+'_'+suffix]
        center=(Vector(r['points'][0])+Vector(r['points'][1]))/2
        per_cooler_gaps['isolation'].append(min((center-c['center']).length for c in isolation_components))
    cool=route_by_name['cooler_'+str(idx)+'_Cool'];center=Vector(cool['points'][1])+Vector((0,0,.12))
    per_cooler_gaps['freeze_sensor'].append(min((center-c['center']).length for c in sensor_components))
    drain=route_by_name['cooler_'+str(idx)+'_drain'];center=Vector(drain['points'][1])+Vector((.17,0,-.02))
    per_cooler_gaps['drain_actuator'].append(min((center-c['center']).length for c in drain_components))
for label,gaps in per_cooler_gaps.items():check('Each cooler has its own '+label+' attached to its route',max(gaps),0,.001)
for route_record in routes:
    mesh=route_record['group']+'_'+route_record['material']
    if mesh not in trees:trees[mesh]=surface_tree(mesh)
    tree=trees[mesh];points=[Vector(p) for p in route_record['points']];gaps=[]
    for p in points:gaps.append(tree.find_nearest(p)[3])
    for a,b in zip(points,points[1:]):
        w=(b-a).normalized();u=w.cross(Vector((0,0,1)))
        if u.length<.1:u=w.cross(Vector((0,1,0)))
        u.normalize()
        # A point on a real generated cylinder vertex direction, halfway along
        # the segment, proves the pipe span as well as its capped endpoints.
        gaps.append(tree.find_nearest((a+b)/2+u*route_record['radius'])[3])
    surface_evidence.append({'route':route_record['name'],'mesh':mesh,'samples':len(gaps),'maximum_surface_gap_m':max(gaps)})
check('All tracked routes exist as saved mesh spans',max([r['maximum_surface_gap_m'] for r in surface_evidence],default=1),0,.0002)

def segment_distance(a,b,c,d):
    """Closest distance between finite segments, including parallel segments."""
    u=b-a;v=d-c;w=a-c;aa=u.dot(u);bb=u.dot(v);cc=v.dot(v);dd=u.dot(w);ee=v.dot(w);den=aa*cc-bb*bb
    if aa<1e-12:return (a-(c+v*max(0,min(1,ee/cc)))).length
    if cc<1e-12:return (c-(a+u*max(0,min(1,-dd/aa)))).length
    sn,sd,tn,td=den,den,den,den
    if den<1e-12:sn=0;sd=1;tn=ee;td=cc
    else:
        sn=bb*ee-cc*dd;tn=aa*ee-bb*dd
        if sn<0:sn=0;tn=ee;td=cc
        elif sn>sd:sn=sd;tn=ee+bb;td=cc
    if tn<0:
        tn=0
        if -dd<0:sn=0
        elif -dd>aa:sn=sd
        else:sn=-dd;sd=aa
    elif tn>td:
        tn=td
        if -dd+bb<0:sn=0
        elif -dd+bb>aa:sn=sd
        else:sn=-dd+bb;sd=aa
    s=0 if abs(sn)<1e-12 else sn/sd;t=0 if abs(tn)<1e-12 else tn/td
    return (w+s*u-t*v).length
def segments(r):
    p=[Vector(x) for x in r['points']];return list(zip(p,p[1:]))
route_segments={r['name']:segments(r) for r in routes}
def route_distance(a,b):
    return min(segment_distance(p,q,x,y) for p,q in route_segments[a['name']] for x,y in route_segments[b['name']])
def connected_graph(selected):
    graph={r['name']:set() for r in selected}
    for i,a in enumerate(selected):
        for b in selected[i+1:]:
            if route_distance(a,b)<.001:
                graph[a['name']].add(b['name']);graph[b['name']].add(a['name'])
    return graph
def path_to(graph,start,targets):
    queue=deque([[start]]);visited={start}
    while queue:
        path=queue.popleft()
        if path[-1] in targets:return path
        for n in sorted(graph.get(path[-1],[])):
            if n not in visited:visited.add(n);queue.append(path+[n])
    return []
drains=[r for r in routes if r['name'].startswith(('drain_row_','drain_to_tanks_','tank_inlet_')) or r['name']=='indoor_drain_manifold' or (r['name'].startswith('cooler_') and r['name'].endswith('_drain'))]
drain_graph=connected_graph(drains);tank_targets={r['name'] for r in drains if r['name'].startswith('tank_inlet_')};drain_paths=[]
for idx in range(102):
    path=path_to(drain_graph,'cooler_'+str(idx)+'_drain',tank_targets)
    drain_paths.append({'cooler':idx,'path':path,'bridges':[n for n in path if n.startswith('drain_to_tanks_')]})
check('Coolers with connected drain path through one bridge into an indoor tank',sum(bool(p['path']) and len(p['bridges'])==1 for p in drain_paths),102,0)
check('Drain paths use all three bridges',len({b for p in drain_paths for b in p['bridges']}),3,0)
for name in sorted(tank_targets):
    endpoint=Vector(route_by_name[name]['points'][-1]);tank_gap=surface_tree('drainTanks_white').find_nearest(endpoint)[3]
    check(name+' terminates on actual tank shell',tank_gap,0,.0002)

def circuit(r):
    for c in ('chipWarm','chipCool','roomWarm','roomCool'):
        if r['name'].startswith(c+'_'):return c
    parts=r['name'].split('_')
    if len(parts)==3 and parts[0]=='cooler' and parts[2] in ('Warm','Cool'):return ('chip' if int(parts[1])<73 else 'room')+parts[2]
    if r['name']=='ground_house_warm':return 'roomWarm'
    if r['name']=='ground_house_blue':return 'roomCool'
    return None
operating=[r for r in routes if circuit(r)]
clearance_pairs=[]
for i,a in enumerate(operating):
    for b in operating[i+1:]:
        if circuit(a)==circuit(b):continue
        clearance=route_distance(a,b)-a['radius']-b['radius']
        clearance_pairs.append({'a':a['name'],'b':b['name'],'clearance_m':clearance})
collisions=[p for p in clearance_pairs if p['clearance_m']<-.001]
check('Unintended operating-circuit pipe intersections',len(collisions),0,0)
drain_clearances=[]
for a in drains:
    for b in operating:
        clearance=route_distance(a,b)-a['radius']-b['radius']
        drain_clearances.append({'a':a['name'],'b':b['name'],'clearance_m':clearance})
drain_collisions=[p for p in drain_clearances if p['clearance_m']<-.001]
check('Drain pipes remain separate from operating coolant pipes',len(drain_collisions),0,0)
operating_paths=[]
for c in ('chipWarm','chipCool','roomWarm','roomCool'):
    subset=[r for r in operating if circuit(r)==c];graph=connected_graph(subset)
    for route_record in subset:
        if route_record['name'].startswith('cooler_'):
            path=path_to(graph,route_record['name'],{c+'_spine'})
            operating_paths.append({'port':route_record['name'],'circuit':c,'path':path})
check('Cooler ports connected to their own hall circuit',sum(bool(p['path']) for p in operating_paths),204,0)
bypass=route_by_name.get('chip_bypass')
if bypass:
    for p,c in zip((bypass['points'][0],bypass['points'][-1]),('chipWarm','chipCool')):
        selected=[r for r in operating if circuit(r)==c]
        gap=min(segment_distance(Vector(p),Vector(p),a,b) for r in selected for a,b in route_segments[r['name']])
        check('Intentional bypass connection to '+c,gap,0,.001)
else:check('Intentional bypass route present',0,1,0)

model_path=ROOT/'blender/SEED-Cambridge.blend';model_hash=hashlib.sha256(model_path.read_bytes()).hexdigest()
report={'model':str(model_path),'revision':bpy.context.scene.get('revision'),'sha256':model_hash,'blender':bpy.app.version_string,'status':'approved design modeled; not site surveyed','checks':checks,'counts':dict(counts),'bounds':{k:bounds(k) for k in ['sealed','hallRoof','boreholes','house','greenhouse','chillers','drainTanks','freshAirCase']},'notes':['Bounds read from evaluated saved mesh vertices in world coordinates.','New equipment counts independently checked against disconnected mesh component bounds.','Saved-scene routing records checked against mesh cap and side surfaces before connectivity and clearance analysis.','Cross-circuit clearance is a conservative centerline-distance minus pipe-radii test. The intentional chip mixing bypass is excluded from accidental-crossing counts and checked separately.','Drain connectivity does not establish hydraulic capacity, fall, air admission, complete drainability or engineered operation.','Visualization is not a construction or engineering approval.']}
(ROOT/'qa/model-connectivity.json').write_text(json.dumps({'revision':report['revision'],'sha256':model_hash,'route_count':len(routes),'surface_evidence':surface_evidence,'drain_paths':drain_paths,'operating_paths':operating_paths,'unintended_intersections':collisions,'drain_operating_intersections':drain_collisions,'minimum_cross_circuit_clearance_m':min((p['clearance_m'] for p in clearance_pairs),default=None),'minimum_drain_operating_clearance_m':min((p['clearance_m'] for p in drain_clearances),default=None),'closest_pairs':sorted(clearance_pairs,key=lambda p:p['clearance_m'])[:12]},indent=2))
(ROOT/'qa/model-measurements.json').write_text(json.dumps(report,indent=2));print(json.dumps(checks,indent=2))
assert all(c['pass'] for c in checks),'Model measurement failed'
