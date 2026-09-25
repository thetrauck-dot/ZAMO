"""Genera el logo SPATIAL SURGERY en 3D (cada letra separada, con bisel).

Uso:  python3 build_logo_3d.py   (requiere `pip install bpy pymupdf`)
Unidades: 1 pt del .ai original = 1 mm.
"""
import os
import sys

import bpy
import pymupdf
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source", "SPATIAL_SURGERY_01.ai")
OUT = os.path.join(HERE, "output")

THICKNESS = 5.0   # grosor total (mm)
BEVEL = 0.4       # bisel en letras (mm)
BEVEL_ICON = 0.2  # bisel en el ícono (trazos más finos)
NAMES = ["Icono", "S", "P", "A", "T", "I", "A", "L",
         "S", "U", "R", "G", "E", "R", "Y"]
COLOR = (0.9756, 0.6154, 0.1650)  # naranja del logo (RGB del .ai)

os.makedirs(os.path.join(OUT, "stl"), exist_ok=True)

# --- PDF (.ai) -> SVG --------------------------------------------------------
svg_path = os.path.join(OUT, "logo.svg")
page = pymupdf.open(SRC)[0]
with open(svg_path, "w") as f:
    f.write(page.get_svg_image())

# --- Escena limpia e importación ---------------------------------------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 0.001
scene.unit_settings.length_unit = "MILLIMETERS"

bpy.ops.import_curve.svg(filepath=svg_path)
curves = [o for o in scene.objects if o.type == "CURVE"]
if len(curves) != len(NAMES):
    sys.exit(f"Se esperaban {len(NAMES)} trazados, hay {len(curves)}")

# Escala: el importador usa 1px = 1/90 in en metros; lo llevamos a 1pt = 1 unidad (mm).
def bbox(o):
    pts = [o.matrix_world @ p.co.xyz for s in o.data.splines
           for p in (s.bezier_points if s.type == "BEZIER" else s.points)]
    return (min(p.x for p in pts), max(p.x for p in pts),
            min(p.y for p in pts), max(p.y for p in pts))

curves.sort(key=lambda o: bbox(o)[0])
boxes = [bbox(o) for o in curves]
x0 = min(b[0] for b in boxes); x1 = max(b[1] for b in boxes)
y0 = min(b[2] for b in boxes); y1 = max(b[3] for b in boxes)
page_w = 494.9628 - 116.59  # ancho real del logo en pt
k = page_w / (x1 - x0)
center = Vector(((x0 + x1) / 2, (y0 + y1) / 2, 0))

mat = bpy.data.materials.new("Naranja_SpatialSurgery")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (*[c ** 2.2 for c in COLOR], 1)
bsdf.inputs["Roughness"].default_value = 0.35
bsdf.inputs["Metallic"].default_value = 0.0

root = bpy.data.objects.new("SPATIAL_SURGERY", None)
scene.collection.objects.link(root)

for i, (obj, name) in enumerate(zip(curves, NAMES)):
    obj.name = f"{i:02d}_{name}_curva"
    obj.data.name = obj.name
    # Hornear la transformación del importador en los puntos.
    mw = obj.matrix_world.copy()
    for s in obj.data.splines:
        for p in s.bezier_points:
            for attr in ("co", "handle_left", "handle_right"):
                setattr(p, attr, (mw @ getattr(p, attr) - center) * k)
        for p in s.points:
            p.co.xyz = (mw @ p.co.xyz - center) * k
    obj.matrix_world.identity()
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    scene.collection.objects.link(obj)

    bev = BEVEL_ICON if name == "Icono" else BEVEL
    cu = obj.data
    cu.dimensions = "2D"
    cu.fill_mode = "BOTH"
    cu.extrude = THICKNESS / 2 - bev
    cu.bevel_depth = bev
    cu.bevel_resolution = 3
    cu.offset = -bev          # el bisel queda dentro del contorno original
    cu.resolution_u = 24
    cu.materials.clear()
    cu.materials.append(mat)

    # Origen de cada pieza en su centro, con la base apoyada en Z=0.
    obj.location.z = THICKNESS / 2
    obj.parent = root

