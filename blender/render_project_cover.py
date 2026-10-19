"""Sundai cover from the saved Blender geometry; never overwrites the master."""
import bpy, math, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent.parent
scene=bpy.context.scene

def show(key,on):
 ob=bpy.data.objects.get(key)
 if ob:
  for obj in [ob,*ob.children_recursive]:obj.hide_render=not on;obj.hide_set(not on)

# A freestanding campus model: remove only off-site scenery and reveal the
# authored underground field. The physical equipment stays in its saved place.
for key in ['context','skyline','groundCap','boreholeSurface']:show(key,False)
for key in ['boreholes','boreholeFocus','groundHeaders','geology']:show(key,True)
cam=bpy.data.objects['S1-Hero'];scene.camera=cam
cam.data.type='ORTHO';cam.data.ortho_scale=1050
cam.location=(-640,-720,500)
cam.rotation_euler=(Vector((-20,-65,-30))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='METAL'
 if any(d.type=='METAL' for d in prefs.devices):scene.cycles.device='GPU'
except Exception:pass
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.8,.83,.79,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.8
light=bpy.data.lights.get('Southwest afternoon')
if light:light.energy=4;light.color=(1,.95,.86);light.angle=math.radians(10)
scene.view_settings.exposure=.6
scene.render.film_transparent=True
scene.render.resolution_x=2400;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.render.filepath=str(ROOT/'stills/Sundai-campus.png')
bpy.ops.render.render(write_still=True)
print('SUNDAI_CAMPUS_RENDER_DONE',flush=True)
