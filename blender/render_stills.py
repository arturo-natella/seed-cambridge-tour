"""Render views of the saved Blender master. All image pixels originate in Blender."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parent.parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
shot=args[0] if args else 'S1'
scene=bpy.context.scene
scene.render.resolution_x=3840;scene.render.resolution_y=2160;scene.render.resolution_percentage=100
scene.cycles.samples=64;scene.cycles.use_denoising=True
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='METAL'
 if any(d.type=='METAL' for d in prefs.devices):scene.cycles.device='GPU'
except Exception:pass

def show(key,on):
 ob=bpy.data.objects.get(key)
 if ob:
  for o in [ob,*ob.children_recursive]:o.hide_render=not on;o.hide_set(not on)
def setcamera(name):scene.camera=bpy.data.objects[name]
def color(name,c):
 m=bpy.data.materials.get(name);rgb=tuple(int(c[i:i+2],16)/255 for i in (0,2,4));rgb=tuple(v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in rgb)
 if m:m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*rgb,1)
def emission(name,c):
 m=bpy.data.materials.new(name);m.use_nodes=True;nodes=m.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');e=nodes.new('ShaderNodeEmission');e.inputs[0].default_value=(*c,1);m.node_tree.links.new(e.outputs[0],out.inputs[0]);return m
ink=emission('Overlay ink',(.035,.065,.042));muted=emission('Overlay muted',(.16,.2,.14));paper=emission('Overlay paper',(.84,.86,.79));white=emission('Overlay white',(.96,.97,.91))
# Flat typography in front of the camera, at normalized page positions.
def plane_coords(x,y):
 bpy.context.view_layer.update()
 cam=scene.camera;fr=cam.data.view_frame(scene=scene);z=fr[0].z
 left=min(v.x for v in fr);right=max(v.x for v in fr);top=max(v.y for v in fr);bottom=min(v.y for v in fr)
 if cam.data.type=='ORTHO':depth=-1;scale=1
 else:depth=-1;scale=1/abs(z)
 return Vector(((left+(right-left)*x)*scale,(bottom+(top-bottom)*y)*scale,depth)),(right-left)*scale,(top-bottom)*scale

def title(body,x,y,size=.018,material=None):
 cu=bpy.data.curves.new('Caption','FONT');cu.body=body;cu.align_y='TOP';cu.size=1;cu.space_line=1.2
 ob=bpy.data.objects.new('Caption '+body[:20],cu);scene.collection.objects.link(ob);pos,w,h=plane_coords(x,y);ob.matrix_world=scene.camera.matrix_world.copy();ob.location=scene.camera.matrix_world@pos;ob.scale=(h*size,)*3;cu.materials.append(material or ink)
 # Overlay is emissive and sits before all modeled geometry.
 return ob

def panel(x,y,w,h,material):
 p,fw,fh=plane_coords(x,y);p.z=-1.02 if scene.camera.data.type!='ORTHO' else -1.02
 verts=[(0,0,0),(w*fw,0,0),(w*fw,h*fh,0),(0,h*fh,0)];me=bpy.data.meshes.new('Caption plate');me.from_pydata(verts,[],[(0,1,2,3)]);ob=bpy.data.objects.new('Caption plate',me);scene.collection.objects.link(ob);ob.matrix_world=scene.camera.matrix_world.copy();ob.location=scene.camera.matrix_world@p;me.materials.append(material)

def common(label,sub):
 panel(.025,.884,.49,.092,white);title('SEED  /  '+label,.04,.962,.027);title(sub,.04,.917,.014,muted)
 title('PROPOSED CAMBRIDGE CAMPUS  /  DESIGN MODEL',.035,.037,.012,muted)

def image_panel(path,x,y,w,h):
 im=bpy.data.images.load(str(path));mat=bpy.data.materials.new('Hall detail image');mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');em=nt.nodes.new('ShaderNodeEmission');tex=nt.nodes.new('ShaderNodeTexImage');tex.image=im;nt.links.new(tex.outputs['Color'],em.inputs[0]);nt.links.new(em.outputs[0],out.inputs[0]);
 p,fw,fh=plane_coords(x,y);me=bpy.data.meshes.new('Inset image');me.from_pydata([(0,0,0),(w*fw,0,0),(w*fw,h*fh,0),(0,h*fh,0)],[],[(0,1,2,3)]);uv=me.uv_layers.new()
 for loop,co in zip(uv.data,[(0,0),(1,0),(1,1),(0,1)]):loop.uv=co
 ob=bpy.data.objects.new('Hall detail inset',me);scene.collection.objects.link(ob);ob.matrix_world=scene.camera.matrix_world.copy();ob.location=scene.camera.matrix_world@p;me.materials.append(mat)

if shot=='S1':
 setcamera('S1-Hero');common('CAMBRIDGE FLAGSHIP','Autumn light • one of six campuses')
elif shot=='S2':
 setcamera('S2-Winter');scene.camera.location.z=60;scene.camera.rotation_euler=(Vector((0,30,10))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.lens=32
 for name in ['grass','meadow','leaf','leafLight','leafGold','leafRust','roof','gravel']:color(name,'E9EEE9')
 color('panel','82918F');scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.68,.77,.85,1)
 common('WINTER OPERATION','Raised coolers stay above the snow')
elif shot in ['S3','S3-detail','Power-detail','Freeze-detail','Cooler-detail','Drain-detail','FreshAir-detail']:
 for name in ['hall','hallRoof','roofSolar','partitions','airlockRoof','freshAirCase','groundCap']:show(name,False)
 for name in ['boreholes','boreholeFocus','groundHeaders','geology','coldInsulation']:show(name,shot=='S3')
 if shot=='S3':show('batteryHouseRoof',False)
 show('boreholeSurface',False)
 if shot=='Freeze-detail':
  setcamera('Freeze-Detail');common('WINTER BYPASS AND DRAIN-DOWN','Yellow actuator = chip-loop bypass • white / purple pipes = drains')
  panel(.025,.075,.47,.17,white);title('BYPASS KEEPS THE HALL SUPPLY WARM',.04,.225,.020);title('Yellow actuator controls the chip-loop bypass.\nWhite drain pipes with purple bands lead indoors.\nPipe sizes, falls and control sequence remain illustrative.',.04,.185,.016,muted)
 elif shot=='Cooler-detail':
  setcamera('Freeze-Detail');scene.camera.location=Vector((0,39.7,14));scene.camera.rotation_euler=(Vector((0,39.2,7.5))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.lens=20
  common('ISOLATE AND MONITOR EACH COOLER','Rear connection detail • a pair of valves on all 102 modules')
  panel(.025,.075,.44,.15,white);title('ORANGE INLET / BLUE OUTLET',.04,.205,.020);title('Dark blue actuators close the two isolation valves.\nA small white sensor monitors the outlet temperature.\nThe separate lowest-point drain is on the opposite side.',.04,.167,.015,muted)
 elif shot=='Drain-detail':
  setcamera('Drain-Detail');scene.camera.location=Vector((-82,41,25));scene.camera.rotation_euler=(Vector((-82,23,2.2))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.lens=25
  common('DRAIN-DOWN STORAGE INDOORS','Two horizontal tanks • four expansion tanks • connected drains')
  panel(.025,.075,.48,.14,white);title('ILLUSTRATIVE TANK ENVELOPES',.04,.195,.021);title('Storage volume, drain slopes and complete drainability\nrequire hydraulic engineering before construction.',.04,.155,.016,muted)
 elif shot=='FreshAir-detail':
  setcamera('FreshAir-Detail');scene.camera.location=Vector((69,18.8,5.5));scene.camera.rotation_euler=(Vector((75,23.3,1.4))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.lens=30
  common('DRY FRESH AIR FOR THE HALLS','Intake duct → coil → drain pan • casing removed for explanation')
  panel(.025,.075,.49,.15,white);title('DEHUMIDIFICATION DUTY IS NOT YET SIZED',.04,.205,.019);title('The 75°F room-air loop cannot establish a 50°F dew point.\nCold-source selection and air-delivery design remain open.',.04,.165,.016,muted)
 elif shot=='Power-detail':
  setcamera('Power-Detail');common('POWER, FROM UPS TO RACKS','Gold = electrical power • red = fire sprinklers • orange / blue = floor coolant')
  panel(.025,.09,.40,.17,white);title('BATTERIES → UPS → DISTRIBUTION',.04,.235,.021);title('Overhead gold busways have a drop to every rack.\nLight gray cable trays are separate from power.\nIllustrative routing; final engineering remains open.',.04,.194,.016,muted)
 elif shot=='S3-detail':
  setcamera('S3-Detail');scene.camera.data.lens=22;scene.cycles.samples=48
  common('INSIDE THE HALL','Pipes below, power above')
 else:
  setcamera('S3-Cutaway');scene.camera.location=Vector((-320,-310,125));scene.camera.rotation_euler=(Vector((-10,-80,-60))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.lens=30
  # Remove the near terrain cheeks for this geological section only.
  show('terrain',False);show('context',False);show('landscape',False);show('skyline',False);show('parking',False);show('solar',False);show('solarField',False);show('roads',False);show('fence',False)
  # A genuine north-south mesh section at x=-37 through pod 2.
  import bmesh
  for ob in list(scene.objects):
   if ob.type!='MESH' or ob.hide_render:continue
   bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.0001,plane_co=(-37,0,0),plane_no=(1,0,0),clear_inner=True);bm.to_mesh(ob.data);bm.free()
  # Direction arrows over the two cooling circuits, rendered in Blender.
  for pos,direction,matname in [((0,33,7.5),(0,1,0),'warm'),((2,33,7.5),(0,-1,0),'blue'),((.13,-220,-30),(0,0,-1),'warm'),((-.13,-220,-60),(0,0,1),'blue'),((.13,-220,-90),(0,0,-1),'warm'),((-.13,-220,-120),(0,0,1),'blue')]:
   bpy.ops.mesh.primitive_cone_add(vertices=12,radius1=1.1,radius2=0,depth=4,location=pos)
   arrow=bpy.context.object;arrow.name='Flow direction '+matname;arrow.rotation_euler=Vector(direction).to_track_quat('Z','Y').to_euler();arrow.data.materials.append(bpy.data.materials[matname])
  common('COOLING, ABOVE AND BELOW','North–south section through pod 2 • x = −37 m')
  if (ROOT/'stills/S3-detail.png').exists():image_panel(ROOT/'stills/S3-detail.png',.625,.57,.35,.35)
  panel(.04,.12,.36,.17,white);title('COOLING STORED IN THE GROUND',.055,.27,.022);title('1,024 total loops, 5 m apart • one U-loop highlighted\nSoil 0–1 m / till 1–15 m / bedrock to 150 m',.055,.225,.017,muted)
  title('Warm fluid',.055,.155,.015,emission('Warm ink',(.68,.12,.03)));title('Cool fluid',.17,.155,.015,emission('Cool ink',(.03,.22,.6)))
elif shot=='S4':
 setcamera('S4-Plan');scene.camera.data.ortho_scale=1080;scene.camera.location.x=95
 # A downward camera with north up (local Y aligns with world north).
 scene.camera.rotation_euler=(0,0,0);scene.camera.rotation_euler=(Vector((95,-65,0))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
 common('CAMPUS PLAN','North up • model units in meters')
 panel(.725,.09,.25,.74,white);title('THE CAMPUS',.745,.80,.021)
 names=['Main hall','Cooling ridge','Backup chillers','Cold Battery House','Borehole meadow / solar','Substation','Backup power / fuel','SEED House','Waste-heat greenhouse','Solar parking']
 for i,name in enumerate(names):title(str(i+1).zfill(2)+'  '+name,.745,.748-i*.056,.016,muted)
 title('N ↑',.66,.92,.023)
 positions=[(0,0,10),(0,48,10),(123,48,4),(0,-47,6),(-10,-170,3),(175,0,10),(210,120,5),(-160,2,9),(-155,-35,8),(-270,0,5)]
 bpy.context.view_layer.update()
 for i,p in enumerate(positions):
  co=world_to_camera_view(scene,scene.camera,Vector(p));panel(co.x-.01,co.y-.013,.024,.036,white);title(str(i+1).zfill(2),co.x-.007,co.y+.016,.018)
else:
 setcamera(shot);scene.render.resolution_x=960;scene.render.resolution_y=540;scene.cycles.samples=16
scene.render.filepath=str(ROOT/('qa' if shot.startswith('QA') else 'stills')/(shot+'.png'))
bpy.context.view_layer.update()
bpy.ops.render.render(write_still=True)
print('SEED_RENDER_DONE',shot,flush=True)
