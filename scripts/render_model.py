"""Run with Blender --background --python scripts/render_model.py -- model.glb output.png."""
import math
import sys
import argparse
from pathlib import Path
import bpy
from mathutils import Vector

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
parser.add_argument('target', type=Path)
parser.add_argument('--view', choices=['front-left', 'front', 'back'], default='front-left')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, target = args.source, args.target
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
if source.suffix.lower() == '.stl':
    bpy.ops.import_mesh.stl(filepath=str(source.resolve()))
else:
    bpy.ops.import_scene.gltf(filepath=str(source.resolve()))
objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
if not objects:
    raise RuntimeError('No mesh objects imported')
points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
minimum = Vector([min(p[i] for p in points) for i in range(3)])
maximum = Vector([max(p[i] for p in points) for i in range(3)])
center = (minimum + maximum) / 2
size = max(maximum - minimum)
material = bpy.data.materials.new('Neutral clay')
material.diffuse_color = (0.65, 0.72, 0.78, 1)
for obj in objects:
    obj.data.materials.clear()
    obj.data.materials.append(material)
direction = {'front-left': [0.75, -1.65, 0.65], 'front': [0, -2, 0.25], 'back': [0, 2, 0.4]}[args.view]
bpy.ops.object.camera_add(location=center + Vector(direction) * size)
camera = bpy.context.object
camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.type = 'ORTHO'
camera.data.ortho_scale = size * 1.4
scene = bpy.context.scene
scene.camera = camera
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.background_type = 'WORLD'
scene.world.color = (0.045, 0.055, 0.07)
scene.render.resolution_x = 1000
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(target.resolve())
bpy.ops.wm.save_as_mainfile(filepath=str(target.with_suffix('.blend').resolve()))
bpy.ops.render.render(write_still=True)