# Quitar colecciones vacías del importador
for c in list(bpy.data.collections):
    if not c.objects:
        bpy.data.collections.remove(c)

# --- Mallas (copia) para exportar ---------------------------------------------
deps = bpy.context.evaluated_depsgraph_get()
mesh_objs = []
mesh_col = bpy.data.collections.new("Mallas")
scene.collection.children.link(mesh_col)
mesh_root = bpy.data.objects.new("SPATIAL_SURGERY_mesh", None)
mesh_col.objects.link(mesh_root)
for obj in [o for o in scene.objects if o.type == "CURVE"]:
    me = bpy.data.meshes.new_from_object(obj.evaluated_get(deps))
    me.name = obj.name.replace("_curva", "")
    mo = bpy.data.objects.new(me.name, me)
    mo.matrix_world = obj.matrix_world
    mesh_col.objects.link(mo)
    mo.parent = mesh_root
    mo.matrix_parent_inverse.identity()
    # Limpieza: fusionar vértices duplicados y recalcular normales
    bpy.context.view_layer.objects.active = mo
    for o in scene.objects:
        o.select_set(False)
    mo.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0005)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    for p in me.polygons:
        p.use_smooth = False
    mesh_objs.append(mo)


def select(objs):
    for o in scene.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


# STL individual por letra (mm) + todo junto
for mo in mesh_objs:
    select([mo])
    bpy.ops.wm.stl_export(filepath=os.path.join(OUT, "stl", mo.name + ".stl"),
                          export_selected_objects=True, apply_modifiers=True)
select(mesh_objs)
bpy.ops.wm.stl_export(filepath=os.path.join(OUT, "SPATIAL_SURGERY_completo.stl"),
                      export_selected_objects=True)
bpy.ops.wm.obj_export(filepath=os.path.join(OUT, "SPATIAL_SURGERY.obj"),
                      export_selected_objects=True, export_materials=True)
select(mesh_objs + [mesh_root])
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "SPATIAL_SURGERY.fbx"),
                         use_selection=True, global_scale=1.0, apply_unit_scale=True)
# glTF en metros reales (378 mm de ancho)
mesh_root.scale = (0.001,) * 3
select(mesh_objs + [mesh_root])
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "SPATIAL_SURGERY.glb"),
                          use_selection=True, export_format="GLB")
mesh_root.scale = (1,) * 3
mesh_col.hide_viewport = True
mesh_col.hide_render = True

# --- Cámara, luces y render de vista previa ----------------------------------
cam_data = bpy.data.cameras.new("Camara")
cam_data.lens = 85
cam_data.clip_start = 1
cam_data.clip_end = 10000
cam = bpy.data.objects.new("Camara", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, -870, 540)
direction = Vector((0, -10, 0)) - cam.location
cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
scene.camera = cam

for name, loc, energy, size in [("Key", (-300, -400, 500), 1.6e6, 250),
                                ("Fill", (400, -300, 200), 3e5, 300),
                                ("Rim", (0, 400, 250), 8e5, 250)]:
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.size = size
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    lo.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(lo)

world = bpy.data.worlds.new("Mundo")
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.02, 0.025, 1)
scene.world = world

ground_me = bpy.data.meshes.new("Suelo")
ground_me.from_pydata([(-2000, -2000, 0), (2000, -2000, 0), (2000, 2000, 0), (-2000, 2000, 0)], [], [(0, 1, 2, 3)])
ground = bpy.data.objects.new("Suelo", ground_me)
gmat = bpy.data.materials.new("Suelo")
gmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.03, 0.03, 0.035, 1)
gmat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6
ground_me.materials.append(gmat)
scene.collection.objects.link(ground)

scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = int(os.environ.get("SAMPLES", 96))
scene.cycles.use_denoising = True
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.filepath = os.path.join(OUT, "preview.png")
scene.view_settings.view_transform = "Standard"
bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "SPATIAL_SURGERY_3D.blend"))
print("OK")
